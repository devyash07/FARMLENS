import uuid
from fastapi import HTTPException
from supabase_client import supabase

BUCKET = "images"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def upload_image(file_bytes: bytes, content_type: str, filename: str) -> str:
    """Upload image to Supabase Storage and return public URL."""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, WEBP allowed.")

    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    path = f"{uuid.uuid4()}.{ext}"

    supabase.storage.from_(BUCKET).upload(
        path,
        file_bytes,
        {"content-type": content_type},
    )

    public_url = supabase.storage.from_(BUCKET).get_public_url(path)
    return public_url
