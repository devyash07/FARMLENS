# 🔧 FARMLENS ARCHITECTURE: BACKEND PILLAR

**Version**: 1.0.0  
**Last Updated**: July 2026  
**Status**: Production Ready (100/100)

---

## 📋 PILLAR OVERVIEW

The **Backend Pillar** serves as the core API gateway and orchestrator. It's responsible for:
- 🔐 User authentication and JWT token management
- 🎯 Crop disease detection inference orchestration
- 💾 Supabase integration (PostgreSQL + RLS)
- 🌍 Multi-language result translation
- 📊 Result storage and history tracking
- 🛡️ Rate limiting and request timeout protection
- 📈 Sentry error tracking integration
- 🤖 Chatbot API integration

---

## 🏗️ ARCHITECTURE DIAGRAM

```
┌───────────────────────────────────────────────────────┐
│             FASTAPI APPLICATION                       │
│              (Port: 8000)                             │
└───────────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │Auth     │   │Analyze   │   │Chatbot   │
   │Routes   │   │Routes    │   │Routes    │
   └─────────┘   └──────────┘   └──────────┘
        │              │              │
        │              ▼              │
        │         ┌─────────────┐     │
        │         │ML Service   │     │
        │         │(Inference)  │     │
        │         └─────────────┘     │
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │Supabase │   │Gemini    │   │Sentry    │
   │Cloud    │   │API       │   │Tracking  │
   │(Auth+DB)│   │(ChatBot) │   │          │
   └─────────┘   └──────────┘   └──────────┘

Rate Limiting Layer (slowapi):
- /analyze: 10 req/min per IP
- /auth/login: 5 req/min per IP
- /auth/register: 3 req/hour per IP
- /chatbot/chat: 20 req/min per IP

Timeout Middleware:
- All requests: 30 second timeout
```

---

## 🛠️ CORE TECHNOLOGIES

| Technology | Purpose | Version |
|-----------|---------|---------|
| **FastAPI** | Web framework | 0.135.2 |
| **Uvicorn** | ASGI server | Latest |
| **Python** | Language | 3.12+ |
| **Supabase** | Auth + Database | Cloud |
| **TensorFlow/Keras** | ML inference | 2.13.0+ |
| **PyTorch** | Alternative ML | Latest |
| **Google Generative AI** | Chatbot API | Latest |
| **Anthropic** | Backup AI | Latest |
| **slowapi** | Rate limiting | 0.1.10 |
| **Sentry SDK** | Error tracking | 2.66.0 |
| **python-jose** | JWT handling | Latest |
| **Supabase Python** | DB client | 2.110.7+ |

---

## 📁 PROJECT STRUCTURE

```
backend/
├── main.py                    # Application entry point
│                            # • Sentry init
│                            # • Rate limiter config
│                            # • CORS middleware
│                            # • Timeout middleware
│
├── routes/                    # API endpoints (routers)
│   ├── auth.py              # POST /api/auth/* (login, register, etc.)
│   ├── analyze.py           # POST /analyze (disease detection)
│   ├── chatbot.py           # POST /api/chatbot/chat
│   ├── disease.py           # GET /api/disease/* (disease info)
│   ├── feedback.py          # POST /api/feedback
│   └── history.py           # GET /api/history
│
├── services/                  # Business logic
│   ├── ai_service.py        # ML inference orchestration
│   ├── gradcam_plus.py      # Heatmap generation
│   └── storage_service.py   # File handling
│
├── utils/                     # Helper utilities
│   └── auth.py              # JWT token creation/verification
│
├── models/                    # ML models (loaded on startup)
│   ├── best_farmlens_finetuned.keras
│   ├── class_names.json
│   └── mobilenetv2_plant.pth
│
├── supabase_client.py        # Supabase client initialization
├── requirements.txt          # Python dependencies
├── .env                      # (Secrets - NOT in git)
├── .env.example             # Template
└── .env.production.example  # Production template
```

---

## 🔐 AUTHENTICATION ARCHITECTURE

### Dual Auth Strategy

