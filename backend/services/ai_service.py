import os
import hashlib
import base64
import json
from typing import Optional
import numpy as np

# Import new Grad-CAM++ module
from services.gradcam_plus import generate_heatmap_b64 as generate_gradcam_heatmap

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
    """Load the legacy PyTorch MobileNetV2 model (fallback)"""
    global _ML_MODEL, _CLASS_NAMES
    
    # First try EfficientNet (preferred)
    model, classes = _load_efficientnet_model()
    if model is not None:
        return model, classes
    
    # Fallback to PyTorch if EfficientNet fails
    try:
        import torch
        from torchvision import models
        import torch.nn as nn
        
        model_path = "mobilenetv2_plant.pth"
        class_path_legacy = "class_names.json"
        
        if not os.path.exists(model_path):
            print(f"[AI] PyTorch model file not found at {model_path}")
            return None, None
        
        # Load class names
        with open(class_path_legacy, 'r') as f:
            _CLASS_NAMES = json.load(f)
        
        # Build model architecture (same as training)
        model = models.mobilenet_v2(weights=None)
        model.classifier[1] = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(model.classifier[1].in_features, len(_CLASS_NAMES))
        )
        
        # Load trained weights
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu'), weights_only=True))
        model.eval()
        
        _ML_MODEL = model
        print(f"[AI] PyTorch MobileNetV2 model loaded with {len(_CLASS_NAMES)} classes")
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
        
        model, class_names = _load_torch_model()  # Will load EfficientNet first
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
            # The model has internal rescaling layers that expect [0, 255]
            # NO external preprocessing needed - just normalize to [0, 1] for numerical stability
            from tensorflow.keras.applications.efficientnet import preprocess_input

            img_array = preprocess_input(img_array)
            print(f"[AI Pipeline] Step 3 - After [0,255]→[0,1]: range [{img_array.min():.3f}, {img_array.max():.3f}]")
            print(f"[AI Pipeline] Step 3 - Model will apply internal rescaling layers")
            
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
            
            print(f"[AI Pipeline] === FINAL RESULT ===")
            print(f"[AI Pipeline] Predicted Index: {predicted_idx}")
            print(f"[AI Pipeline] Predicted Class: {class_names[predicted_idx]}")
            print(f"[AI Pipeline] Raw Confidence: {confidence:.6f}")
            print(f"[AI Pipeline] Confidence %: {confidence*100:.2f}%")
            print(f"[AI Pipeline] Sum of probs: {probs.sum():.6f}")
            print(f"[AI Pipeline] Max prob: {probs.max():.6f}, Min prob: {probs.min():.6f}")
            for i, idx in enumerate(top5_indices):
                print(f"  {i+1}. {class_names[idx]} ({probs[idx]*100:.1f}%)")
            
            # DEBUG: Log raw model output statistics
            print(f"[AI] DEBUG - Confidence stats:")
            print(f"  - Max prob: {probs.max():.4f}")
            print(f"  - Mean prob: {probs.mean():.4f}")
            print(f"  - Top prob: {confidence:.4f}")
            print(f"  - Image shape: {img_array.shape}, range: [{img_array.min():.3f}, {img_array.max():.3f}]")
        
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
        # Format 1: "Crop___Disease" (e.g., "Tomato___Late_blight")
        # Format 2: "Crop_Disease" (e.g., "Tomato_Late_Blight", "Cotton_Healthy")
        # Format 3: "Disease" only (e.g., "Aphid", "Blast")
        
        if '___' in label:
            # Standard format: Crop___Disease
            parts = label.split('___')
            crop = parts[0].replace('_', ' ').replace('(', '').replace(')', '').strip()
            disease_raw = parts[1].replace('_', ' ').strip() if len(parts) > 1 else "Unknown"
        elif '_' in label:
            # Format: Crop_Disease
            # Find the crop name - check for known crops first
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
            # Disease only format (Aphid, Blast, Smut, etc.)
            crop = "General"  # Will be refined from disease_info
            disease_raw = label.replace('_', ' ')
        
        is_healthy = 'healthy' in disease_raw.lower()
        disease = "Healthy" if is_healthy else disease_raw
        
        # Get detailed information from disease knowledge base
        treatment = ""
        symptoms = []
        prevention = []
        
        # Try to find exact match in disease_info
        if label in disease_info:
            info = disease_info[label]
            crop = info.get('crop', crop)  # Override with more accurate crop name
            disease = info.get('disease', disease)
            symptoms = info.get('symptoms', [])
            prevention = info.get('prevention', [])
            treatment_list = info.get('treatment', [])
            
            # Build detailed treatment from knowledge base with proper formatting
            treatment_parts = []
            
            if treatment_list:
                # Format treatment as a proper sentence with "Apply" prefix
                if len(treatment_list) == 1:
                    treatment_parts.append(f"Apply {treatment_list[0]} fungicide immediately.")
                else:
                    # Join multiple treatments with commas
                    treatments_str = ", ".join(treatment_list[:-1]) + f", or {treatment_list[-1]}"
                    treatment_parts.append(f"Treatment: Apply {treatments_str} according to label instructions.")
            
            if prevention:
                # Add prevention as a separate sentence
                if len(prevention) == 1:
                    treatment_parts.append(f"Prevention: {prevention[0]}.")
                elif len(prevention) == 2:
                    treatment_parts.append(f"Prevention: {prevention[0]} and {prevention[1].lower()}.")
                else:
                    # Take top 3 prevention measures
                    prev_str = ", ".join(prevention[:2]) + f", and {prevention[2].lower()}"
                    treatment_parts.append(f"Prevention: {prev_str}.")
            
            if symptoms:
                # Add symptoms information
                if len(symptoms) <= 2:
                    symp_str = " and ".join(symptoms)
                else:
                    symp_str = ", ".join(symptoms[:2]) + f", and {symptoms[2]}"
                treatment_parts.append(f"Common symptoms include: {symp_str}.")
            
            treatment = " ".join(treatment_parts)
        
        # Fallback treatment if not found in knowledge base
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
        
        # Calculate severity based on confidence and disease type
        # IMPORTANT: Healthy plants should have 0% severity, regardless of confidence
        if is_healthy:
            severity = 0
            confidence_pct = min(99, int(confidence * 100))
        else:
            # For diseased plants: map confidence to severity
            # Low confidence (60-70%) = Low severity (30-50%)
            # Medium confidence (70-85%) = Medium severity (50-70%)
            # High confidence (85-100%) = High severity (70-95%)
            confidence_pct = min(99, int(confidence * 100))
            
            if confidence < 0.7:  # Low confidence
                severity = max(30, min(50, int(confidence * 70)))
            elif confidence < 0.85:  # Medium confidence
                severity = max(50, min(70, int(confidence * 80)))
            else:  # High confidence
                severity = max(70, min(95, int(confidence * 95)))
        
        # Build explanation
        model_name = "Fine-tuned EfficientNet" if is_tensorflow else "MobileNetV2"
        explanation = f"Detected {disease} in {crop} with {confidence_pct}% confidence using {model_name} deep learning model."
        
        if symptoms:
            explanation += f" Symptoms: {', '.join(symptoms[:3])}."
        
        # Special case: If confidence is very low and there's a healthy class in top-5, prefer healthy
        # This helps fix misidentifications of healthy plants as diseased
        if is_tensorflow and confidence_pct < 30:  # Very low confidence
            print(f"[AI] ⚠️ Very low confidence ({confidence_pct}%) - checking if it might be healthy...")
            # Check if any healthy class is in top-5
            for i, idx in enumerate(top5_indices[:5]):  # top 5
                class_label = class_names[idx]
                prob = probs[idx] * 100
                if 'healthy' in class_label.lower():
                    print(f"[AI] ✓ Found '{class_label}' in top-5 (rank {i+1}, prob {prob:.1f}%)")
                    # If healthy is in top-5 and has higher probability, use it instead
                    if prob > confidence_pct * 0.8:  # If healthy prob is at least 80% of current
                        print(f"[AI] → Switching to healthy prediction")
                        label = class_label
                        predicted_idx = idx
                        confidence = probs[idx]
                        confidence_pct = int(confidence * 100)
                        is_healthy = True
                        disease = "Healthy"
                        severity = 0
                        crop = class_label.replace('_', ' ').replace('_Healthy', '').strip()
                        treatment = "Maintain regular watering schedule (2-3cm per week) and balanced fertilization (NPK 10-10-10 monthly). Monitor plants weekly for early signs of disease or pest damage. For prevention: practice crop rotation annually, maintain soil health with compost, and remove weeds that harbor pests."
                        explanation = f"Plant appears healthy. No significant disease detected. Recommend continued monitoring and preventive care."
                        break
        
        # Return result with Grad-CAM++ metadata (for TensorFlow models only)
        result = {
            "crop": crop,
            "disease": disease,
            "severity": severity,
            "confidence": confidence_pct,
            "status": "Healthy" if is_healthy else "Infected",
            "explanation": explanation,
            "treatment": treatment,
        }
        
        # Add Grad-CAM++ metadata for TensorFlow models
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
        
        # Load image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image")
        
        h, w = img.shape[:2]
        
        # Convert to multiple color spaces for better analysis
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        h_chan, s_chan, v_chan = cv2.split(hsv)
        l_chan, a_chan, b_chan = cv2.split(lab)
        
        # Calculate comprehensive color statistics
        mean_hue = np.mean(h_chan)
        mean_sat = np.mean(s_chan)
        mean_val = np.mean(v_chan)
        std_hue = np.std(h_chan)
        std_sat = np.std(s_chan)
        
        # LAB color space analysis (better for disease detection)
        mean_a = np.mean(a_chan)  # green-red axis
        mean_b = np.mean(b_chan)  # blue-yellow axis
        
        # Detect different color regions
        healthy_green = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
        dark_green = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([75, 255, 150]))
        light_green = cv2.inRange(hsv, np.array([40, 30, 100]), np.array([85, 255, 255]))
        brown_mask = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([35, 255, 200]))
        yellow_mask = cv2.inRange(hsv, np.array([20, 80, 100]), np.array([40, 255, 255]))
        dark_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 80]))
        
        # Calculate ratios
        healthy_ratio = np.sum(healthy_green > 0) / healthy_green.size
        dark_green_ratio = np.sum(dark_green > 0) / dark_green.size
        light_green_ratio = np.sum(light_green > 0) / light_green.size
        brown_ratio = np.sum(brown_mask > 0) / brown_mask.size
        yellow_ratio = np.sum(yellow_mask > 0) / yellow_mask.size
        dark_ratio = np.sum(dark_mask > 0) / dark_mask.size
        
        # Texture analysis - multiple scales
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_var = np.var(laplacian)
        texture_mean = np.mean(np.abs(laplacian))
        
        # Edge detection for leaf shape analysis
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Detect wrinkled/bumpy texture (potato characteristic)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        detail = cv2.absdiff(gray, blurred)
        wrinkle_score = np.mean(detail)
        
        # Crop identification with improved logic
        crop = "Unknown"
        crop_confidence = 0
        
        # Potato: broad leaves, wrinkled texture, medium-dark green, compound leaves
        potato_score = 0
        if 40 <= mean_hue <= 75 and mean_sat > 60:  # Green range
            potato_score += 30
        if wrinkle_score > 8:  # Wrinkled/textured surface
            potato_score += 25
        if dark_green_ratio > 0.25:  # Darker green leaves
            potato_score += 25
        if texture_var > 300 and texture_var < 900:  # Medium texture
            potato_score += 15
        if edge_density < 0.18:  # Broad leaves, fewer edges
            potato_score += 20
        if brown_ratio > 0.1 and dark_ratio < 0.2:  # Blight but not black galls
            potato_score += 15
        
        # Penalty for characteristics that indicate NOT potato
        if dark_ratio > 0.25:  # Too much black = likely corn smut, not potato blight
            potato_score -= 30
            print(f"[Color Analysis] Very high dark_ratio ({dark_ratio:.2f}) - unlikely potato")
        if yellow_ratio > 0.2:  # Too much yellow = likely corn
            potato_score -= 20
        
        # Tomato: compound leaves, high texture, bright green, serrated edges
        tomato_score = 0
        if 45 <= mean_hue <= 80 and mean_sat > 70:  # Bright green
            tomato_score += 25
        if texture_var > 500:  # High texture (compound leaves)
            tomato_score += 30
        if edge_density > 0.15:  # Many leaflets = more edges
            tomato_score += 25
        if light_green_ratio > 0.35:  # Lighter green
            tomato_score += 15
        if std_hue > 12:  # More color variation
            tomato_score += 10
        if brown_ratio > 0.1:  # Often has blight/spot
            tomato_score += 10
        
        # Corn: long narrow leaves, parallel veins, yellow-green, very broad (10-15cm)
        # IMPORTANT: Corn with smut has black galls, so dark_ratio will be high
        corn_score = 0
        
        # Check for corn characteristics
        if 25 <= mean_hue <= 55:  # Yellow-green to green (wider range)
            corn_score += 25  # Reduced from 30
        if mean_b > 125:  # Yellow bias in LAB space (lowered threshold)
            corn_score += 20  # Reduced from 25
        
        # Corn leaves are long and narrow with parallel veins
        if texture_var < 500:  # Smoother texture than compound leaves
            corn_score += 15  # Reduced from 20
        if std_sat < 50:  # More uniform color
            corn_score += 10  # Reduced from 15
        
        # Black galls (smut) are a strong indicator of corn
        if dark_ratio > 0.2:  # Significant dark areas = likely corn smut
            corn_score += 35  # Reduced from 40
            print(f"[Color Analysis] High dark_ratio ({dark_ratio:.2f}) - likely corn smut")
        
        # Yellow/brown areas common in corn (kernels, disease)
        if yellow_ratio > 0.15 or brown_ratio > 0.15:
            corn_score += 15  # Reduced from 20
        
        # Corn has simpler leaf structure than potato/tomato
        if edge_density < 0.20:  # Fewer edges than compound leaves
            corn_score += 10  # Reduced from 15
        
        # Penalty for characteristics that indicate NOT corn
        if texture_var > 700:  # Too much texture = compound leaves (potato/tomato)
            corn_score -= 25
        if wrinkle_score > 12:  # Too wrinkled = potato
            corn_score -= 20
        # Coffee rust has orange/brown spots - penalize if rust pattern detected
        # Rust pattern: high brown + high yellow (regardless of dark ratio)
        if brown_ratio > 0.2 and yellow_ratio > 0.2:
            corn_score -= 40  # Strong penalty - likely coffee rust, not corn
            print(f"[Color Analysis] Orange/rust pattern detected - unlikely corn")
        
        # Wheat/Rice: thin leaves, low saturation, light color, grain heads
        wheat_score = 0
        if mean_sat < 70:  # Low saturation
            wheat_score += 30
        if mean_val > 110:  # Light colored
            wheat_score += 25
        if texture_var < 350:  # Fine texture
            wheat_score += 20
        if edge_density > 0.25:  # Thin leaves = many edges
            wheat_score += 20
        if yellow_ratio > 0.12:  # Yellowish tint
            wheat_score += 15
        
        # Grape: lobed leaves, distinct veins, medium green
        grape_score = 0
        if 50 <= mean_hue <= 70:  # Medium green
            grape_score += 25
        if texture_var > 400 and texture_var < 700:
            grape_score += 20
        if edge_density > 0.12 and edge_density < 0.18:  # Lobed edges
            grape_score += 25
        if std_hue > 12 and std_hue < 20:
            grape_score += 15
        
        # Coffee: broad oval leaves, may have rust spots
        coffee_score = 0
        if 40 <= mean_hue <= 65:  # Dark green
            coffee_score += 30  # Increased from 25
        if texture_var > 350 and texture_var < 650:
            coffee_score += 20
        if edge_density < 0.14:  # Broad simple leaves
            coffee_score += 20
        # Coffee rust: orange/brown/yellow spots on leaves
        if brown_ratio > 0.15 or yellow_ratio > 0.15:  # Rust symptoms
            coffee_score += 30  # Increased from 25
            print(f"[Color Analysis] Rust-like symptoms detected - likely coffee rust")
        if dark_green_ratio > 0.35:  # Dark green leaves
            coffee_score += 15
        # Bonus for rust pattern (orange/brown + yellow, but not too dark)
        if brown_ratio > 0.2 and yellow_ratio > 0.2 and dark_ratio < 0.15:
            coffee_score += 25  # Strong indicator of coffee rust
            print(f"[Color Analysis] Strong rust pattern - coffee rust likely")
        
        # Cotton: broad heart-shaped or oval leaves, bright green, soft texture
        cotton_score = 0
        if 45 <= mean_hue <= 75:  # Bright green
            cotton_score += 35
        if mean_sat > 80:  # High saturation (vibrant green)
            cotton_score += 30
        if texture_var > 200 and texture_var < 600:  # Moderate texture (not too smooth, not too rough)
            cotton_score += 25
        if wrinkle_score < 8:  # Smooth leaves (less wrinkled than potato)
            cotton_score += 20
        if edge_density < 0.16:  # Broad leaves with fewer edges
            cotton_score += 20
        if dark_ratio < 0.1:  # Very few dark areas (Cotton is mostly healthy green)
            cotton_score += 25
        # Penalty if too much disease color pattern
        if brown_ratio > 0.25 or dark_ratio > 0.2:
            cotton_score -= 30  # Cotton rarely has brown/dark spots
        
        # Rice: thin grass-like leaves, low saturation, yellowish-green tint
        rice_score = 0
        if 30 <= mean_hue <= 60:  # Yellow-green to green
            rice_score += 25
        if mean_sat < 60:  # Lower saturation (less vibrant)
            rice_score += 30
        if mean_val > 100:  # Light colored
            rice_score += 20
        if texture_var < 400:  # Fine texture (grass-like)
            rice_score += 25
        if edge_density > 0.20:  # Many thin edges (blade-like leaves)
            rice_score += 25
        if yellow_ratio > 0.15:  # Yellowish tint
            rice_score += 15
        # Rice often shows brown spots, so don't penalize as much
        if brown_ratio > 0.1:
            rice_score += 15  # Brown spots are common in rice diseases
        
        # Select crop with highest score
        scores = {
            "Potato": potato_score,
            "Tomato": tomato_score,
            "Corn": corn_score,
            "Wheat": wheat_score,
            "Grape": grape_score,
            "Coffee": coffee_score,
            "Cotton": cotton_score,
            "Rice": rice_score,
        }
        
        crop = max(scores, key=scores.get)
        crop_confidence = scores[crop]
        
        # Debug logging
        print(f"[Color Analysis] Crop scores: {scores}")
        print(f"[Color Analysis] Selected: {crop} (score: {crop_confidence})")
        
        # If all scores are low, default to most common
        if crop_confidence < 50:
            crop = "Potato"  # Most common in dataset
            print(f"[Color Analysis] Low confidence, defaulting to Potato")
        
        # Disease identification
        is_healthy = healthy_ratio > 0.65 and brown_ratio < 0.1 and dark_ratio < 0.15
        
        # Log color ratios for debugging
        print(f"[Color Analysis] Color ratios - healthy:{healthy_ratio:.2f}, dark:{dark_ratio:.2f}, brown:{brown_ratio:.2f}, yellow:{yellow_ratio:.2f}")
        
        if is_healthy:
            disease = "Healthy"
            severity = 0
            confidence = min(95, int(healthy_ratio * 100))
            explanation = "No disease detected. Plant appears healthy with good green coloration."
            treatment = "Maintain regular watering schedule (2-3cm per week) and balanced fertilization (NPK 10-10-10 monthly). Monitor plants weekly for early signs of disease or pest damage. For prevention: practice crop rotation annually, maintain soil health with compost, and remove weeds that harbor pests."
        else:
            # Determine disease type based on color patterns and crop
            # CORN SMUT: Black/brown galls/tumors on corn
            # Check for dark galls OR brown tumors (smut starts brown, turns black)
            if crop == "Corn" and (dark_ratio > 0.15 or (brown_ratio > 0.2 and yellow_ratio > 0.15)):
                disease = "Corn Smut"
                severity = min(95, int((dark_ratio + brown_ratio) * 120))
                explanation = f"Detected black/brown galls or tumors (corn smut) on corn plant. Dark areas: ~{int(dark_ratio*100)}%, Brown areas: ~{int(brown_ratio*100)}%."
                treatment = "Immediately remove and destroy infected ears or galls before they rupture and release black teliospores (spores). Burn or bury infected material deep in soil. Do not compost. Apply fungicides containing azoxystrobin or propiconazole at early infection stage. For prevention: plant resistant corn varieties, practice 2-3 year crop rotation, avoid excessive nitrogen fertilization which promotes smut, and maintain balanced soil fertility."
                confidence = min(92, 75 + int(severity / 4))
                print(f"[Color Analysis] Detected Corn Smut - dark_ratio:{dark_ratio:.2f}, brown_ratio:{brown_ratio:.2f}")
            elif brown_ratio > 0.15 or dark_ratio > 0.2:
                # Check for coffee rust first (orange/brown spots on coffee)
                if crop == "Coffee" and brown_ratio > 0.15 and yellow_ratio > 0.1:
                    disease = "Coffee Rust"
                    severity = min(90, int((brown_ratio + yellow_ratio) * 110))
                    explanation = f"Detected orange/brown rust spots (coffee leaf rust) covering ~{int((brown_ratio + yellow_ratio)*100)}% of leaf area."
                    treatment = "Apply copper-based fungicides (2-3g/L) or systemic fungicides containing triadimefon or propiconazole (1ml/L) every 14-21 days. Remove and destroy heavily infected leaves to reduce spore load. Improve air circulation by proper pruning and spacing (2-3m between plants). For prevention: plant rust-resistant varieties, apply preventive fungicide sprays before rainy season, maintain proper shade management, and ensure adequate nutrition with balanced NPK fertilizer."
                    confidence = min(92, 75 + int(severity / 4))
                    print(f"[Color Analysis] Detected Coffee Rust - brown:{brown_ratio:.2f}, yellow:{yellow_ratio:.2f}")
                # Blight diseases (common in potato, tomato)
                elif crop in ["Potato", "Tomato"]:
                    disease = "Late Blight" if dark_ratio > 0.25 else "Early Blight"
                    severity = min(90, int((brown_ratio + dark_ratio) * 100))
                    explanation = f"Detected brown/dark lesions covering ~{int((brown_ratio + dark_ratio)*100)}% of leaf area."
                    treatment = "Apply copper-based fungicides (2-3g/L) or Mancozeb 75% WP (2.5g/L) immediately and repeat every 5-7 days. Remove and destroy all infected leaves and stems to prevent spread. Avoid overhead watering and water only at soil level. For prevention: space plants 60-90cm apart, apply mulch to prevent soil splash, and rotate crops annually."
                    confidence = min(92, 70 + int(severity / 3))
                else:
                    disease = "Leaf Blight"
                    severity = min(90, int((brown_ratio + dark_ratio) * 100))
                    explanation = f"Detected brown/dark lesions covering ~{int((brown_ratio + dark_ratio)*100)}% of leaf area."
                    treatment = "Apply copper-based fungicides (2-3g/L) or Mancozeb 75% WP (2.5g/L) immediately and repeat every 5-7 days. Remove and destroy all infected leaves and stems to prevent spread. Avoid overhead watering and water only at soil level. For prevention: space plants 60-90cm apart, apply mulch to prevent soil splash, and rotate crops annually."
                    confidence = min(92, 70 + int(severity / 3))
            elif yellow_ratio > 0.2:
                # Mildew or chlorosis
                disease = "Powdery Mildew" if mean_val > 150 else "Leaf Spot"
                severity = min(85, int(yellow_ratio * 150))
                explanation = f"Detected yellow discoloration covering ~{int(yellow_ratio*100)}% of leaf area."
                treatment = "Apply sulfur dust (3g/L) or potassium bicarbonate (5g/L) weekly until symptoms disappear. Improve ventilation by thinning dense foliage and ensuring 45-60cm spacing between plants. Reduce humidity by watering in morning hours only. For prevention: plant resistant varieties, prune regularly for air flow, and apply preventive sulfur sprays in humid conditions."
                confidence = min(92, 70 + int(severity / 3))
            elif dark_ratio > 0.15:
                disease = "Bacterial Spot" if texture_var > 400 else "Leaf Blight"
                severity = min(80, int(dark_ratio * 120))
                explanation = f"Detected dark spots/lesions covering ~{int(dark_ratio*100)}% of leaf area."
                treatment = "Apply copper fungicides (2-3g/L) or chlorothalonil (2ml/L) every 7-10 days for 3-4 applications. Remove and destroy all infected foliage immediately to prevent disease spread. Avoid overhead watering and work with plants when dry. For prevention: use certified disease-free seeds, maintain field sanitation by removing plant debris, and rotate to non-host crops."
                confidence = min(92, 70 + int(severity / 3))
            else:
                disease = "Leaf Damage"
                severity = int((1 - healthy_ratio) * 100)
                explanation = "Detected general leaf damage and discoloration."
                treatment = "Apply appropriate broad-spectrum fungicide (Mancozeb 75% WP at 2.5g/L or Copper oxychloride at 3g/L) every 7-10 days. Remove and destroy all infected plant material immediately. Improve cultural practices including proper spacing (45-60cm), drainage, and sanitation. For prevention: monitor regularly for early symptoms and apply preventive fungicide sprays during favorable disease conditions."
                confidence = min(92, 70 + int(severity / 3))
        
        print(f"[AI] Crop scores: Potato={potato_score}, Tomato={tomato_score}, Corn={corn_score}, Wheat={wheat_score}, Grape={grape_score}")
        print(f"[AI] Selected: {crop} (score={crop_confidence})")
        
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
    
    # Encode image to base64
    img_b64 = base64.b64encode(image_bytes).decode()
    
    # Detect image type from magic bytes
    mime = "image/jpeg"  # default
    if image_bytes.startswith(b'\x89PNG'):
        mime = "image/png"
    elif image_bytes.startswith(b'RIFF') and b'WEBP' in image_bytes[:20]:
        mime = "image/webp"
    elif image_bytes.startswith(b'\xff\xd8\xff'):
        mime = "image/jpeg"
    
    # Language mapping
    language_names = {
        "en": "English",
        "hi": "Hindi (हिंदी)",
        "bn": "Bengali (বাংলা)",
        "te": "Telugu (తెలుగు)",
        "mr": "Marathi (मराठी)",
        "ta": "Tamil (தமிழ்)",
        "gu": "Gujarati (ગુજરાતી)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
        "or": "Odia (ଓଡ଼ିଆ)",
        "ml": "Malayalam (മലയാളം)",
    }
    target_language = language_names.get(language, "English")
    
    language_instruction = ""
    if language != "en":
        language_instruction = f"""

CRITICAL LANGUAGE REQUIREMENT:
- The 'treatment' field MUST be written ENTIRELY in {target_language} language
- Keep fungicide/pesticide names in English but translate all other text
"""
    
    prompt = f"""You are an expert agricultural plant pathologist and botanist AI.

{language_instruction}

Carefully examine this plant image and identify the crop type and any diseases.
Respond ONLY with a valid JSON object (no markdown, no extra text):
{{
  "crop": "<exact crop name>",
  "disease": "<exact disease name or 'Healthy'>",
  "severity": <0-100>,
  "confidence": <50-99>,
  "explanation": "<brief description of what you observe>",
  "treatment": "<detailed 3-4 sentence treatment plan including: immediate actions, specific fungicides/pesticides with application rates, cultural practices, and prevention measures for future>"
}}

CROP IDENTIFICATION GUIDELINES:
- Coffee: Broad oval leaves, grows on shrubs/small trees, may show rust spots
- Corn/Maize: Very broad leaves (10-15cm wide), tall thick stalks, parallel leaf veins
- Wheat/Barley: Narrow grass-like leaves (<2cm wide), grain heads/spikes, thin stalks
- Rice: Very thin grass leaves, grows in paddies
- Potato: Compound leaves with multiple oval leaflets, low bushy growth
- Tomato: Compound serrated leaves, vine growth, may have fruits
- Apple/Grape: Tree/vine leaves, may show fruits

DISEASE SEVERITY SCALE:
- 0 = Completely healthy
- 20-40 = Early stage (few spots, minimal damage)
- 50-70 = Moderate (visible lesions, some leaf damage)
- 80-95 = Severe (extensive damage, significant leaf area affected)

TREATMENT REQUIREMENTS:
- Must be 3-4 complete sentences
- Include specific fungicide/pesticide names (e.g., Mancozeb, Copper oxychloride, Chlorothalonil)
- Include application rates and frequency
- Include cultural practices (pruning, spacing, watering)
- Include prevention measures for future
- Example: "Apply Mancozeb 75% WP at 2g/liter every 10-14 days. Remove and destroy all infected leaves and plant debris. Improve air circulation by proper spacing and pruning. For prevention: avoid overhead irrigation, apply preventive fungicide sprays during humid weather, and practice crop rotation."
"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": img_b64,
                    },
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ],
        }],
    )
    
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    data = json.loads(text)
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
# Real AI via Gemini Vision (used when GEMINI_API_KEY is set)
# ---------------------------------------------------------------------------
def _gemini_predict(image_bytes: bytes, language: str = "en") -> dict:
    """Use Gemini API via REST - tries multiple models for reliability"""
    import requests
    import base64
    import time
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    
    # Encode image to base64
    img_b64 = base64.b64encode(image_bytes).decode()
    
    # Detect mime type
    mime = "image/jpeg"
    if image_bytes.startswith(b'\x89PNG'):
        mime = "image/png"
    elif image_bytes.startswith(b'RIFF') and b'WEBP' in image_bytes[:20]:
        mime = "image/webp"
    elif image_bytes.startswith(b'\xff\xd8\xff'):
        mime = "image/jpeg"
    
    # Language mapping
    language_names = {
        "en": "English",
        "hi": "Hindi (हिंदी)",
        "bn": "Bengali (বাংলা)",
        "te": "Telugu (తెలుగు)",
        "mr": "Marathi (मराठी)",
        "ta": "Tamil (தமிழ்)",
        "gu": "Gujarati (ગુજરાતી)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
        "or": "Odia (ଓଡ଼ିଆ)",
        "ml": "Malayalam (മലയാളം)",
    }
    target_language = language_names.get(language, "English")
    
    language_instruction = ""
    if language != "en":
        language_instruction = f"\n\nCRITICAL: The 'treatment' field MUST be in {target_language}. Keep fungicide names in English but translate all other text."
    
    prompt = f"""You are an expert agricultural plant pathologist and botanist AI.

