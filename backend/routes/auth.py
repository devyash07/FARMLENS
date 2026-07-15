"""
Authentication routes for FarmLens
Handles user registration, login, token refresh, and password management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import re
import hashlib
import secrets
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
bearer_scheme = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "farmlens-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# In-memory user storage (for development - replace with database in production)
# Format: {email: {password_hash, name, created_at, ...}}
USERS_DB = {}

# Validation patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PASSWORD_MIN_LENGTH = 6


# ============================================================================
# Request/Response Models
# ============================================================================

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    email: str
    name: str
    userId: str
    created_at: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=PASSWORD_MIN_LENGTH)

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def validate_email(email: str) -> bool:
    """Validate email format"""
    return bool(EMAIL_PATTERN.match(email))

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
    
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, ""

def hash_password(password: str) -> str:
    """
    Hash password using PBKDF2-SHA256 with salt
    Format: algorithm$iterations$salt$hash
    """
    salt = secrets.token_hex(32)
    iterations = 100000
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${pwdhash.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        algorithm, iterations, salt, pwdhash = hashed_password.split('$')
        if algorithm != 'pbkdf2_sha256':
            return False
        iterations = int(iterations)
        test_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), iterations)
        return test_hash.hex() == pwdhash
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """
    Dependency to get current authenticated user email from JWT token
    Raises HTTPException if token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user still exists
        if email not in USERS_DB:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return email
        
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user data by email"""
    return USERS_DB.get(email)


# ============================================================================
# Initialize Demo User
# ============================================================================

def _init_demo_user():
    """Initialize demo user for testing"""
    demo_email = "demo@farmlens.com"
    demo_password = "Demo@123"  # Password with letter and number
    demo_name = "Demo User"
    
    if demo_email not in USERS_DB:
        hashed = hash_password(demo_password)
        USERS_DB[demo_email] = {
            "userId": "user_demo_001",
            "email": demo_email,
            "name": demo_name,
            "password_hash": hashed,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"✅ Demo user created: {demo_email} / {demo_password}")

# Initialize demo user on startup
_init_demo_user()


# ============================================================================
# Authentication Routes
# ============================================================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """
    Register a new user
    
    Requirements:
    - Email must be valid and unique
    - Password must be at least 6 characters with letter and number
    - Name must be 2-100 characters
    """
    email = req.email.lower().strip()
    
    # Validate email format
    if not validate_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Check if user already exists
    if email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password(req.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create user
    user_id = f"user_{len(USERS_DB) + 1}_{datetime.utcnow().timestamp()}"
    hashed_password = hash_password(req.password)
    
    USERS_DB[email] = {
        "userId": user_id,
        "email": email,
        "name": req.name.strip(),
        "password_hash": hashed_password,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    # Create access token
    access_token = create_access_token(data={"sub": email})
    
    # Return token and user info (without password)
    user_data = {
        "userId": user_id,
        "email": email,
        "name": req.name.strip(),
    }
    
    logger.info(f"New user registered: {email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """
    Authenticate user and return JWT token
    
    Validates credentials and returns access token if successful
    """
    email = req.email.lower().strip()
    
    # Get user
    user = get_user_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(req.password, user["password_hash"]):
        logger.warning(f"Failed login attempt for: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": email})
    
    # Return token and user info (without password)
    user_data = {
        "userId": user["userId"],
        "email": user["email"],
        "name": user["name"],
    }
    
    logger.info(f"User logged in: {email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(email: str = Depends(get_current_user_email)):
    """
    Get current authenticated user information
    
    Requires valid JWT token in Authorization header
    """
    user = get_user_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "userId": user["userId"],
        "email": user["email"],
        "name": user["name"],
        "created_at": user.get("created_at"),
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(email: str = Depends(get_current_user_email)):
    """
    Refresh access token
    
    Generates a new token for authenticated user
    """
    user = get_user_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": email})
    
    user_data = {
        "userId": user["userId"],
        "email": user["email"],
        "name": user["name"],
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    email: str = Depends(get_current_user_email)
):
    """
    Change user password
    
    Requires current password verification
    """
    user = get_user_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(req.current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    is_valid, error_msg = validate_password(req.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    user["password_hash"] = hash_password(req.new_password)
    user["updated_at"] = datetime.utcnow().isoformat()
    
    logger.info(f"Password changed for user: {email}")
    
    return {"message": "Password changed successfully"}


@router.put("/profile")
async def update_profile(
    req: UpdateProfileRequest,
    email: str = Depends(get_current_user_email)
):
    """
    Update user profile
    
    Can update name and phone number
    """
    user = get_user_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if req.name:
        user["name"] = req.name.strip()
    
    if req.phone is not None:
        user["phone"] = req.phone.strip() if req.phone else None
    
    user["updated_at"] = datetime.utcnow().isoformat()
    
    logger.info(f"Profile updated for user: {email}")
    
    return {
        "userId": user["userId"],
        "email": user["email"],
        "name": user["name"],
        "phone": user.get("phone"),
    }


@router.post("/logout")
async def logout(email: str = Depends(get_current_user_email)):
    """
    Logout user (client should clear token)
    
    Note: With JWT, actual logout is handled client-side by clearing the token
    This endpoint exists for logging purposes and future token blacklist implementation
    """
    logger.info(f"User logged out: {email}")
    
    return {"message": "Logged out successfully"}


# ============================================================================
# Admin/Debug Routes (Remove in production)
# ============================================================================

@router.get("/debug/users", include_in_schema=False)
async def debug_list_users():
    """Debug endpoint to list all users (REMOVE IN PRODUCTION)"""
    users = []
    for email, user_data in USERS_DB.items():
        users.append({
            "email": email,
            "name": user_data["name"],
            "userId": user_data["userId"],
            "created_at": user_data.get("created_at"),
        })
    return {"users": users, "count": len(users)}
