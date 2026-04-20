from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, Header
from typing import Optional
from utils.auth import get_current_user
from services.ai_service import predict
from services.storage_service import upload_image
from supabase_client import supabase

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    language: str = Form("en"),  # Get language from form data
    authorization: Optional[str] = Header(None),  # Make auth optional
):
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
    
    print(f"[Analyze] User: {user_id}, Language: {language}")
    
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Use JPG, PNG, or WEBP.")

    print(f"[Analyze] Received language parameter: {language}")  # Debug logging

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Skip Supabase upload for now (RLS policy issue) - just use local analysis
    image_url = f"local://{file.filename}"

    # Run AI prediction with language parameter
    print(f"[Analyze] Calling predict with language: {language}")
    result = predict(file_bytes, language=language)

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

    return {
        "crop":        result.get("crop", "Unknown"),
        "disease":     result["disease"],
        "severity":    result["severity"],
        "confidence":  result["confidence"],
        "status":      result["status"],
        "image_url":   image_url,
        "heatmap_url": result.get("heatmap_url", ""),
        "heatmap_b64": result.get("heatmap_b64", ""),
        "explanation": result.get("explanation", ""),
        "treatment":   result.get("treatment", ""),
    }
