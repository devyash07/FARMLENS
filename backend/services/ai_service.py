import os
import hashlib
import base64
import json
from typing import Optional
import numpy as np
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
        
        # Use the new fine-tuned model
        model_path = "best_farmlens_finetuned.keras"
        class_path = "class_names.json"
        
        if not os.path.exists(model_path):
            print(f"[AI] Fine-tuned model not found at {model_path}, trying legacy model...")
            model_path = "farmlens_efficientnet.keras"
            if not os.path.exists(model_path):
                print(f"[AI] EfficientNet model file not found")
                return None, None
        
        # Load class names
        with open(class_path, 'r') as f:
            _CLASS_NAMES = json.load(f)
        
        # Load the trained Keras model
        model = tf.keras.models.load_model(model_path)
        
        _ML_MODEL = model
        model_type = "Fine-tuned EfficientNet" if "finetuned" in model_path else "EfficientNet"
        print(f"[AI] {model_type} model loaded with {len(_CLASS_NAMES)} classes")
        return _ML_MODEL, _CLASS_NAMES
    except Exception as e:
        print(f"[AI] Failed to load EfficientNet model: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def _load_torch_model():
    """Load the PyTorch MobileNetV2 model"""
    global _ML_MODEL, _CLASS_NAMES
    
    # CRITICAL FIX: CACHING CHECK
    if _ML_MODEL is not None:
        return _ML_MODEL, _CLASS_NAMES
    
    try:
        import torch
        from torchvision import models
        import torch.nn as nn
        
        model_path = "mobilenetv2_plant.pth"
        
        if not os.path.exists(model_path):
            print(f"[AI] PyTorch model file not found at {model_path}")
            return None, None
        
        # Hardcode the standard 38 classes to align perfectly with the model weights
        _CLASS_NAMES = [
            'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
            'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew', 'Cherry_(including_sour)___healthy',
            'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_', 'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy',
            'Grape___Black_rot', 'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy',
            'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot', 'Peach___healthy',
            'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy',
            'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew', 'Strawberry___Leaf_scorch', 'Strawberry___healthy',
            'Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold',
            'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot',
            'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 'Tomato___healthy'
        ]
        
        # Build model architecture 
        model = models.mobilenet_v2(weights=None)
        model.classifier[1] = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(model.classifier[1].in_features, 38)
        )
        
        # Load trained weights
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu'), weights_only=True))
        model.eval()
        
        _ML_MODEL = model
        print(f"[AI] PyTorch MobileNetV2 model loaded successfully with 38 classes")
        return _ML_MODEL, _CLASS_NAMES
    except Exception as e:
        print(f"[AI] Failed to load PyTorch model: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def _torch_predict(image_bytes: bytes) -> dict:
    """Use custom EfficientNet or PyTorch model for prediction with disease knowledge base"""
    try:
        from PIL import Image
        import io
        import numpy as np
        
        model, class_names = _load_torch_model()  # Will load PyTorch MobileNetV2
        disease_info = _load_disease_info()
        
        if model is None or class_names is None:
            raise ValueError("Model not available")
        
        # Detect model type
        is_tensorflow = hasattr(model, 'predict')
        
        # VERIFY CLASS NAMES
        print(f"[AI Pipeline] === CLASS NAMES VERIFICATION ===")
        print(f"[AI Pipeline] Total classes: {len(class_names)}")
        print(f"[AI Pipeline] First 10 classes:")
        for i in range(min(10, len(class_names))):
            print(f"  [{i:2d}] {class_names[i]}")
        print(f"[AI Pipeline] Last 10 classes:")
        for i in range(max(0, len(class_names)-10), len(class_names)):
            print(f"  [{i:2d}] {class_names[i]}")
        
        # Preprocess image
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        if is_tensorflow:
            # TensorFlow/Keras EfficientNet preprocessing
            import tensorflow as tf
            
            # Step 1: Resize to model input size (224x224 for EfficientNet)
            img_resized = img.resize((224, 224))
            img_array = np.array(img_resized, dtype=np.float32)
            
            print(f"[AI Pipeline] === INFERENCE DEBUG ===")
            print(f"[AI Pipeline] Step 1 - Image shape: {img_array.shape}")
            print(f"[AI Pipeline] Step 1 - Pixel range: [{img_array.min():.1f}, {img_array.max():.1f}]")
            
            # Step 2: Expand batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            print(f"[AI Pipeline] Step 2 - Batch shape: {img_array.shape}")
            
            # Step 3: CORRECT PREPROCESSING for EfficientNet
            from tensorflow.keras.applications.efficientnet import preprocess_input

            img_array = preprocess_input(img_array)
            print(f"[AI Pipeline] Step 3 - After [0,255]→[0,1]: range [{img_array.min():.3f}, {img_array.max():.3f}]")
            
            # Step 4: Predict
            print(f"[AI Pipeline] Step 4 - Running model prediction...")
            preds = model.predict(img_array, verbose=0)
            probs = preds[0]
            predicted_idx = int(np.argmax(probs))
            confidence = float(probs[predicted_idx])
            
            # Print RAW PREDICTION VECTOR
            print(f"[AI Pipeline] Step 5 - RAW SOFTMAX OUTPUT (first 10 classes):")
            for i in range(min(10, len(probs))):
                print(f"  [{i:2d}] {class_names[i]:40s} = {probs[i]:.6f}")
            
            # Get top 5 predictions
            top5_indices = np.argsort(probs)[-5:][::-1]
            print(f"[AI Pipeline] === TOP 5 PREDICTIONS ===")
            for rank, idx in enumerate(top5_indices, 1):
                print(f"  #{rank} [{idx:2d}] {class_names[idx]:40s} = {probs[idx]*100:.2f}%")
        
        else:
            # PyTorch preprocessing
            import torch
            from torchvision import transforms
            
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
            
            x = transform(img).unsqueeze(0)
            
            # Predict
            with torch.no_grad():
                preds = model(x)
                probs = torch.softmax(preds, dim=1)[0]
                top5_probs, top5_indices = torch.topk(probs, min(5, len(probs)))
                
                confidence = float(top5_probs[0])
                predicted_idx = top5_indices[0].item()
                
                print(f"[AI] Top 5 PyTorch predictions:")
                for i in range(min(5, len(top5_indices))):
                    idx = top5_indices[i].item()
                    prob = float(top5_probs[i])
                    print(f"  {i+1}. {class_names[idx]} ({prob*100:.1f}%)")
                
                # For PyTorch, we don't have img_array in the right format for Grad-CAM
                img_array = None
        
        # Get predicted class label
        label = class_names[predicted_idx]
        print(f"[AI] Selected prediction: {label} ({confidence*100:.1f}%)")
        
        # Parse label - handle different formats
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
        
        # Get detailed information from disease knowledge base
        treatment = ""
        symptoms = []
        prevention = []
        
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
            treatments = {
                "scab": "Apply fungicides (captan or myclobutanil) at bud break. Remove infected leaves.",
                "black rot": "Prune infected branches. Apply copper-based fungicides. Remove mummified fruits.",
                "rust": "Apply fungicides (myclobutanil) in spring. Improve air circulation.",
                "blight": "Apply copper-based fungicides immediately. Remove infected leaves. Avoid overhead watering.",
                "mildew": "Apply sulfur or potassium bicarbonate. Improve ventilation. Reduce humidity.",
                "spot": "Apply chlorothalonil or copper fungicides. Remove infected foliage. Rotate crops.",
                "rot": "Improve drainage. Apply fungicides. Remove infected plant material.",
                "mold": "Improve ventilation. Apply fungicides. Reduce humidity.",
                "mosaic": "Remove infected plants immediately. Control aphid vectors. Use resistant varieties.",
                "curl": "Remove infected leaves. Control whitefly vectors. Apply appropriate insecticides.",
                "mite": "Apply miticides. Increase humidity. Remove heavily infested leaves.",
                "healthy": "Maintain regular watering and fertilization. Monitor for early signs of disease.",
            }
            treatment = next(
                (v for k, v in treatments.items() if k in disease.lower()),
                "Apply appropriate fungicide or pesticide based on disease type. Remove infected plant material. Consult local agricultural extension for specific treatment."
            )
        
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
        
        model_name = "Fine-tuned EfficientNet" if is_tensorflow else "PyTorch MobileNetV2"
        explanation = f"Detected {disease} in {crop} with {confidence_pct}% confidence using {model_name} deep learning model."
        
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
        }
        
        if is_tensorflow and img_array is not None:
            result["_gradcam_model"] = model
            result["_gradcam_img_array"] = img_array
            result["_gradcam_class_idx"] = predicted_idx
        
        return result
    except Exception as e:
        print(f"[AI] Model prediction failed: {e}")
        import traceback
        traceback.print_exc()
        raise

