from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import logging
import asyncio

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.getenv("DEBUG", "false").lower() == "true" else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from routes.analyze import router as analyze_router
from routes.history import router as history_router
from routes.feedback import router as feedback_router
from routes.chatbot import router as chatbot_router
from routes.auth import router as auth_router
from routes.disease import router as disease_router

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
logger.info(f"Starting FarmLens API in {ENVIRONMENT} mode")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Get allowed origins from environment variable
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:8080,http://localhost:8081,http://localhost:3000"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

# Add wildcard for development mode
if ENVIRONMENT == "development":
    logger.warning("Development mode: CORS allows all localhost origins")
    allowed_origins.extend(["http://localhost:*", "http://127.0.0.1:*"])

logger.info(f"CORS allowed origins: {allowed_origins}")

app = FastAPI(
    title="FarmLens API",
    version="1.0.0",
    description="AI-Powered Crop Disease Detection API"
)

# Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Timeout middleware - prevents requests from hanging indefinitely
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Add 30-second timeout to all requests"""
    try:
        return await asyncio.wait_for(call_next(request), timeout=30.0)
    except asyncio.TimeoutError:
        logger.error(f"Request timeout: {request.method} {request.url.path}")
        return JSONResponse(
            status_code=408,
            content={
                "error": "Request timeout",
                "message": "The request took too long to process. Please try again."
            }
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(analyze_router)
app.include_router(history_router)
app.include_router(feedback_router)
app.include_router(chatbot_router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(disease_router, prefix="/api/disease", tags=["disease-info"])


@app.get("/")
def root():
    return {
        "status": "FarmLens API is running",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "endpoints": {
            "analyze": "/analyze",
            "history": "/history",
            "feedback": "/feedback",
            "chatbot": "/api/chatbot/chat",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    import torch
    
    # Check if ML model files exist
    finetuned_model_exists = os.path.exists("best_farmlens_finetuned.keras")
    legacy_model_exists = os.path.exists("farmlens_efficientnet.keras")
    
    # Check TensorFlow availability
    tensorflow_available = False
    try:
        import tensorflow as tf
        tensorflow_available = True
    except ImportError:
        pass
    
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "ml_model": {
            "primary_method": "Fine-tuned EfficientNet (66 classes)",
            "finetuned_model_exists": finetuned_model_exists,
            "legacy_model_exists": legacy_model_exists,
            "active_model": "best_farmlens_finetuned.keras" if finetuned_model_exists else "farmlens_efficientnet.keras",
            "tensorflow_available": tensorflow_available
        },
        "pytorch_available": torch.cuda.is_available() if hasattr(torch, 'cuda') else False,
        "backup_apis": {
            "claude_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))  # deprecated
        },
        "supabase_configured": bool(os.getenv("SUPABASE_URL"))
    }