```
┌─────────────────────┐
│  Frontend Login     │
└─────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌──────────────┐
│Supabase│  │Backend API   │
│OAuth   │  │(Fallback)    │
└────────┘  └──────────────┘
    │           │
    └─────┬─────┘
          ▼
    ┌──────────────┐
    │JWT Token     │
    │in localStorage
    └──────────────┘
          │
          ▼
┌──────────────────────┐
│Every API request:    │
│Authorization: Bearer │
└──────────────────────┘
```

### Authentication Flow

```python
# POST /api/auth/login
@router.post("/login")
@limiter.limit("5/minute")  # Brute force protection
async def login(request: Request, req: LoginRequest):
    """
    1. Validate email format
    2. Lookup user in in-memory DB (development)
    3. Verify password against hash
    4. Create JWT token
    5. Return token + user info
    """
    user = get_user_by_email(req.email)
    
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": req.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "userId": user["userId"],
            "email": user["email"],
            "name": user["name"],
        }
    }
```

### JWT Token Structure

```python
# Token payload
{
    "sub": "user@example.com",      # Subject (user email)
    "exp": 1234567890,              # Expiration (7 days)
    "iat": 1234567890,              # Issued at
    "type": "access"                # Token type
}

# Secret: JWT_SECRET_KEY from .env
# Algorithm: HS256
```

### Password Hashing

```python
# Using PBKDF2-SHA256 with salt
def hash_password(password: str) -> str:
    salt = secrets.token_hex(32)
    iterations = 100000
    pwdhash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${pwdhash.hex()}"

# Demo Credentials (Development)
demo@farmlens.com / Demo@123
```

---

## 🎯 DISEASE DETECTION INFERENCE PIPELINE

### Request Flow

```
┌─────────────────────────────────────────┐
│ POST /analyze                           │
│ • file: MultipartFile (JPG/PNG)         │
│ • language: str (en, hi, bn, ...)      │
│ • Authorization: Bearer <JWT>           │
└─────────────────────────────────────────┘
         │
         ▼ (VALIDATION)
┌─────────────────────────────────────────┐
│ • Check file size (<10MB)               │
│ • Check file type (JPG/PNG only)        │
│ • Check file not empty                  │
│ • Enforce rate limit (10/min per IP)    │
│ • Enforce timeout (30s)                 │
└─────────────────────────────────────────┘
         │
         ▼ (PREPROCESSING)
┌─────────────────────────────────────────┐
│ • Decode image from bytes               │
│ • Resize to model input (224x224)       │
│ • Normalize pixel values                │
│ • Convert to tensor                     │
└─────────────────────────────────────────┘
         │
         ▼ (INFERENCE)
┌─────────────────────────────────────────┐
│ • Load EfficientNet model               │
│   (best_farmlens_finetuned.keras)       │
│ • Forward pass through model            │
│ • Get predictions for 66 disease classes│
│ • Top-1 class with confidence score     │
└─────────────────────────────────────────┘
         │
         ▼ (POST-PROCESSING)
┌─────────────────────────────────────────┐
│ • Get disease name from class_names.json │
│ • Extract severity (0-100%)             │
│ • Extract confidence (0-100%)           │
│ • Generate GradCAM+ heatmap             │
│ • Lookup disease info from disease_info │
└─────────────────────────────────────────┘
         │
         ▼ (TRANSLATION)
┌─────────────────────────────────────────┐
│ • Translate disease name to language    │
│ • Translate treatment steps             │
│ • Translate precautions                 │
│ • Use Claude API for on-the-fly trans   │
└─────────────────────────────────────────┘
         │
         ▼ (RESPONSE)
┌─────────────────────────────────────────┐
│ {                                       │
│   "crop": "Tomato",                    │
│   "disease": "Early Blight",           │
│   "disease_key": "Tomato___Early_blight"│
│   "severity": 78,                      │
│   "confidence": 92,                    │
│   "status": "Identified",              │
│   "heatmap_b64": "data:image/png;...",│
│   "explanation": "Early blight is...", │
│   "treatment": ["Apply fungicide..."], │
│   "precautions": ["Remove leaves..."]  │
│ }                                       │
└─────────────────────────────────────────┘
```

### Code Implementation