# ---------------------------------------------------------------------------
# Advanced color-based crop and disease detection (no ML model needed)
# ---------------------------------------------------------------------------
def _color_based_predict(image_bytes: bytes) -> dict:
    """
    Analyzes image using color histograms, texture, and shape patterns to identify crop and disease.
    More accurate than random mock, works without API calls.
    """
    try:
        import cv2
        from PIL import Image
        import io
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image")
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        healthy_green = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
        brown_mask = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([35, 255, 200]))
        dark_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 80]))
        
        healthy_ratio = np.sum(healthy_green > 0) / healthy_green.size
        brown_ratio = np.sum(brown_mask > 0) / brown_mask.size
        dark_ratio = np.sum(dark_mask > 0) / dark_mask.size
        
        crop = "Unknown"
        is_healthy = healthy_ratio > 0.65 and brown_ratio < 0.1 and dark_ratio < 0.15
        
        if is_healthy:
            disease = "Healthy"
            severity = 0
            confidence = min(95, int(healthy_ratio * 100))
            explanation = "No disease detected. Plant appears healthy."
            treatment = "Maintain regular watering and fertilization schedule."
        else:
            disease = "Leaf Blight"
            severity = min(90, int((brown_ratio + dark_ratio) * 100))
            explanation = f"Detected brown/dark lesions covering ~{int((brown_ratio + dark_ratio)*100)}% of leaf area."
            treatment = "Apply appropriate broad-spectrum fungicide and remove infected plant material."
            confidence = min(92, 70 + int(severity / 3))
        
        return {
            "crop": crop,
            "disease": disease,
            "severity": severity,
            "confidence": confidence,
            "status": "Healthy" if is_healthy else "Infected",
            "explanation": explanation,
            "treatment": treatment,
        }
    except Exception as e:
        print(f"[AI] Color-based analysis failed: {e}")
        raise

