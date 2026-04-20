import os
import hashlib
import base64
import json
from typing import Optional
import numpy as np

# ---------------------------------------------------------------------------
# Local PyTorch MobileNetV2 model (runs without API calls)
# ---------------------------------------------------------------------------
_TORCH_MODEL = None
_CLASS_NAMES = None

def _load_torch_model():
    """Load the pre-trained MobileNetV2 model for plant disease detection"""
    global _TORCH_MODEL, _CLASS_NAMES
    if _TORCH_MODEL is not None:
        return _TORCH_MODEL, _CLASS_NAMES
    
    try:
        import torch
        from torchvision import models
        import torch.nn as nn
        
        model_path = "mobilenetv2_plant.pth"
        class_path = "class_names.json"
        
        if not os.path.exists(model_path):
            print(f"[AI] Model file not found at {model_path}")
            return None, None
        
        # Load class names
        with open(class_path, 'r') as f:
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
        
        _TORCH_MODEL = model
        print(f"[AI] PyTorch model loaded with {len(_CLASS_NAMES)} classes")
        return _TORCH_MODEL, _CLASS_NAMES
    except Exception as e:
        print(f"[AI] Failed to load PyTorch model: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def _torch_predict(image_bytes: bytes) -> dict:
    """Use local PyTorch MobileNetV2 model for prediction"""
    try:
        import torch
        from torchvision import transforms
        from PIL import Image
        import io
        
        model, class_names = _load_torch_model()
        if model is None or class_names is None:
            raise ValueError("Model not available")
        
        # Preprocess image (same as training)
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        x = transform(img).unsqueeze(0)
        
        # Predict
        with torch.no_grad():
            preds = model(x)
            probs = torch.softmax(preds, dim=1)[0]
            
            # Get top 5 predictions to check for confusion
            top5_probs, top5_indices = torch.topk(probs, min(5, len(probs)))
            
            confidence = float(top5_probs[0])
            index = top5_indices[0].item()
            
            # Log top predictions for debugging
            print(f"[AI] Top 5 predictions:")
            for i in range(min(5, len(top5_indices))):
                idx = top5_indices[i].item()
                prob = float(top5_probs[i])
                print(f"  {i+1}. {class_names[idx]} ({prob*100:.1f}%)")
            
            # Handle potato/tomato confusion
            # If top prediction is tomato but potato is in top 3 with similar confidence, check further
            top_label = class_names[index]
            if 'Tomato' in top_label and confidence < 0.70:  # Low confidence tomato
                # Check if potato is in top 3
                for i in range(min(3, len(top5_indices))):
                    idx = top5_indices[i].item()
                    prob = float(top5_probs[i])
                    label = class_names[idx]
                    if 'Potato' in label and prob > confidence * 0.7:  # Potato is close
                        print(f"[AI] Detected potato/tomato confusion. Switching to potato (was {confidence*100:.1f}%, potato is {prob*100:.1f}%)")
                        index = idx
                        confidence = prob
                        break
        
        # Parse label (format: "Crop___Disease")
        label = class_names[index]
        parts = label.split('___')
        crop = parts[0].replace('_', ' ').replace('(', '').replace(')', '').strip()
        disease_raw = parts[1].replace('_', ' ').strip() if len(parts) > 1 else "Unknown"
        
        is_healthy = 'healthy' in disease_raw.lower()
        disease = "Healthy" if is_healthy else disease_raw
        
        # Calculate severity based on confidence
        # Higher confidence in disease detection = higher severity
        severity = 0 if is_healthy else max(40, min(95, int(confidence * 80 + 20)))
        confidence_pct = min(99, int(confidence * 100))
        
        # Treatment recommendations
        treatments = {
            "scab": "Apply fungicides (captan or myclobutanil) at bud break. Remove infected leaves.",
            "black rot": "Prune infected branches. Apply copper-based fungicides. Remove mummified fruits.",
            "rust": "Apply fungicides (myclobutanil) in spring. Improve air circulation.",
            "blight": "Apply copper-based fungicides immediately. Remove infected leaves. Avoid overhead watering.",
            "mildew": "Apply sulfur or potassium bicarbonate. Improve ventilation. Reduce humidity.",
            "spot": "Apply chlorothalonil or copper fungicides. Remove infected foliage. Rotate crops.",
            "rot": "Improve drainage. Apply fungicides. Remove infected plant material.",
            "mold": "Improve ventilation. Apply fungicides. Reduce humidity.",
            "scorch": "Ensure adequate watering. Mulch to retain moisture. Avoid drought stress.",
            "mosaic": "Remove infected plants immediately. Control aphid vectors. Use resistant varieties.",
            "curl": "Remove infected leaves. Control whitefly vectors. Apply appropriate insecticides.",
            "mites": "Apply miticides. Increase humidity. Remove heavily infested leaves.",
            "greening": "Remove infected trees. Control psyllid vectors. No cure available.",
            "healthy": "Maintain regular watering and fertilization. Monitor for early signs of disease.",
        }
        treatment = next(
            (v for k, v in treatments.items() if k in disease.lower()),
            "Apply appropriate fungicide for the detected disease. Remove infected plant material. Consult local agricultural extension for specific treatment."
        )
        
        return {
            "crop": crop,
            "disease": disease,
            "severity": severity,
            "confidence": confidence_pct,
            "status": "Healthy" if is_healthy else "Infected",
            "explanation": f"Detected {disease} in {crop} with {confidence_pct}% confidence using deep learning model.",
            "treatment": treatment,
        }
    except Exception as e:
        print(f"[AI] PyTorch model prediction failed: {e}")
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
        
        # Select crop with highest score
        scores = {
            "Potato": potato_score,
            "Tomato": tomato_score,
            "Corn": corn_score,
            "Wheat": wheat_score,
            "Grape": grape_score,
            "Coffee": coffee_score,
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
# Heatmap generation (works without a real model — highlights high-contrast
# regions as a proxy for "areas of interest")
# ---------------------------------------------------------------------------
def generate_heatmap_b64(image_bytes: bytes, severity: int) -> str:
    """
    Returns a base64-encoded JPEG of the image with a disease heatmap overlay.
    Red/yellow = most infected regions, blue/green = least infected.
    Uses colour deviation from healthy green to detect diseased areas.
    """
    try:
        import cv2
        import numpy as np

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return ""

        h, w = img.shape[:2]

        # --- Disease detection via colour analysis ---
        # Convert to HSV — diseased areas (brown/yellow/dark) deviate from healthy green
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Healthy green mask (hue 35-85, decent saturation)
        healthy_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))

        # Disease score = inverse of healthy green presence
        disease_map = cv2.bitwise_not(healthy_mask).astype(np.float32) / 255.0

        # Also boost areas with brown/yellow tones (typical disease colours)
        brown_mask = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([35, 255, 200]))
        yellow_mask = cv2.inRange(hsv, np.array([20, 80, 100]), np.array([40, 255, 255]))
        disease_boost = (brown_mask.astype(np.float32) + yellow_mask.astype(np.float32)) / 255.0
        disease_map = np.clip(disease_map + disease_boost * 0.5, 0, 1)

        # Smooth the map for a natural look
        disease_map = cv2.GaussianBlur(disease_map, (21, 21), 0)
        disease_map = cv2.normalize(disease_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Apply JET colormap: blue=least infected → red=most infected
        heatmap_color = cv2.applyColorMap(disease_map, cv2.COLORMAP_JET)

        # Blend: stronger overlay where severity is higher
        alpha = 0.35 + (severity / 100.0) * 0.35  # range 0.35–0.70
        blended = cv2.addWeighted(img, 1.0 - alpha * 0.4, heatmap_color, alpha, 0)

        # Add a colour legend bar at the bottom with percentage markers
        bar_h = max(24, h // 15)  # Slightly taller for better visibility
        legend = np.zeros((bar_h, w, 3), dtype=np.uint8)
        
        # Create gradient bar
        for x in range(w):
            val = int(x / w * 255)
            color = cv2.applyColorMap(np.array([[val]], dtype=np.uint8), cv2.COLORMAP_JET)[0][0]
            legend[:, x] = color
        
        # Add labels with better visibility
        font = cv2.FONT_HERSHEY_SIMPLEX
        fs = max(0.35, bar_h / 50)
        thickness = max(1, int(bar_h / 20))
        
        # Add percentage markers
        markers = [
            (0, "0%", 4),
            (0.25, "25%", None),
            (0.5, "50%", None),
            (0.75, "75%", None),
            (1.0, "100%", w - 40)
        ]
        
        for pos, label, x_override in markers:
            x_pos = x_override if x_override is not None else int(w * pos) - 15
            # Add black outline for better readability
            cv2.putText(legend, label, (x_pos, bar_h - 6), font, fs, (0, 0, 0), thickness + 1, cv2.LINE_AA)
            cv2.putText(legend, label, (x_pos, bar_h - 6), font, fs, (255, 255, 255), thickness, cv2.LINE_AA)
        
        # Add descriptive labels at top of legend
        label_y = int(bar_h * 0.4)
        cv2.putText(legend, "Healthy", (4, label_y), font, fs * 0.8, (0, 0, 0), thickness + 1, cv2.LINE_AA)
        cv2.putText(legend, "Healthy", (4, label_y), font, fs * 0.8, (255, 255, 255), thickness, cv2.LINE_AA)
        
        cv2.putText(legend, "Infected", (w - 60, label_y), font, fs * 0.8, (0, 0, 0), thickness + 1, cv2.LINE_AA)
        cv2.putText(legend, "Infected", (w - 60, label_y), font, fs * 0.8, (255, 255, 255), thickness, cv2.LINE_AA)

        output = np.vstack([blended, legend])

        _, buf = cv2.imencode(".jpg", output, [cv2.IMWRITE_JPEG_QUALITY, 88])
        return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()
    except Exception as e:
        print(f"[Heatmap] generation failed: {e}")
        return ""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def predict(image_bytes: Optional[bytes] = None, language: str = "en") -> dict:
    if not image_bytes:
        return {
            "crop": "Unknown", "disease": "Unknown", "severity": 0,
            "confidence": 0, "status": "Unknown",
            "heatmap_b64": "", "explanation": "No image provided.", "treatment": "",
        }

    print(f"[AI] Predict called with language: {language}")  # Debug logging

    # PRIORITY: Gemini (most accurate) > PyTorch (limited classes) > Claude > Color-based
    result = None
    
    # Try Gemini first (most accurate when available)
    if os.environ.get("GEMINI_API_KEY"):
        try:
            print("[AI] Trying Gemini Vision API (primary method)...")
            print(f"[AI] Passing language to Gemini: {language}")
            result = _gemini_predict(image_bytes, language=language)
            print(f"[AI] Gemini result: {result['crop']} / {result['disease']} ({result['confidence']}% confidence)")
        except Exception as e:
            print(f"[AI] Gemini failed: {e}")
    
    # Try PyTorch if Gemini failed (local model, limited to 38 classes)
    if not result:
        try:
            print("[AI] Using PyTorch MobileNetV2 model for analysis...")
            result = _torch_predict(image_bytes)
            print(f"[AI] PyTorch result: {result['crop']} / {result['disease']} ({result['confidence']}% confidence)")
        except Exception as e:
            print(f"[AI] PyTorch model failed: {e}")
    
    # Try Claude if both failed
    if not result and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            print("[AI] Trying Claude (Anthropic) as backup...")
            result = _claude_predict(image_bytes, language=language)
            print(f"[AI] Claude result: {result['crop']} / {result['disease']} ({result['confidence']}% confidence)")
        except Exception as e:
            print(f"[AI] Claude failed: {e}")
            if "credit balance" in str(e).lower():
                print("[AI] Claude needs credits. Add $5 at https://console.anthropic.com/settings/billing")
    
    # Try color-based analysis as last resort
    if not result:
        try:
            print("[AI] Using fast color-based analysis as fallback...")
            result = _color_based_predict(image_bytes)
            print(f"[AI] Color result: {result['crop']} / {result['disease']} ({result['confidence']}% confidence)")
        except Exception as e:
            print(f"[AI] Color analysis failed: {e}")
    
    # Final fallback to mock
    if not result:
        print("[AI] All methods failed, using mock prediction")
        result = _mock_predict(image_bytes)

    heatmap_b64 = ""
    if result["status"] == "Infected":
        heatmap_b64 = generate_heatmap_b64(image_bytes, result["severity"])

    result["heatmap_b64"] = heatmap_b64
    result["heatmap_url"] = ""
    return result
