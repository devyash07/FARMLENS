from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase_client import supabase

bearer_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    token = credentials.credentials
    
    try:
        # Ask the official Supabase client to verify the token for us
        response = supabase.auth.get_user(token)
        
        # If Supabase says it's good, return the user's ID!
        if response and response.user:
            return response.user.id
            
    except Exception as e:
        # If it fails, print the exact reason to the terminal
        print(f"\n[Auth Error] Supabase Verification Failed: {str(e)}\n")
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Could not validate token"
    )