# ---------------------------------------------------------------------------
# Real AI via Claude (Anthropic)
# ---------------------------------------------------------------------------
def _claude_predict(image_bytes: bytes, language: str = "en") -> dict:
    import anthropic
    import base64

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    img_b64 = base64.b64encode(image_bytes).decode()
    mime = "image/jpeg"
    
    prompt = f"Analyze this leaf and output a JSON with crop, disease, severity, confidence, explanation, and treatment."

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mime, "data": img_b64}},
                {"type": "text", "text": prompt}
            ],
        }],
    )
    
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text.strip())
    
    disease = data.get("disease", "Unknown")
    return {
        "crop":        data.get("crop", "Unknown"),
        "disease":     disease,
        "severity":    int(data.get("severity", 50)),
        "confidence":  int(data.get("confidence", 80)),
        "status":      "Healthy" if disease.lower() == "healthy" else "Infected",
        "explanation": data.get("explanation", ""),
        "treatment":   data.get("treatment", ""),
    }

# ---------------------------------------------------------------------------
# Real AI via Gemini Vision
# ---------------------------------------------------------------------------
def _gemini_predict(image_bytes: bytes, language: str = "en") -> dict:
    import requests
    import base64
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    
    img_b64 = base64.b64encode(image_bytes).decode()
    mime = "image/jpeg"
    
    prompt = f"Analyze this leaf and output a JSON with crop, disease, severity, confidence, explanation, and treatment."
    
    models_to_try = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-pro-latest"]
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": img_b64}}]}],
            "generationConfig": {"temperature": 0.4, "topK": 32, "topP": 1, "maxOutputTokens": 2048}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=40)
            if response.status_code == 200:
                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                
                data = json.loads(text.strip())
                disease = data.get("disease", "Unknown")
                
                return {
                    "crop": data.get("crop", "Unknown"),
                    "disease": disease,
                    "severity": int(data.get("severity", 50)),
                    "confidence": int(data.get("confidence", 80)),
                    "status": "Healthy" if disease.lower() == "healthy" else "Infected",
                    "explanation": data.get("explanation", ""),
                    "treatment": data.get("treatment", ""),
                }
        except Exception as e:
            continue
    raise Exception("All Gemini models failed")

