from fastapi import APIRouter, Depends
from utils.auth import get_current_user
from supabase_client import supabase

router = APIRouter()


@router.get("/history")
def get_history(user_id: str = Depends(get_current_user)):
    response = (
        supabase.table("history")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"history": response.data}