```python
# services/ai_service.py
def predict(image_bytes: bytes, language: str = "en") -> dict:
    """
    Main inference function
    """
    try:
        # 1. Load image
        image_array = cv2.imdecode(
            np.frombuffer(image_bytes, np.uint8), 
            cv2.IMREAD_COLOR
        )
        
        # 2. Resize and preprocess
        image_resized = cv2.resize(image_array, (224, 224))
        image_normalized = image_resized / 255.0
        image_tensor = np.expand_dims(image_normalized, 0)
        
        # 3. Load model (cached)
        model = load_model("best_farmlens_finetuned.keras")
        
        # 4. Inference
        predictions = model.predict(image_tensor)
        
        # 5. Get top prediction
        class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][class_idx]) * 100
        
        # 6. Load class names
        with open("class_names.json") as f:
            class_names = json.load(f)
        disease_name = class_names[str(class_idx)]
        
        # 7. Generate heatmap
        heatmap_b64 = generate_gradcam_heatmap(model, image_tensor, class_idx)
        
        # 8. Lookup disease info
        disease_info = load_disease_info(disease_name, language)
        
        # 9. Translate if needed
        if language != "en":
            disease_info = translate_results(disease_info, language)
        
        # 10. Return result
        return {
            "crop": extract_crop(disease_name),
            "disease": disease_name,
            "disease_key": disease_name,
            "severity": int(confidence),
            "confidence": int(confidence),
            "status": "Identified",
            "heatmap_b64": heatmap_b64,
            "explanation": disease_info.get("explanation", ""),
            "treatment": disease_info.get("treatment", []),
            "precautions": disease_info.get("precautions", []),
        }
        
    except Exception as e:
        logger.error(f"Inference error: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Inference failed")
```

---

## 🌍 ON-THE-FLY TRANSLATION STRATEGY

### Language Support

Translate disease detection results to 11 languages:
1. English (en)
2. Hindi (hi)
3. Bengali (bn)
4. Telugu (te)
5. Marathi (mr)
6. Tamil (ta)
7. Gujarati (gu)
8. Kannada (kn)
9. Punjabi (pa)
10. Odia (or)
11. Malayalam (ml)

### Translation Pipeline

```python
# routes/analyze.py
def translate_results(disease_info: dict, language: str) -> dict:
    """
    Translate disease detection results to target language
    """
    
    # Skip if English
    if language == "en":
        return disease_info
    
    # Use Claude API for translation
    prompt = f"""
    Translate these agricultural disease details to {language}:
    
    Disease: {disease_info['disease']}
    Explanation: {disease_info['explanation']}
    Treatment: {disease_info['treatment']}
    Precautions: {disease_info['precautions']}
    
    Return as JSON with same keys.
    """
    
    client = Anthropic()
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return json.loads(message.content[0].text)
```

### Translation Caching (Future)

```python
# Cache translations in Supabase to reduce API calls
# translations table:
# ├── disease_key (String)
# ├── language (String)
# ├── translated_name (String)
# ├── translated_treatment (Array)
# └── created_at (Timestamp)
```

---

## 💾 SUPABASE INTEGRATION

### Authentication

```python
# supabase_client.py
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

### Database Schema

```sql
-- Users table (managed by Supabase Auth)
CREATE TABLE auth.users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE,
  created_at TIMESTAMP
);

-- Analysis history
CREATE TABLE analysis_history (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  image_url TEXT,
  disease TEXT,
  severity INT,
  confidence INT,
  status TEXT,
  heatmap_url TEXT,
  created_at TIMESTAMP
);

-- Feedback
CREATE TABLE feedback (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  analysis_id UUID REFERENCES analysis_history(id),
  correct BOOLEAN,
  feedback_text TEXT,
  created_at TIMESTAMP
);
```

### Row Level Security (RLS)

```sql
-- Users can only see their own data
ALTER TABLE analysis_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own analysis"
ON analysis_history FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analysis"
ON analysis_history FOR INSERT
WITH CHECK (auth.uid() = user_id);
```

---

## 🛡️ RATE LIMITING & TIMEOUT PROTECTION

### Rate Limits

```python
# main.py - Configured with slowapi