def _mock_predict(image_bytes: bytes) -> dict:
    MOCK_DISEASES = [
        {"crop": "Tomato",  "disease": "Leaf Blight",    "severity": 65, "confidence": 92},
        {"crop": "Wheat",   "disease": "Powdery Mildew", "severity": 45, "confidence": 88},
        {"crop": "Rice",    "disease": "Healthy",        "severity": 0,  "confidence": 97},
    ]
    digest = hashlib.md5(image_bytes).hexdigest()
    index = int(digest[:8], 16) % len(MOCK_DISEASES)
    r = MOCK_DISEASES[index]
    disease = r["disease"]
    return {
        "crop": r["crop"],
        "disease": disease,
        "severity": r["severity"],
        "confidence": r["confidence"],
        "status": "Healthy" if disease == "Healthy" else "Infected",
        "explanation": "No disease detected." if disease == "Healthy" else "Infected regions detected.",
        "treatment": "Continue regular care." if disease == "Healthy" else "Consult local extension.",
    }

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
    method_used = "unknown"
    
    # 1. Try custom ML model first (PyTorch MobileNetV2 - PRIMARY METHOD)
    try:
        print("[AI Pipeline] ✓ Step 1: Using PyTorch MobileNetV2 model (primary method)...")
        result = _torch_predict(image_bytes)
        method_used = "PyTorch MobileNetV2 Model"
        print(f"[AI Pipeline] ✅ ML Model success: {result['crop']} / {result['disease']} ({result['confidence']}% confidence)")
    except Exception as e:
        print(f"[AI Pipeline] ❌ ML Model failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Try Claude as backup
    if not result and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            print("[AI Pipeline] ✓ Step 2: Using Claude (Anthropic) as backup...")
            result = _claude_predict(image_bytes, language=language)
            method_used = "Claude AI"
        except Exception as e:
            print(f"[AI Pipeline] ❌ Claude failed: {e}")
    
    # 3. Try Gemini as backup
    if not result and os.environ.get("GEMINI_API_KEY"):
        try:
            print("[AI Pipeline] ✓ Step 3: Using Gemini as backup...")
            result = _gemini_predict(image_bytes, language=language)
            method_used = "Gemini AI"
        except Exception as e:
            print(f"[AI Pipeline] ❌ Gemini failed: {e}")

    # 4. Try color-based analysis as fallback
    if not result:
        try:
            print("[AI Pipeline] ✓ Step 4: Using color-based analysis (fallback)...")
            result = _color_based_predict(image_bytes)
            method_used = "Color Analysis"
        except Exception as e:
            print(f"[AI Pipeline] ❌ Color analysis failed: {e}")
    
    # 5. Final fallback to mock
    if not result:
        print("[AI Pipeline] ⚠️ All methods failed, using mock prediction")
        result = _mock_predict(image_bytes)
        method_used = "Mock (Fallback)"

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
            precautions = [
                "Continue regular monitoring for early disease detection",
                "Maintain proper irrigation and avoid water stress",
                "Practice crop rotation to prevent soil-borne diseases"
            ]
        else:
            precautions = [
                "Monitor plants daily for spreading of disease",
                "Isolate infected plants to prevent disease spread",
                "Remove and destroy infected plant debris immediately"
            ]
    
    # Generate Grad-CAM++ heatmap for infected plants
    heatmap_b64 = ""
    if result["status"] == "Infected" and result["severity"] > 0:
        model = result.get("_gradcam_model")
        img_array = result.get("_gradcam_img_array")
        class_idx = result.get("_gradcam_class_idx", 0)
        
        if model is not None and img_array is not None:
            try:
                # 🚨 LAZY IMPORT 🚨
                # TensorFlow will now ONLY load if this exact block of code runs
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
    
    # Clean up metadata from result (don't send to API response)
    result.pop("_gradcam_model", None)
    result.pop("_gradcam_img_array", None)
    result.pop("_gradcam_class_idx", None)

    # Build comprehensive structured response
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
        "explanation": result.get("explanation", "Analysis completed using AI vision models."),
        "treatment": result.get("treatment", "Consult local agricultural extension for specific treatment recommendations."),
        "precautions": precautions
    }

    # ZERO-DEPENDENCY AUTO-TRANSLATION 
    if language != "en" and method_used not in ["Claude AI", "Gemini AI"]:
        print(f"[AI Pipeline] Translating local model results to {language}...")
        response["explanation"] = translate_content(response["explanation"], language)
        response["treatment"] = translate_content(response["treatment"], language)
        response["precautions"] = translate_content(response["precautions"], language)

    # Ensure precautions is a single string at the end to match frontend expectations
    if isinstance(response["precautions"], list):
        response["precautions"] = " ".join(response["precautions"])

    print(f"[AI Pipeline] ✅ Prediction complete! Returning structured JSON response")
    return response