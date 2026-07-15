"""
Disease Information API Routes
Provides disease knowledge base and treatment information
"""

from fastapi import APIRouter, HTTPException
import json
import os
from typing import Optional

router = APIRouter()

# Load disease info globally
_DISEASE_INFO = None

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
def get_disease_info(disease_key: str):
    """
    Get detailed information for a specific disease
    
    Args:
        disease_key: The disease identifier (e.g., "Tomato_Early_Blight")
    
    Returns:
        Disease information including symptoms, prevention, and treatment
    """
    disease_db = _load_disease_info()
    
    if not disease_db:
        raise HTTPException(status_code=503, detail="Disease database not loaded")
    
    # Try exact match first
    if disease_key in disease_db:
        return {
            "key": disease_key,
            "found": True,
            "data": disease_db[disease_key]
        }
    
    # Try case-insensitive match
    for key in disease_db.keys():
        if key.lower() == disease_key.lower():
            return {
                "key": key,
                "found": True,
                "data": disease_db[key]
            }
    
    # Try partial match (for variations)
    matching_keys = [k for k in disease_db.keys() if disease_key.lower() in k.lower()]
    
    if matching_keys:
        return {
            "key": disease_key,
            "found": True,
            "matches": matching_keys[:5],  # Return top 5 matches
            "data": disease_db[matching_keys[0]]  # Return best match
        }
    
    raise HTTPException(status_code=404, detail=f"Disease '{disease_key}' not found in database")


@router.get("/disease")
def list_all_diseases():
    """
    Get a list of all diseases in the database
    
    Returns:
        List of disease keys and basic info
    """
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
    """
    Get list of all crops in the database
    
    Returns:
        List of unique crops with disease counts
    """
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
    """
    Get all diseases for a specific crop
    
    Args:
        crop_name: The crop name (e.g., "Tomato")
    
    Returns:
        List of diseases affecting the crop
    """
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
    """
    Search diseases by name or crop
    
    Args:
        query: Search term for disease name or symptoms
        crop: Filter by crop type
        limit: Max number of results
    
    Returns:
        List of matching diseases
    """
    disease_db = _load_disease_info()
    
    if not disease_db:
        raise HTTPException(status_code=503, detail="Disease database not loaded")
    
    results = []
    query_lower = query.lower() if query else ""
    crop_lower = crop.lower() if crop else ""
    
    for key, info in disease_db.items():
        # Check crop filter
        if crop_lower and crop_lower not in info.get("crop", "").lower():
            continue
        
        # Check query match in disease name
        if query_lower:
            disease_name = info.get("disease", "").lower()
            key_lower = key.lower()
            
            if query_lower not in disease_name and query_lower not in key_lower:
                # Check symptoms
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
