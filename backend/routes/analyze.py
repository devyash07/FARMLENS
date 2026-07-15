from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, Header
from typing import Optional
from utils.auth import get_current_user
from services.ai_service import predict
from services.storage_service import upload_image
from supabase_client import supabase

router = APIRouter()

# STRICT file type validation - Only JPG, JPEG, and PNG
ALLOWED_TYPES = {"image/jpeg", "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes

@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    language: str = Form("en"),  # Get language from form data
    authorization: Optional[str] = Header(None),  # Make auth optional
):
    # VALIDATION 1: Check if file was provided
    if not file:
        raise HTTPException(
            status_code=400, 
            detail="No file uploaded. Please select an image to ."
        )
    
    # VALIDATION 2: Check if file is empty (no content)
    file_bytes = await file.read()
    if not file_bytes or len(file_bytes) == 0:
        raise HTTPException(
            status_code=400, 
            detail="Uploaded file is empty (0 bytes). Please select a valid image file."
        )
    
    # VALIDATION 3: Check file size (must be under 10MB)
    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.2f}MB). Maximum allowed size is 10MB. Please compress or resize the image."
        )
    
    # VALIDATION 4: Check file type - STRICT validation for JPG/JPEG/PNG only
    file_type = file.content_type.lower() if file.content_type else ""
    file_name = file.filename.lower() if file.filename else ""
    file_extension = file_name[file_name.rfind('.'):] if '.' in file_name else ""
    
    # Reject anything that's not explicitly JPG, JPEG, or PNG
    is_valid_type = file_type in ALLOWED_TYPES
    is_valid_extension = file_extension in ALLOWED_EXTENSIONS
    
    if not is_valid_type and not is_valid_extension:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only JPG, JPEG, and PNG images are accepted. Your file: {file.filename} (type: {file_type})"
        )
    
    if file_extension and not is_valid_extension:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{file_extension}'. Only .jpg, .jpeg, and .png files are allowed."
        )
    
    # Try to get user_id from token if provided, otherwise use "anonymous"
    user_id = "anonymous"
    if authorization:
        try:
            from fastapi.security import HTTPAuthorizationCredentials
            from utils.auth import get_current_user
            # Parse the token manually
            token = authorization.replace("Bearer ", "")
            from jose import jwt
            from utils.auth import DEV_JWT_SECRET, SUPABASE_JWT_SECRET
            for secret in [DEV_JWT_SECRET, SUPABASE_JWT_SECRET]:
                if secret:
                    try:
                        payload = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
                        user_id = payload.get("sub", "anonymous")
                        break
                    except:
                        continue
        except:
            pass  # If token validation fails, just use anonymous
    
    print(f"[] ✅ Valid upload - User: {user_id}, Language: {language}, File: {file.filename}, Size: {file_size / 1024:.2f}KB")

    # Skip Supabase upload for now (RLS policy issue) - just use local analysis
    image_url = f"local://{file.filename}"

    # Run AI prediction with language parameter
    print(f"[] 🤖 Calling AI prediction pipeline with language: {language}")
    result = predict(file_bytes, language=language)
    
    # Add image URL to result
    result["image_url"] = image_url
    
    print(f"[] ✅ Prediction complete:")
    print(f"  - Crop: {result.get('crop', 'N/A')}")
    print(f"  - Disease: {result.get('disease', 'N/A')}")
    print(f"  - Severity: {result.get('severity', 0)}%")
    print(f"  - Confidence: {result.get('confidence', 0)}%")
    print(f"  - Heatmap: {'Generated' if result.get('heatmap_b64') else 'Not generated'}")

    # Skip saving to history table for now (can add later when Supabase is configured)
    # record = {
    #     "user_id":     user_id,
    #     "image_url":   image_url,
    #     "disease":     result["disease"],
    #     "severity":    result["severity"],
    #     "confidence":  result["confidence"],
    #     "status":      result["status"],
    #     "heatmap_url": result.get("heatmap_url", ""),
    # }
    # supabase.table("history").insert(record).execute()

    # Return comprehensive structured JSON
    return {
        "crop":        result.get("crop", "Unknown"),
        "disease":     result.get("disease", "Unknown"),
        "disease_key": result.get("disease_key", ""),  # Key for disease info lookup
        "severity":    result.get("severity", 0),
        "confidence":  result.get("confidence", 0),
        "status":      result.get("status", "Unknown"),
        "image_url":   result.get("image_url", image_url),
        "heatmap_url": result.get("heatmap_url", ""),
        "heatmap_b64": result.get("heatmap_b64", ""),
        "explanation": result.get("explanation", ""),
        "treatment":   result.get("treatment", ""),
        "precautions": result.get("precautions", "")
    }
