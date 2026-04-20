import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

# Accept either Supabase JWT secret or our own dev secret
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
DEV_JWT_SECRET = "farmlens-dev-secret"

bearer_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    token = credentials.credentials

    # Try our dev secret first (frontend-generated tokens)
    for secret in [DEV_JWT_SECRET, SUPABASE_JWT_SECRET]:
        if not secret:
            continue
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
            user_id: str = payload.get("sub")
            if user_id:
                return user_id
        except JWTError:
            continue

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate token")
