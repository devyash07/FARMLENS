"""
Disease Information API Routes
Provides disease knowledge base and treatment information
"""

from fastapi import APIRouter, HTTPException
import json
import os
from typing import Optional
import urllib.request
import urllib.parse

router = APIRouter()

# Load disease info globally
_DISEASE_INFO = None

# --- Zero Dependency Translator ---
def translate_content(text, target_lang):
    if not text or target_lang == "en":
        return text
    try:
        # Recursively handle lists (like symptoms and prevention arrays)
        if isinstance(text, list):
            return [translate_content(item, target_lang) for item in text]
            
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={urllib.parse.quote(str(text))}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return "".join([sentence[0] for sentence in data[0] if sentence[0]])
    except Exception as e:
        print(f"[Translator] Failed to translate: {e}")
        return text
# ----------------------------------

def _load_disease_info():
    """Load the disease information knowledge base"""
    global _DISEASE_INFO
    if _DISEASE_INFO is not None:
        return _DISEASE_INFO
    try:
        disease_info_path = "disease_info.json"
        if os.path.exists(disease_info_path):
            with open(disease_info_path, 'r') as f:
                _DISEASE_INFO = json.load(f)
            print(f"[Disease API] Loaded {len(_DISEASE_INFO)} disease entries")
        else:
            print(f"[Disease API] disease_info.json not found")
            _DISEASE_INFO = {}
        return _DISEASE_INFO
    except Exception as e:
        print(f"[Disease API] Failed to load disease info: {e}")
        return {}


@router.get("/disease/{disease_key}")
def get_disease_info(disease_key: str, language: str = "en"):
    """
    Get detailed information for a specific disease
    """
    disease_db = _load_disease_info()
    if not disease_db:
        raise HTTPException(status_code=503, detail="Disease database not loaded")
        
    def prepare_response(key, data_obj):
        # Deep copy to avoid translating the master database in-memory
        data = data_obj.copy() 
        if language != "en":
            print(f"[Disease API] Translating database entry to {language}...")
            data["symptoms"] = translate_content(data.get("symptoms", []), language)
            data["prevention"] = translate_content(data.get("prevention", []), language)
            data["treatment"] = translate_content(data.get("treatment", []), language)
        return data

    # Try exact match first
    if disease_key in disease_db:
        return {
            "key": disease_key,
            "found": True,
            "data": prepare_response(disease_key, disease_db[disease_key])
        }
        
    # Try case-insensitive match
    for key in disease_db.keys():
        if key.lower() == disease_key.lower():
            return {
                "key": key,
                "found": True,
                "data": prepare_response(key, disease_db[key])
            }
            
    # Try partial match (for variations)
    matching_keys = [k for k in disease_db.keys() if disease_key.lower() in k.lower()]
    if matching_keys:
        return {
            "key": disease_key,
            "found": True,
            "matches": matching_keys[:5], 
            "data": prepare_response(matching_keys[0], disease_db[matching_keys[0]]) 
        }
        
    raise HTTPException(status_code=404, detail=f"Disease '{disease_key}' not found in database")


@router.get("/disease")
def list_all_diseases():
    disease_db = _load_disease_info()
    if not disease_db:
        raise HTTPException(status_code=503, detail="Disease database not loaded")
    return {
        "total": len(disease_db),
        "diseases": [
            {
                "key": key,
                "name": info.get("disease", key),
                "crop": info.get("crop", "Unknown"),
            }
            for key, info in disease_db.items()
        ]
    }


@router.get("/crops")
def get_crops():
    disease_db = _load_disease_info()
    if not disease_db:
        raise HTTPException(status_code=503, detail="Disease database not loaded")
    crops = {}
    for key, info in disease_db.items():
        crop = info.get("crop", "Unknown")
        if crop not in crops:
            crops[crop] = {
                "crop": crop,
                "disease_count": 0,
                "diseases": []
            }
        crops[crop]["disease_count"] += 1
        crops[crop]["diseases"].append({
            "key": key,
            "name": info.get("disease", key)
        })
    return {
        "total_crops": len(crops),
        "crops": list(crops.values())
    }


@router.get("/disease-by-crop/{crop_name}")
def get_diseases_by_crop(crop_name: str):
    disease_db = _load_disease_info()
    if not disease_db:
        raise HTTPException(status_code=503, detail="Disease database not loaded")
    matching_diseases = []
    for key, info in disease_db.items():
        if info.get("crop", "").lower() == crop_name.lower():
            matching_diseases.append({
                "key": key,
                "name": info.get("disease", key),
                "symptoms": info.get("symptoms", []),
                "severity_indicator": "Healthy" in info.get("disease", "")
            })
    if not matching_diseases:
        raise HTTPException(status_code=404, detail=f"No diseases found for crop '{crop_name}'")
    return {
        "crop": crop_name,
        "disease_count": len(matching_diseases),
        "diseases": matching_diseases
    }


@router.post("/disease/search")
def search_diseases(query: str = None, crop: Optional[str] = None, limit: int = 10):
    disease_db = _load_disease_info()
    if not disease_db:
        raise HTTPException(status_code=503, detail="Disease database not loaded")
    results = []
    query_lower = query.lower() if query else ""
    crop_lower = crop.lower() if crop else ""
    for key, info in disease_db.items():
        if crop_lower and crop_lower not in info.get("crop", "").lower():
            continue
        if query_lower:
            disease_name = info.get("disease", "").lower()
            key_lower = key.lower()
            if query_lower not in disease_name and query_lower not in key_lower:
                symptoms_text = " ".join(info.get("symptoms", [])).lower()
                if query_lower not in symptoms_text:
                    continue
        results.append({
            "key": key,
            "name": info.get("disease", key),
            "crop": info.get("crop", "Unknown"),
            "symptoms": info.get("symptoms", []),
        })
        if len(results) >= limit:
            break
    return {
        "query": query or "all",
        "crop_filter": crop or "all",
        "total_results": len(results),
        "results": results
    }