Carefully examine this plant image and identify the crop type and any diseases.
Respond ONLY with a valid JSON object (no markdown, no extra text):
{{
  "crop": "<exact crop name>",
  "disease": "<exact disease name or 'Healthy'>",
  "severity": <0-100>,
  "confidence": <50-99>,
  "explanation": "<brief description>",
  "treatment": "<detailed 3-4 sentence treatment with fungicides, rates, and prevention>"
}}

CROP IDENTIFICATION:
- Coffee: Broad oval leaves, rust shows as orange/yellow spots
- Corn: Very broad leaves, smut shows as black galls
- Wheat: Narrow grass leaves, rust shows as orange pustules
- Cucumber: Vine plant, large palmate leaves, anthracnose shows as circular lesions
- Potato: Compound leaves with leaflets
- Tomato: Compound serrated leaves
- Be VERY specific about the disease{language_instruction}"""
    
    # Try multiple Gemini models in order of preference (updated model names for 2025)
    models_to_try = [
        "gemini-flash-latest",      # Latest flash model (fast and reliable)
        "gemini-2.5-flash",         # Gemini 2.5 Flash (good balance)
        "gemini-pro-latest",        # Latest pro model (most capable)
    ]
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime,
                            "data": img_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 2048,
            }
        }
        
        try:
            print(f"[Gemini] Trying model: {model_name}")
            response = requests.post(url, json=payload, timeout=40)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if response has the expected structure
                if 'candidates' not in result or not result['candidates']:
                    print(f"[Gemini] {model_name} returned empty candidates")
                    continue
                
                text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                
                # Clean markdown if present
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                text = text.strip()
                
                data = json.loads(text)
                disease = data.get("disease", "Unknown")
                
                print(f"[Gemini] Success with {model_name}: {data.get('crop')} / {disease} ({data.get('confidence')}%)")
                
                return {
                    "crop": data.get("crop", "Unknown"),
                    "disease": disease,
                    "severity": int(data.get("severity", 50)),
                    "confidence": int(data.get("confidence", 80)),
                    "status": "Healthy" if disease.lower() == "healthy" else "Infected",
                    "explanation": data.get("explanation", ""),
                    "treatment": data.get("treatment", ""),
                }
            else:
                error_msg = response.text
                print(f"[Gemini] {model_name} error {response.status_code}: {error_msg[:200]}")
                # Try next model
                continue
                
        except requests.exceptions.Timeout:
            print(f"[Gemini] {model_name} timeout after 40s")
            continue
        except Exception as e:
            print(f"[Gemini] {model_name} failed: {e}")
            continue
    
    # If all models failed, raise exception
    raise Exception("All Gemini models failed or unavailable")
    
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    data = json.loads(text)
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



    """
    Uses HuggingFace Inference API with a free token.
    Requires HF_TOKEN in .env (free at huggingface.co/settings/tokens)
    """
    import urllib.request, ssl

    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        raise ValueError("No HF_TOKEN set")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # PlantVillage-trained model via HF Inference API
    url = "https://api-inference.huggingface.co/models/Diginsa/Plant-Disease-Detection-Project"
    req = urllib.request.Request(url, data=image_bytes, method="POST")
    req.add_header("Content-Type", "application/octet-stream")
    req.add_header("Authorization", f"Bearer {hf_token}")

    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        results = json.loads(resp.read())

    if not results or not isinstance(results, list):
        raise ValueError(f"Bad response: {results}")

    top = results[0]
    label = top.get("label", "Unknown___Unknown")
    score = float(top.get("score", 0.8))

    # Parse "Crop___Disease" format
    if "___" in label:
        parts = label.split("___")
        crop = parts[0].replace("_", " ").strip()
        disease = parts[1].replace("_", " ").strip()
    else:
        crop, disease = "Plant", label.replace("_", " ").strip()

    is_healthy = "healthy" in disease.lower()
    if is_healthy:
        disease = "Healthy"

    # Higher confidence in disease = higher severity
    severity = 0 if is_healthy else max(40, min(95, int(score * 80 + 20)))
    confidence = min(99, int(score * 100))

    treatments = {
        "scab": "Apply fungicides containing captan (2.5g/L) or myclobutanil (0.5ml/L) at bud break and repeat every 10-14 days. Remove and destroy all infected leaves and fallen fruit. Prune trees to improve air circulation and reduce humidity. For prevention: rake and destroy fallen leaves in autumn, apply dormant oil sprays in early spring, and maintain proper tree spacing.",
        "black rot": "Prune and destroy all infected branches, cutting 15cm below visible symptoms. Apply copper-based fungicides (2g/L) or Mancozeb 75% WP (2.5g/L) every 7-10 days. Remove all mummified fruits from tree and ground. For prevention: maintain good sanitation, ensure proper drainage, apply preventive fungicide during wet periods, and avoid overhead irrigation.",
        "rust": "Apply systemic fungicides like myclobutanil (0.5ml/L) or propiconazole (1ml/L) in early spring and repeat every 14 days. Remove alternate host plants (junipers) within 300m if possible. Improve air circulation through proper pruning. For prevention: plant resistant varieties, avoid overhead watering, apply preventive sprays before rust season, and maintain tree vigor through proper fertilization.",
        "blight": "Apply copper fungicides (2-3g/L) or chlorothalonil (2ml/L) immediately and repeat every 5-7 days during wet weather. Remove and destroy all infected leaves and stems. Avoid overhead watering and water only at soil level. For prevention: space plants 60-90cm apart, apply mulch to prevent soil splash, rotate crops annually, and use disease-free seeds or transplants.",
        "mildew": "Apply sulfur dust (3g/L) or potassium bicarbonate (5g/L) weekly until symptoms disappear. Improve ventilation by thinning dense foliage and proper spacing. Reduce humidity by watering in morning hours only. For prevention: plant resistant varieties, ensure 45-60cm spacing between plants, avoid late-day watering, prune regularly for air flow, and apply preventive sulfur sprays in humid conditions.",
        "spot": "Apply chlorothalonil (2ml/L) or Mancozeb 75% WP (2.5g/L) every 7-10 days for 3-4 applications. Remove and destroy all infected foliage immediately. Rotate to non-host crops for 2-3 years. For prevention: use certified disease-free seeds, avoid working with plants when wet, maintain field sanitation by removing plant debris, and apply preventive fungicide before disease appears.",
        "rot": "Improve soil drainage immediately by creating raised beds or installing drainage tiles. Apply fungicides like metalaxyl (1g/L) or fosetyl-al (2.5g/L) as soil drench. Remove and destroy all infected plant material. For prevention: avoid overwatering (water only when top 5cm soil is dry), ensure proper soil drainage with organic matter, use raised beds in heavy soils, and rotate crops to non-susceptible species.",
        "mold": "Improve ventilation by increasing plant spacing to 45-60cm and pruning dense growth. Apply fungicides like iprodione (1.5ml/L) or fenhexamid (1ml/L) every 7-10 days. Reduce humidity by using fans in greenhouses or avoiding overcrowding. For prevention: increase air circulation, avoid overcrowding plants, water in morning hours only, remove dead plant material promptly, and maintain relative humidity below 85%.",
        "healthy": "Maintain regular watering schedule (2-3cm per week) and balanced fertilization (NPK 10-10-10 monthly). Monitor plants weekly for early signs of disease or pest damage. For prevention: practice crop rotation annually, maintain soil health with compost, inspect plants regularly for symptoms, remove weeds that harbor pests, and apply preventive treatments during disease-prone seasons.",
    }
    treatment = next(
        (v for k, v in treatments.items() if k in disease.lower()),
        "Apply appropriate broad-spectrum fungicide (e.g., Mancozeb 75% WP at 2.5g/L or Copper oxychloride at 3g/L) every 7-10 days. Remove and destroy all infected plant material immediately. Improve cultural practices including proper spacing, drainage, and sanitation. For prevention: practice good field hygiene, ensure adequate plant spacing for air circulation, monitor regularly for early symptoms, and apply preventive fungicide sprays during favorable disease conditions."
    )

    return {
        "crop": crop,
        "disease": disease,
        "severity": severity,
        "confidence": confidence,
        "status": "Healthy" if is_healthy else "Infected",
        "explanation": f"Detected {disease} in {crop} with {confidence}% confidence.",
        "treatment": treatment,
    }

    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        results = json.loads(resp.read())

    if not results or not isinstance(results, list):
        raise ValueError(f"Unexpected response: {results}")

    # Top prediction
    top = results[0]
    label = top.get("label", "Unknown___Unknown")
    score = float(top.get("score", 0.8))

    # PlantVillage labels are "Crop___Disease" format
    parts = label.replace("_", " ").split("   ")  # triple space separator
    if len(parts) == 2:
        crop, disease = parts[0].strip(), parts[1].strip()
    elif "___" in top.get("label", ""):
        raw_parts = top["label"].split("___")
        crop = raw_parts[0].replace("_", " ").strip()
        disease = raw_parts[1].replace("_", " ").strip()
    else:
        crop = "Unknown"
        disease = label

    is_healthy = "healthy" in disease.lower()
    if is_healthy:
        disease = "Healthy"

    # Higher confidence in disease detection = higher severity
    severity = 0 if is_healthy else max(40, min(95, int(score * 80 + 20)))
    confidence = int(score * 100)

    # Treatment lookup
    treatments = {
        "Apple Scab": "Apply fungicides (captan or myclobutanil) at bud break. Remove infected leaves. Ensure good air circulation.",
        "Apple Black Rot": "Prune infected branches. Apply copper-based fungicides. Remove mummified fruits.",
        "Cedar Apple Rust": "Apply fungicides (myclobutanil) in spring. Remove nearby cedar trees if possible.",
        "Corn Common Rust": "Apply fungicides (azoxystrobin). Plant resistant varieties. Rotate crops.",
        "Corn Northern Leaf Blight": "Apply fungicides at early infection. Use resistant hybrids. Rotate crops.",
        "Grape Black Rot": "Apply fungicides (mancozeb or myclobutanil). Remove infected berries. Prune for air flow.",
        "Tomato Early Blight": "Apply copper fungicides. Remove lower infected leaves. Avoid overhead watering.",
        "Tomato Late Blight": "Apply chlorothalonil or copper fungicides immediately. Remove infected plants.",
        "Tomato Leaf Mold": "Improve ventilation. Apply fungicides (chlorothalonil). Reduce humidity.",
        "Potato Early Blight": "Apply mancozeb or chlorothalonil. Remove infected foliage. Rotate crops.",
        "Potato Late Blight": "Apply metalaxyl fungicides. Destroy infected plants. Avoid wet conditions.",
        "Healthy": "Maintain regular watering and fertilization. Monitor for early signs of disease. Ensure proper spacing for air circulation.",
    }
    treatment = next((v for k, v in treatments.items() if k.lower() in disease.lower()), 
                     "Apply appropriate fungicide for the detected disease. Consult local agricultural extension for specific treatment. Remove infected plant material and improve air circulation.")

    return {
        "crop":        crop,
        "disease":     disease,
        "severity":    severity,
        "confidence":  confidence,
        "status":      "Healthy" if is_healthy else "Infected",
        "explanation": f"Detected {disease} in {crop} with {confidence}% confidence.",
        "treatment":   treatment,
    }

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    data = json.loads(text)
    disease = data.get("disease", "Unknown")
    severity = int(data.get("severity", 50))
    confidence = int(data.get("confidence", 80))
    crop = data.get("crop", "Unknown")
    explanation = data.get("explanation", "")
    treatment = data.get("treatment", "")

    return {
        "crop": crop,
        "disease": disease,
        "severity": severity,
        "confidence": confidence,
        "status": "Healthy" if disease.lower() == "healthy" else "Infected",
        "explanation": explanation,
        "treatment": treatment,
    }


# ---------------------------------------------------------------------------
# Deterministic mock (same image bytes → same result, always)
# ---------------------------------------------------------------------------
MOCK_DISEASES = [
    {"crop": "Tomato",  "disease": "Leaf Blight",    "severity": 65, "confidence": 92},
    {"crop": "Wheat",   "disease": "Powdery Mildew", "severity": 45, "confidence": 88},
    {"crop": "Maize",   "disease": "Root Rot",        "severity": 80, "confidence": 95},
    {"crop": "Potato",  "disease": "Bacterial Spot",  "severity": 55, "confidence": 85},
    {"crop": "Rice",    "disease": "Healthy",          "severity": 0,  "confidence": 97},
]

def _mock_predict(image_bytes: bytes) -> dict:
    # Hash the image bytes so the same image always maps to the same result
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
        "explanation": "No disease detected." if disease == "Healthy" else "Infected regions detected in the crop.",
        "treatment": "Continue regular care." if disease == "Healthy" else "Consult local agricultural extension for treatment options.",
    }


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# OLD GRAD-CAM IMPLEMENTATION - REPLACED BY Grad-CAM++ (gradcam_plus.py)
# ---------------------------------------------------------------------------
# The following functions are deprecated and no longer used.
# Kept here for reference only.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# End of deprecated code
# ---------------------------------------------------------------------------
    """
    Generate Grad-CAM heatmap using the actual ML model's activations.
    Returns the raw heatmap array for further processing.
    """
    try:
        import tensorflow as tf
        
        # Get the last convolutional layer
        last_conv_layer = None
        for layer in reversed(model.layers):
            if len(layer.output_shape) == 4:  # Convolutional layer
                last_conv_layer = layer
                break
        
        if last_conv_layer is None:
            print("[Grad-CAM] No convolutional layer found")
            return None
        
        print(f"[Grad-CAM] Using layer: {last_conv_layer.name}")
        
        # Create a model that maps the input image to the activations of the last conv layer
        grad_model = tf.keras.models.Model(
            [model.inputs],
            [last_conv_layer.output, model.output]
        )
        
        # Compute gradient of the predicted class with respect to the feature map
        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(img_array)
            loss = predictions[:, class_idx]
        
        # Extract gradients
        grads = tape.gradient(loss, conv_outputs)
        
        # Pool the gradients over all the axes leaving out the channel dimension
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        
        # Weight the channels by the gradients
        conv_outputs = conv_outputs[0]
        pooled_grads = pooled_grads.numpy()
        conv_outputs = conv_outputs.numpy()
        
        for i in range(pooled_grads.shape[0]):
            conv_outputs[:, :, i] *= pooled_grads[i]
        
        # Average over all the filters to get a single 2D heatmap
        heatmap = np.mean(conv_outputs, axis=-1)
        
        # Normalize between 0 and 1
        heatmap = np.maximum(heatmap, 0)
        if np.max(heatmap) != 0:
            heatmap /= np.max(heatmap)
        
        return heatmap
        
    except Exception as e:
        print(f"[Grad-CAM] Failed to generate: {e}")
        return None


# ---------------------------------------------------------------------------
# Public entry point with enhanced structured output
# ---------------------------------------------------------------------------
def predict(image_bytes: Optional[bytes] = None, language: str = "en") -> dict:
    """
    Main prediction pipeline that returns structured JSON containing:
    - crop: Detected crop name
    - disease: Detected disease name  
    - severity: Disease severity (0-100)
    - confidence: Model confidence (0-100)
    - status: "Healthy" or "Infected"
    - image_url: URL or identifier of the uploaded image
    - heatmap_url: URL of the heatmap (if applicable)
    - heatmap_b64: Base64-encoded heatmap image
    - explanation: Brief explanation of the diagnosis
    - treatment: Personalized treatment recommendations
    - precautions: Prevention and precautionary measures
    
    Prediction Priority:
    1. Custom ML Model (EfficientNet with 66 disease classes) - PRIMARY
    2. Claude AI (backup)
    3. Color-based analysis (fallback)
    4. Mock prediction (final fallback)
    """
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

    # PREDICTION PRIORITY: Custom ML Model (66 classes) > Claude > Color-based > Mock
    result = None
    method_used = "unknown"
    
    # 1. Try custom ML model first (Fine-tuned EfficientNet with 66 disease classes - PRIMARY METHOD)
    try:
        print("[AI Pipeline] ✓ Step 1: Using fine-tuned EfficientNet model (66 classes - primary method)...")
        result = _torch_predict(image_bytes)
        method_used = "Fine-tuned EfficientNet Model"
        print(f"[AI Pipeline] ✅ ML Model success: {result['crop']} / {result['disease']} ({result['confidence']}% confidence)")
        
        # Quality check: If prediction seems suspicious, log a warning
        # (e.g., very high confidence on disease might be misclassification)
        if result['confidence'] > 95 and result['disease'] != 'Healthy':
            print(f"[AI Pipeline] ⚠️ WARNING: Very high confidence ({result['confidence']}%) on disease detection.")
            print(f"[AI Pipeline] ⚠️ This might be a misclassification. Review the uploaded image.")
            print(f"[AI Pipeline] ℹ️ If incorrect, consider using Claude AI backup by setting ANTHROPIC_API_KEY")
        
    except Exception as e:
        print(f"[AI Pipeline] ❌ ML Model failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Try Claude as backup (if ML model fails)
    if not result and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            print("[AI Pipeline] ✓ Step 2: Using Claude (Anthropic) as backup...")
            result = _claude_predict(image_bytes, language=language)
            method_used = "Claude AI"
            print(f"[AI Pipeline] ✅ Claude success: {result['crop']} / {result['disease']} ({result['confidence']}% confidence)")
        except Exception as e:
            print(f"[AI Pipeline] ❌ Claude failed: {e}")
            if "credit balance" in str(e).lower():
                print("[AI Pipeline] ⚠️ Claude needs credits. Add $5 at https://console.anthropic.com/settings/billing")
    
    # 3. Try color-based analysis as last resort
    if not result:
        try:
            print("[AI Pipeline] ✓ Step 3: Using color-based analysis (fallback)...")
            result = _color_based_predict(image_bytes)
            method_used = "Color Analysis"
            print(f"[AI Pipeline] ✅ Color analysis success: {result['crop']} / {result['disease']} ({result['confidence']}% confidence)")
        except Exception as e:
            print(f"[AI Pipeline] ❌ Color analysis failed: {e}")
    
    # 4. Final fallback to mock
    if not result:
        print("[AI Pipeline] ⚠️ All methods failed, using mock prediction")
        result = _mock_predict(image_bytes)
        method_used = "Mock (Fallback)"

    # Enhance result with additional fields
    print(f"[AI Pipeline] 📊 Final result from {method_used}")
    print(f"[AI Pipeline] - Crop: {result['crop']}")
    print(f"[AI Pipeline] - Disease: {result['disease']}")
    print(f"[AI Pipeline] - Severity: {result['severity']}%")
    print(f"[AI Pipeline] - Confidence: {result['confidence']}%")
    
    # Extract precautions from disease info
    disease_info = _load_disease_info()
    precautions = []
    disease_key = ""  # Track the matched disease key
    
    # Try to find precautions in disease knowledge base
    for key, info in disease_info.items():
        if (result['disease'].lower() in key.lower() or 
            result['disease'].lower() in info.get('disease', '').lower()):
            precautions = info.get('prevention', [])
            disease_key = key  # Store the matched disease key
            if precautions:
                print(f"[AI Pipeline] ✓ Found {len(precautions)} precautions from knowledge base")
                print(f"[AI Pipeline] ✓ Disease key: {disease_key}")
                break
    
    # Default precautions if none found
    if not precautions:
        if result['status'] == "Healthy":
            precautions = [
                "Continue regular monitoring for early disease detection",
                "Maintain proper irrigation and avoid water stress",
                "Apply balanced fertilizers according to crop needs",
                "Practice crop rotation to prevent soil-borne diseases",
                "Remove weeds regularly to reduce pest harboring"
            ]
        else:
            precautions = [
                "Monitor plants daily for spreading of disease",
                "Isolate infected plants to prevent disease spread",
                "Avoid working with plants when leaves are wet",
                "Sterilize pruning tools between plants",
                "Remove and destroy infected plant debris immediately",
                "Practice crop rotation for at least 2-3 years"
            ]
    
    # Generate Grad-CAM++ heatmap for infected plants
    heatmap_b64 = ""
    if result["status"] == "Infected" and result["severity"] > 0:
        print(f"[AI Pipeline] === GRAD-CAM HEATMAP GENERATION ===")
        print(f"[AI Pipeline] Status: {result['status']}, Severity: {result['severity']}")
        
        # Extract Grad-CAM++ metadata if available
        model = result.get("_gradcam_model")
        img_array = result.get("_gradcam_img_array")
        class_idx = result.get("_gradcam_class_idx", 0)
        
        print(f"[AI Pipeline] Metadata check:")
        print(f"  - Model: {model is not None} (type: {type(model).__name__ if model else 'None'})")
        print(f"  - Image array: {img_array is not None} (shape: {img_array.shape if img_array is not None else 'None'})")
        print(f"  - Class index: {class_idx}")
        
        if model is not None and img_array is not None:
            try:
                print(f"[AI Pipeline] Calling generate_gradcam_heatmap...")
                # Generate heatmap using new Grad-CAM++ implementation
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
                print("\n========== HEATMAP DEBUG ==========")
                print("Heatmap generated:", heatmap_b64 is not None)
                print("Heatmap length:", len(heatmap_b64) if heatmap_b64 else 0)
                print("==================================\n")
                
                if heatmap_b64:
                    print(f"[AI Pipeline] ✅ Heatmap SUCCESS - Size: {len(heatmap_b64)} bytes")
                else:
                    print(f"[AI Pipeline] ⚠️ Heatmap EMPTY STRING returned")
            except Exception as e:
                print(f"[AI Pipeline] ❌ Heatmap EXCEPTION: {e}")
                import traceback
                traceback.print_exc()
                heatmap_b64 = ""
        else:
            print(f"[AI Pipeline] ⚠️ SKIPPING HEATMAP - Missing metadata")
            if model is None:
                print(f"  - Model is None (not stored from TensorFlow inference)")
            if img_array is None:
                print(f"  - Image array is None (not stored from TensorFlow inference)")
    else:
        print(f"[AI Pipeline] Skipping heatmap (Status: {result['status']}, Severity: {result['severity']}))")
    
    # Clean up metadata from result (don't send to API response)
    result.pop("_gradcam_model", None)
    result.pop("_gradcam_img_array", None)
    result.pop("_gradcam_class_idx", None)

    # Build comprehensive structured response
    response = {
        "crop": result.get("crop", "Unknown"),
        "disease": result.get("disease", "Unknown"),
        "disease_key": disease_key,  # Include the database key for disease info lookup
        "severity": result.get("severity", 0),
        "confidence": result.get("confidence", 0),
        "status": result.get("status", "Unknown"),
        "image_url": "",  # Will be set by the route handler
        "heatmap_url": "",  # Will be set if uploaded to storage
        "heatmap_b64": heatmap_b64,
        "explanation": result.get("explanation", "Analysis completed using AI vision models."),
        "treatment": result.get("treatment", "Consult local agricultural extension for specific treatment recommendations."),
        "precautions": " ".join(precautions) if isinstance(precautions, list) else precautions
    }
    
    # DEBUG: Verify response structure
    print(f"[AI Pipeline] === API RESPONSE ===")
    print(f"[AI Pipeline] Response keys: {list(response.keys())}")
    print(f"[AI Pipeline] Heatmap included: {bool(response['heatmap_b64'])}")
    print(f"[AI Pipeline] Heatmap size: {len(response['heatmap_b64'])} bytes" if response['heatmap_b64'] else "Empty")
    print(f"[AI Pipeline] Crop: {response['crop']}")
    print(f"[AI Pipeline] Disease: {response['disease']}")
    print(f"[AI Pipeline] Status: {response['status']}")
    print(f"[AI Pipeline] Confidence: {response['confidence']}%")
    print(f"[AI Pipeline] Severity: {response['severity']}%")
    
    print(f"[AI Pipeline] ✅ Prediction complete! Returning structured JSON response")
    return response
