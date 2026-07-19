from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import logging
import asyncio
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

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

# Initialize Sentry for error tracking
SENTRY_DSN = os.getenv("SENTRY_DSN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        integrations=[
            StarletteIntegration(transaction_style="url"),
            FastApiIntegration(transaction_style="url"),
        ],
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
        # Adjust this value in production (0.1 = 10% of requests)
        traces_sample_rate=0.1 if ENVIRONMENT == "production" else 1.0,
        # Set profiles_sample_rate to profile 10% of sampled transactions
        profiles_sample_rate=0.1 if ENVIRONMENT == "production" else 1.0,
        # Send default PII (email, username) with error events
        send_default_pii=False,  # Set to False in production for privacy
        # Attach stack traces to all messages
        attach_stacktrace=True,
    )
    logger.info(f"✅ Sentry initialized for {ENVIRONMENT} environment")
else:
    logger.warning("⚠️  Sentry DSN not configured - error tracking disabled")
    logger.warning("   Add SENTRY_DSN to .env for production error monitoring")

from routes.analyze import router as analyze_router
from routes.history import router as history_router
from routes.feedback import router as feedback_router
from routes.chatbot import router as chatbot_router
from routes.auth import router as auth_router
from routes.disease import router as disease_router

# Get environment (already loaded above)
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
    """
    Health check endpoint for monitoring services (UptimeRobot, Pingdom, etc.)
    
    Returns:
    - status: "healthy" if service is running
    - environment: current environment (development/production)
    - ml_model: AI model configuration and availability
    - pytorch_available: GPU availability status
    - backup_apis: External API configuration status
    - supabase_configured: Database connection status
    
    Usage with UptimeRobot:
    1. Go to https://uptimerobot.com
    2. Create "HTTP(s)" monitor
    3. URL: https://your-api-domain.com/health
    4. Keyword: "healthy" (checks if response contains this word)
    5. Interval: 5 minutes
    6. Alerts: Email/SMS/Slack
    """
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
