import os
import hashlib
import base64
import json
from typing import Optional
import urllib.request
import urllib.parse


# --- Zero Dependency Translator ---
def translate_content(text, target_lang):
    if not text or target_lang == "en":
        return text
    try:
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


# ---------------------------------------------------------------------------
# Local ML Models (runs without API calls)
# ---------------------------------------------------------------------------
_ML_MODEL = None
_CLASS_NAMES = None
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
            print(f"[AI] Disease knowledge base loaded with {len(_DISEASE_INFO)} entries")
        else:
            print(f"[AI] disease_info.json not found, using fallback treatment")
            _DISEASE_INFO = {}
        return _DISEASE_INFO
    except Exception as e:
        print(f"[AI] Failed to load disease info: {e}")
        return {}

def _load_efficientnet_model():
    """Load the fine-tuned EfficientNet Keras model for plant disease detection"""
    global _ML_MODEL, _CLASS_NAMES
    if _ML_MODEL is not None:
        return _ML_MODEL, _CLASS_NAMES
    
    try:
        import tensorflow as tf
        
        model_path = "best_farmlens_finetuned.keras"
        class_path = "class_names.json"
        
        if not os.path.exists(model_path):
            print(f"[AI] Fine-tuned model not found at {model_path}")
            return None, None
        
        # Load class names (66 Classes)
        with open(class_path, 'r') as f:
            _CLASS_NAMES = json.load(f)
        
        # Load the trained Keras model
        model = tf.keras.models.load_model(model_path)
        
        _ML_MODEL = model
        print(f"[AI] EfficientNet model loaded successfully with {len(_CLASS_NAMES)} classes")
        return _ML_MODEL, _CLASS_NAMES
    except Exception as e:
        print(f"[AI] Failed to load EfficientNet model: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def _run_ml_predict(image_bytes: bytes) -> dict:
    """Use custom EfficientNet model for prediction"""
    try:
        from PIL import Image
        import io
        import numpy as np
        
        model, class_names = _load_efficientnet_model()
        disease_info = _load_disease_info()
        
        if model is None or class_names is None:
            raise ValueError("Model not available")
        
        print(f"[AI Pipeline] === CLASS NAMES VERIFICATION ===")
        print(f"[AI Pipeline] Total classes: {len(class_names)}")
        
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        import tensorflow as tf
        img_resized = img.resize((224, 224))
        img_array = np.array(img_resized, dtype=np.float32)
        img_array = np.expand_dims(img_array, axis=0)
        
        from tensorflow.keras.applications.efficientnet import preprocess_input
        img_array = preprocess_input(img_array)
        
        preds = model.predict(img_array, verbose=0)
        probs = preds[0]
        predicted_idx = int(np.argmax(probs))
        confidence = float(probs[predicted_idx])
        
        top5_indices = np.argsort(probs)[-5:][::-1]
        print(f"[AI Pipeline] === TOP 5 PREDICTIONS ===")
        for rank, idx in enumerate(top5_indices, 1):
            print(f"  #{rank} [{idx:2d}] {class_names[idx]:40s} = {probs[idx]*100:.2f}%")
        
        label = class_names[predicted_idx]
        print(f"[AI] Selected prediction: {label} ({confidence*100:.1f}%)")
        
        # Parse the custom labels
        if '___' in label:
            parts = label.split('___')
            crop = parts[0].replace('_', ' ').replace('(', '').replace(')', '').strip()
            disease_raw = parts[1].replace('_', ' ').strip() if len(parts) > 1 else "Unknown"
        elif '_' in label:
            found = False
            for crop_name in ['Cotton', 'Tomato', 'Potato', 'Rice', 'Wheat', 'Corn', 'Apple', 'Grape', 'Orange', 'Peach', 'Pepper', 'Raspberry', 'Blueberry', 'Strawberry', 'Squash', 'Soybean', 'Cherry']:
                if label.startswith(crop_name):
                    crop = crop_name
                    disease_raw = label[len(crop_name)+1:].replace('_', ' ')
                    found = True
                    break
            if not found:
                crop = "Unknown"
                disease_raw = label.replace('_', ' ')
        else:
            crop = "General"
            disease_raw = label.replace('_', ' ')
        
        is_healthy = 'healthy' in disease_raw.lower()
        disease = "Healthy" if is_healthy else disease_raw
        
        treatment = ""
        symptoms = []
        prevention = []
        
        # Fetch detailed info from the JSON knowledge base
        if label in disease_info:
            info = disease_info[label]
            crop = info.get('crop', crop)
            disease = info.get('disease', disease)
            symptoms = info.get('symptoms', [])
            prevention = info.get('prevention', [])
            treatment_list = info.get('treatment', [])
            
            treatment_parts = []
            if treatment_list:
                if len(treatment_list) == 1:
                    treatment_parts.append(f"Apply {treatment_list[0]} fungicide immediately.")
                else:
                    treatments_str = ", ".join(treatment_list[:-1]) + f", or {treatment_list[-1]}"
                    treatment_parts.append(f"Treatment: Apply {treatments_str} according to label instructions.")
            
            if prevention:
                if len(prevention) == 1:
                    treatment_parts.append(f"Prevention: {prevention[0]}.")
                elif len(prevention) == 2:
                    treatment_parts.append(f"Prevention: {prevention[0]} and {prevention[1].lower()}.")
                else:
                    prev_str = ", ".join(prevention[:2]) + f", and {prevention[2].lower()}"
                    treatment_parts.append(f"Prevention: {prev_str}.")
            
            if symptoms:
                if len(symptoms) <= 2:
                    symp_str = " and ".join(symptoms)
                else:
                    symp_str = ", ".join(symptoms[:2]) + f", and {symptoms[2]}"
                treatment_parts.append(f"Common symptoms include: {symp_str}.")
            
            treatment = " ".join(treatment_parts)
        
        if not treatment:
            treatment = "Apply appropriate fungicide or pesticide based on disease type. Consult local agricultural extension."
        
        if is_healthy:
            severity = 0
            confidence_pct = min(99, int(confidence * 100))
        else:
            confidence_pct = min(99, int(confidence * 100))
            if confidence < 0.7:
                severity = max(30, min(50, int(confidence * 70)))
            elif confidence < 0.85:
                severity = max(50, min(70, int(confidence * 80)))
            else:
                severity = max(70, min(95, int(confidence * 95)))
        
        explanation = f"Detected {disease} in {crop} with {confidence_pct}% confidence using Fine-tuned EfficientNet deep learning model."
        if symptoms:
            explanation += f" Symptoms: {', '.join(symptoms[:3])}."
        
        result = {
            "crop": crop,
            "disease": disease,
            "severity": severity,
            "confidence": confidence_pct,
            "status": "Healthy" if is_healthy else "Infected",
            "explanation": explanation,
            "treatment": treatment,
            "_gradcam_model": model,           # Passed for Heatmap generation
            "_gradcam_img_array": img_array,   # Passed for Heatmap generation
            "_gradcam_class_idx": predicted_idx # Passed for Heatmap generation
        }
        
        return result
    except Exception as e:
        print(f"[AI] Model prediction failed: {e}")
        import traceback
        traceback.print_exc()
        raise

# ---------------------------------------------------------------------------
# Public entry point with enhanced structured output
# ---------------------------------------------------------------------------
def predict(image_bytes: Optional[bytes] = None, language: str = "en") -> dict:
    if not image_bytes:
        return {
            "crop": "Unknown",
            "disease": "Unknown",
            "severity": 0,
            "confidence": 0,
            "status": "Unknown",
            "image_url": "",
            "heatmap_url": "",
            "heatmap_b64": "",
            "explanation": "No image provided.",
            "treatment": "",
            "precautions": ""
        }

    print(f"[AI Pipeline] Starting prediction with language: {language}")

    result = None
    
    # 1. Force custom Keras ML model locally
    try:
        print("[AI Pipeline] ✓ Step 1: Using Fine-tuned EfficientNet model...")
        result = _run_ml_predict(image_bytes)
        print(f"[AI Pipeline] ✅ ML Model success: {result['crop']} / {result['disease']} ({result['confidence']}% confidence)")
    except Exception as e:
        print(f"[AI Pipeline] ❌ ML Model failed: {e}")
        import traceback
        traceback.print_exc()
        
    if not result:
        print("[AI Pipeline] ⚠️ All methods failed, using mock prediction")
        result = {
            "crop": "Unknown",
            "disease": "Unknown Error",
            "severity": 0,
            "confidence": 0,
            "status": "Unknown",
            "explanation": "Prediction failed.",
            "treatment": "Please try again."
        }

    # Extract precautions from disease info
    disease_info = _load_disease_info()
    precautions = []
    disease_key = "" 
    
    for key, info in disease_info.items():
        if (result['disease'].lower() in key.lower() or 
            result['disease'].lower() in info.get('disease', '').lower()):
            precautions = info.get('prevention', [])
            disease_key = key 
            break
    
    if not precautions:
        if result['status'] == "Healthy":
            precautions = ["Continue regular monitoring for early disease detection"]
        else:
            precautions = ["Isolate infected plants to prevent disease spread"]
    
    # Generate Grad-CAM++ heatmap for infected plants
    heatmap_b64 = ""
    if result["status"] == "Infected" and result["severity"] > 0:
        model = result.get("_gradcam_model")
        img_array = result.get("_gradcam_img_array")
        class_idx = result.get("_gradcam_class_idx", 0)
        
        if model is not None and img_array is not None:
            try:
                from services.gradcam_plus import generate_heatmap_b64 as generate_gradcam_heatmap
                
                heatmap_b64 = generate_gradcam_heatmap(
                    image_bytes, 
                    result["severity"],
                    result.get("crop", "Unknown"),
                    result.get("disease", "Unknown"),
                    result.get("confidence", 0),
                    model=model,
                    img_array=img_array,
                    class_idx=class_idx
                )
            except Exception as e:
                print(f"[AI Pipeline] ❌ Heatmap EXCEPTION: {e}")
                heatmap_b64 = ""
    
    # Clean up metadata before sending to frontend
    result.pop("_gradcam_model", None)
    result.pop("_gradcam_img_array", None)
    result.pop("_gradcam_class_idx", None)

    response = {
        "crop": result.get("crop", "Unknown"),
        "disease": result.get("disease", "Unknown"),
        "disease_key": disease_key,
        "severity": result.get("severity", 0),
        "confidence": result.get("confidence", 0),
        "status": result.get("status", "Unknown"),
        "image_url": "", 
        "heatmap_url": "", 
        "heatmap_b64": heatmap_b64,
        "explanation": result.get("explanation", "Analysis completed."),
        "treatment": result.get("treatment", ""),
        "precautions": precautions if isinstance(precautions, str) else " ".join(precautions)
    }

    print(f"[AI Pipeline] ✅ Prediction complete! Returning structured JSON response")
    return response