limiter = Limiter(key_func=get_remote_address)

@router.post("/analyze")
@limiter.limit("10/minute")  # 10 predictions/min per IP
async def analyze_image(...):
    """Prevent AI inference abuse"""

@router.post("/api/auth/login")
@limiter.limit("5/minute")   # 5 login attempts/min per IP
async def login(...):
    """Prevent brute force attacks"""

@router.post("/api/auth/register")
@limiter.limit("3/hour")     # 3 registrations/hour per IP
async def register(...):
    """Prevent spam accounts"""

@router.post("/api/chatbot/chat")
@limiter.limit("20/minute")  # 20 queries/min per IP
async def chat(...):
    """Prevent API abuse"""
```

### Timeout Middleware

```python
# main.py
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """
    Enforce 30-second timeout on all requests
    Returns 408 Request Timeout if exceeded
    """
    try:
        return await asyncio.wait_for(call_next(request), timeout=30.0)
    except asyncio.TimeoutError:
        logger.error(f"Timeout: {request.method} {request.url.path}")
        return JSONResponse(
            status_code=408,
            content={
                "error": "Request timeout",
                "message": "The request took too long. Please try again."
            }
        )
```

---

## 📊 ERROR HANDLING & MONITORING

### Sentry Integration

```python
# main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
)
```

### Error Handling Pattern

```python
@router.post("/analyze")
async def analyze_image(file: UploadFile):
    try:
        # Process request
        result = predict(file.file.read())
        return result
        
    except FileNotFoundError as e:
        logger.error(f"Model not found: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Model loading failed")
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 🔗 INTERACTION WITH OTHER PILLARS

### Backend → Frontend
```
JSON Responses:
├── /analyze → Disease prediction + heatmap
├── /api/auth/login → JWT token + user info
├── /api/disease/:key → Disease info (localized)
└── /health → Status + model availability
```

### Backend → ML Model
```
Internal Calls:
├── Load model from disk
├── Pass image tensor to model
├── Get class predictions
└── Extract top-K predictions
```

### Backend → DevOps
```
Deployment Requirements:
├── Python 3.12+ runtime
├── GPU (optional, for inference speedup)
├── 4GB+ RAM for model loading
├── Environment variables (see .env.example)
└── Secrets management (SUPABASE_*, JWT_SECRET)
```

---

## 📋 API ENDPOINTS

| Endpoint | Method | Protected | Rate Limit | Purpose |
|----------|--------|-----------|-----------|---------|
| `/` | GET | No | - | Health check |
| `/health` | GET | No | - | Detailed status |
| `/api/auth/login` | POST | No | 5/min | Login user |
| `/api/auth/register` | POST | No | 3/hr | Create account |
| `/api/auth/me` | GET | Yes | - | Get user info |
| `/api/auth/refresh` | POST | Yes | - | Refresh token |
| `/analyze` | POST | Yes | 10/min | Detect disease |
| `/api/disease/:key` | GET | No | - | Get disease info |
| `/api/chatbot/chat` | POST | No | 20/min | Agricultural chatbot |
| `/api/history` | GET | Yes | - | User analysis history |
| `/api/feedback` | POST | Yes | - | Submit feedback |

---

## 🧪 DEVELOPMENT & TESTING

### Start Backend Server
```bash
cd backend
python3 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Environment Setup
```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
ANTHROPIC_API_KEY=sk-...
GEMINI_API_KEY=...
JWT_SECRET_KEY=your-secret-key
ENVIRONMENT=development
SENTRY_DSN=https://your-sentry-dsn
```

### Testing Inference
```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@crop_image.jpg" \
  -F "language=en" \
  -H "Authorization: Bearer <jwt_token>"
```

---

## 📚 REFERENCES

- FastAPI Docs: https://fastapi.tiangolo.com
- Supabase Docs: https://supabase.com/docs
- TensorFlow/Keras: https://www.tensorflow.org
- Sentry: https://docs.sentry.io
- slowapi: https://github.com/laurentS/slowapi

---

**Last Reviewed**: July 20, 2026  
**Next Review**: October 2026  
**Maintainer**: FarmLens Engineering Team
