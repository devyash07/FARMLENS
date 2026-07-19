from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from utils.auth import get_current_user
from supabase_client import supabase
import traceback

router = APIRouter()

# Define the exact data structure we want to receive from the frontend
class HistoryRecord(BaseModel):
    crop: Optional[str] = None
    disease: str
    severity: int     # <-- Changed from float to int
    confidence: int   # <-- Changed from float to int
    image_url: Optional[str] = None
    heatmap_url: Optional[str] = None
    symptoms: Optional[List[str]] = []
    prevention: Optional[List[str]] = []
    treatment: Optional[List[str]] = []

@router.get("/history")
def get_history(user_id: str = Depends(get_current_user)):
    try:
        response = (
            supabase.table("history")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return {"history": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/history")
def add_history(record: HistoryRecord, user_id: str = Depends(get_current_user)):
    try:
        # Use .dict() which safely works across different Pydantic versions
        data = record.dict()
        data["user_id"] = user_id
        
        print(f"\n[Database] Attempting to insert: {data}\n")
        
        response = supabase.table("history").insert(data).execute()
            
        return {"message": "History saved successfully", "data": response.data[0] if response.data else {}}
        
    except Exception as e:
        # If it fails, print the exact python error to the terminal
        print("\n=== HISTORY SAVE ERROR ===")
        traceback.print_exc()
        print("==========================\n")
        raise HTTPException(status_code=500, detail="Internal Server Error: Check backend terminal")