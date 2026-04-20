from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from supabase_client import supabase

router = APIRouter()


class FeedbackRequest(BaseModel):
    name: str
    email: EmailStr
    message: str


@router.post("/feedback")
def submit_feedback(body: FeedbackRequest):
    supabase.table("feedback").insert({
        "name":    body.name,
        "email":   body.email,
        "message": body.message,
    }).execute()
    return {"message": "Feedback submitted successfully"}
