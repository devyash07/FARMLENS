# FarmLens - Complete Project Architecture Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Backend Architecture](#backend-architecture)
5. [Frontend Architecture](#frontend-architecture)
6. [AI/ML Pipeline](#aiml-pipeline)
7. [Data Flow](#data-flow)
8. [Key Features](#key-features)
9. [API Endpoints](#api-endpoints)
10. [Configuration](#configuration)

---

## 1. Project Overview

**FarmLens** is an AI-powered agricultural disease detection platform that helps farmers identify crop diseases through image analysis. The system uses multiple AI models (Gemini Vision API, PyTorch MobileNetV2, Claude) to analyze plant images and provide:
- Crop identification
- Disease detection
- Severity assessment
- Treatment recommendations
- Multi-language support (12 languages including English and 11 Indian languages)

### Key Capabilities
- Real-time crop disease detection
- Heatmap visualization of infected areas
- Multi-language treatment recommendations
- Agricultural chatbot for farming queries
- User history tracking
- Feedback system

---

## 2. Technology Stack

### Frontend
- **Framework**: React 18.3 with TypeScript
- **Build Tool**: Vite 5.4
- **Routing**: React Router DOM 6.30
- **UI Library**: Radix UI + Tailwind CSS + shadcn/ui
- **State Management**: React Context API + TanStack Query
- **Styling**: Tailwind CSS with custom theme
- **Animations**: Framer Motion
- **Forms**: React Hook Form + Zod validation

### Backend
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn (ASGI server)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT (python-jose)
- **Image Processing**: OpenCV, Pillow
- **AI/ML**: 
  - Google Gemini Vision API
  - PyTorch + TorchVision (MobileNetV2)
  - Anthropic Claude API
  - Custom color-based analysis

### Development Tools
- **Package Manager**: npm (frontend), pip (backend)
- **Testing**: Vitest, Playwright
- **Linting**: ESLint
- **Type Checking**: TypeScript

---

## 3. Project Structure

```
seed-to-insight-ui/
├── backend/                      # Python FastAPI backend
│   ├── routes/                   # API route handlers
│   │   ├── analyze.py           # Image analysis endpoint
│   │   ├── chatbot.py           # AI chatbot endpoint
│   │   ├── feedback.py          # Feedback submission
│   │   └── history.py           # User history
│   ├── services/                # Business logic
│   │   ├── ai_service.py        # AI prediction models
│   │   └── storage_service.py   # Image storage
│   ├── utils/                   # Utilities
│   │   └── auth.py              # JWT authentication
│   ├── main.py                  # FastAPI app entry point
│   ├── supabase_client.py       # Supabase connection
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Environment variables
│   ├── mobilenetv2_plant.pth    # PyTorch model weights
│   └── class_names.json         # Model class labels (38 classes)
│
├── src/                         # React frontend
│   ├── components/              # Reusable components
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── landing/             # Landing page sections
│   │   ├── Navbar.tsx           # Navigation bar
│   │   ├── Footer.tsx           # Footer
│   │   └── Chatbot.tsx          # AI chatbot widget
│   ├── contexts/                # React contexts
│   │   ├── AuthContext.tsx      # Authentication state
│   │   ├── ThemeContext.tsx     # Dark/light theme
│   │   └── I18nContext.tsx      # Internationalization
│   ├── pages/                   # Page components
│   │   ├── Index.tsx            # Landing page
│   │   ├── Login.tsx            # Login/Register
│   │   ├── Result.tsx           # Analysis results
│   │   ├── Profile.tsx          # User profile
│   │   ├── Feedback.tsx         # Feedback form
│   │   ├── GuideDetail.tsx      # Crop guides
│   │   └── NotFound.tsx         # 404 page
│   ├── lib/                     # Utilities
│   │   └── utils.ts             # Helper functions
│   ├── App.tsx                  # Main app component
│   ├── main.tsx                 # React entry point
│   └── index.css                # Global styles
│
├── public/                      # Static assets
│   ├── logo.png
│   ├── hero images (language-specific)
│   └── social media icons
│
├── package.json                 # Frontend dependencies
├── vite.config.ts              # Vite configuration
├── tailwind.config.ts          # Tailwind configuration
├── tsconfig.json               # TypeScript configuration
└── README.md                   # Project documentation
```

---

## 4. Backend Architecture

### 4.1 Main Application (`backend/main.py`)

```python
FastAPI app with:
- CORS middleware (allows frontend origins)
- Route registration (analyze, history, feedback, chatbot)
- Environment variable loading
```

**Ports**: Backend runs on `http://localhost:8001`

### 4.2 Routes

#### **Analyze Route** (`backend/routes/analyze.py`)
- **Endpoint**: `POST /analyze`
- **Purpose**: Analyze uploaded plant images
- **Input**: 
  - `file`: Image file (JPEG/PNG/WEBP)
  - `language`: Language code (en, hi, bn, te, etc.)
  - `authorization`: Optional JWT token
- **Output**: 
  ```json
  {
    "crop": "Tomato",
    "disease": "Late Blight",
    "severity": 85,
    "confidence": 92,
    "status": "Infected",
    "explanation": "...",
    "treatment": "...",
    "heatmap_b64": "data:image/jpeg;base64,..."
  }
  ```

#### **Chatbot Route** (`backend/routes/chatbot.py`)
- **Endpoint**: `POST /api/chatbot/chat`
- **Purpose**: Agriculture-specific Q&A chatbot
- **Input**: 
  ```json
  {
    "message": "How to treat tomato blight?",
    "history": [...]
  }
  ```
- **Output**: 
  ```json
  {
    "response": "...",
    "is_agriculture_related": true
  }
  ```
- **Features**:
  - Uses Gemini Flash model
  - Filters non-agriculture questions
  - Maintains conversation context

#### **History Route** (`backend/routes/history.py`)
- **Endpoint**: `GET /history`
- **Purpose**: Fetch user's analysis history
- **Authentication**: Required (JWT)

#### **Feedback Route** (`backend/routes/feedback.py`)
- **Endpoint**: `POST /feedback`
- **Purpose**: Submit user feedback
- **Input**: name, email, message

### 4.3 AI Service (`backend/services/ai_service.py`)

This is the **core AI engine** with multiple prediction methods:

#### **Prediction Priority Chain**:
1. **Gemini Vision API** (Primary - Most Accurate)
2. **PyTorch MobileNetV2** (Fallback - Local Model)
3. **Claude API** (Backup - Requires Credits)
4. **Color-based Analysis** (Last Resort)

#### **Method 1: Gemini Vision API** (`_gemini_predict`)
```python
Models tried in order:
- gemini-flash-latest (fastest, most reliable)
- gemini-2.5-flash (good balance)
- gemini-pro-latest (most capable)

Features:
- Multi-language support
- Detailed disease identification
- Treatment recommendations
- 40-second timeout
- Automatic model fallback
```

#### **Method 2: PyTorch MobileNetV2** (`_torch_predict`)
```python
Local deep learning model:
- 38 classes from PlantVillage dataset
- No API calls needed
- Fast inference (~1-2 seconds)
- Limited to trained classes

Classes include:
- Apple (scab, black rot, rust, healthy)
- Corn (leaf spot, rust, blight, healthy)
- Grape (black rot, esca, leaf blight, healthy)
- Potato (early blight, late blight, healthy)
- Tomato (7 diseases + healthy)
- And more...
```

#### **Method 3: Claude API** (`_claude_predict`)
```python
Anthropic Claude 3.5 Sonnet:
- High accuracy
- Requires $5 minimum credits
- Multi-language support
- Detailed analysis
```

#### **Method 4: Color-based Analysis** (`_color_based_predict`)
```python
Computer vision fallback:
- HSV color space analysis
- Texture detection (Laplacian)
- Edge detection (Canny)
- Disease pattern recognition
- No ML model needed
- Less accurate but always available
```

#### **Heatmap Generation** (`generate_heatmap_b64`)
```python
Creates disease visualization:
- Detects healthy green vs diseased areas
- Applies JET colormap (blue=healthy, red=infected)
- Adds severity-based overlay
- Returns base64-encoded JPEG
```

### 4.4 Authentication (`backend/utils/auth.py`)
```python
JWT-based authentication:
- Token generation with HS256
- Token validation
- User ID extraction
- Optional authentication (for analyze endpoint)
```

### 4.5 Database (Supabase)
```python
Tables:
- users: User accounts
- history: Analysis records
- feedback: User feedback

Note: Currently using local storage on frontend
      for development (Supabase integration optional)
```

---

## 5. Frontend Architecture

### 5.1 Application Entry (`src/main.tsx` → `src/App.tsx`)

```typescript
App.tsx structure:
- QueryClientProvider (TanStack Query)
- ThemeProvider (Dark/Light mode)
- I18nProvider (Multi-language)
- AuthProvider (User authentication)
- BrowserRouter (Routing)
- Chatbot (Global AI assistant)
```

### 5.2 Routing (`src/App.tsx`)

```typescript
Routes:
/ → Index (Landing page)
/login → Login (Auth page)
/result → Result (Analysis results)
/profile → Profile (User profile)
/feedback → Feedback (Feedback form)
/guide/:type → GuideDetail (Crop guides)
* → NotFound (404 page)
```

### 5.3 Context Providers

#### **AuthContext** (`src/contexts/AuthContext.tsx`)
```typescript
Manages:
- User authentication state
- Login/Register/Logout
- JWT token generation (client-side)
- Analysis history (localStorage)
- Profile updates

Features:
- Persistent login (localStorage)
- JWT token with 7-day expiry
- History limit (50 records)
- Storage quota management
```

#### **ThemeContext** (`src/contexts/ThemeContext.tsx`)
```typescript
Manages:
- Dark/Light mode toggle
- System theme detection
- Theme persistence
```

#### **I18nContext** (`src/contexts/I18nContext.tsx`)
```typescript
Manages:
- Language selection (12 languages)
- Translations for UI text
- Language persistence

Supported languages:
- English (en)
- Hindi (hi)
- Bengali (bn)
- Telugu (te)
- Marathi (mr)
- Tamil (ta)
- Gujarati (gu)
- Kannada (kn)
- Punjabi (pa)
- Odia (or)
- Malayalam (ml)
```

### 5.4 Key Pages

#### **Index Page** (`src/pages/Index.tsx`)
```typescript
Landing page with:
- Hero section (language-specific images)
- Features section
- Upload section (drag & drop)
- Crop guide section
- Footer

Features:
- Image upload with preview
- Drag & drop support
- File validation (JPEG/PNG/WEBP, max 10MB)
- Chatbot trigger on scroll
```

#### **Result Page** (`src/pages/Result.tsx`)
```typescript
Analysis results display:
- Original image + heatmap
- Crop and disease info
- Severity and confidence meters
- Treatment recommendations
- Language switching (re-analyzes on change)

Features:
- Real-time language switching
- Heatmap color guide
- Analysis history saving
- Multiple image analysis
```

#### **Login Page** (`src/pages/Login.tsx`)
```typescript
Authentication:
- Login form
- Register form
- Form validation (Zod)
- JWT token generation
- Redirect to result page
```

#### **Profile Page** (`src/pages/Profile.tsx`)
```typescript
User profile:
- Profile information
- Analysis history
- Edit profile
- Logout
```

#### **GuideDetail Page** (`src/pages/GuideDetail.tsx`)
```typescript
Crop-specific guides:
- Planting guide
- Care instructions
- Disease prevention
- Harvest timing
- Chatbot integration
```

### 5.5 Components

#### **Chatbot** (`src/components/Chatbot.tsx`)
```typescript
AI assistant widget:
- Floating chat button
- Chat interface
- Message history
- Agriculture-specific responses
- Auto-popup on guide pages
```

#### **Navbar** (`src/components/Navbar.tsx`)
```typescript
Navigation bar:
- Logo and branding
- Navigation links
- Language selector
- Theme toggle
- User menu (when logged in)
```

#### **Landing Sections** (`src/components/landing/`)
- HeroSection: Main banner with CTA
- FeaturesSection: Feature cards
- UploadSection: Image upload interface
- CropGuideSection: Crop guide cards

---

## 6. AI/ML Pipeline

### 6.1 Image Analysis Flow

```
User uploads image
       ↓
Frontend validation (type, size)
       ↓
Send to /analyze endpoint
       ↓
Backend receives image + language
       ↓
Try Gemini Vision API
  ├─ Success → Return result
  └─ Fail → Try PyTorch model
       ├─ Success → Return result
       └─ Fail → Try Claude API
            ├─ Success → Return result
            └─ Fail → Color-based analysis
                 └─ Return result
       ↓
Generate heatmap (if infected)
       ↓
Return JSON response
       ↓
Frontend displays results
```

### 6.2 Gemini API Integration

```python
# Model selection (tries in order)
models = [
    "gemini-flash-latest",    # Primary
    "gemini-2.5-flash",       # Backup
    "gemini-pro-latest"       # Fallback
]

# Prompt structure
System prompt: Agricultural expert instructions
User prompt: Image + "Identify crop and disease"
Language instruction: "Translate treatment to {language}"

# Response format (JSON)
{
  "crop": "Tomato",
  "disease": "Late Blight",
  "severity": 85,
  "confidence": 92,
  "explanation": "...",
  "treatment": "Apply copper fungicides..."
}
```

### 6.3 PyTorch Model

```python
Architecture: MobileNetV2
Input size: 224x224 RGB
Classes: 38 (PlantVillage dataset)
Preprocessing:
  - Resize to 224x224
  - Normalize: mean=[0.485, 0.456, 0.406]
               std=[0.229, 0.224, 0.225]
Output: Softmax probabilities
```

### 6.4 Heatmap Generation

```python
Algorithm:
1. Convert image to HSV color space
2. Detect healthy green areas (H: 35-85)
3. Detect disease colors (brown, yellow, dark)
4. Create disease probability map
5. Apply Gaussian blur for smoothing
6. Apply JET colormap
7. Blend with original image
8. Add legend bar with percentage markers
9. Encode as base64 JPEG
```

---

## 7. Data Flow

### 7.1 Image Upload Flow

```
User (Browser)
    ↓ [Upload image]
Index.tsx
    ↓ [FormData with file + language]
POST /analyze
    ↓
analyze.py
    ↓ [image_bytes, language]
ai_service.predict()
    ↓ [Try Gemini → PyTorch → Claude → Color]
Return JSON
    ↓
Result.tsx
    ↓ [Display results]
User sees analysis
```

### 7.2 Language Switching Flow

```
User clicks language selector
    ↓
I18nContext updates language
    ↓
Result.tsx detects language change
    ↓
Re-analyze all images with new language
    ↓
Backend generates treatment in new language
    ↓
UI updates with translated text
```

### 7.3 Chatbot Flow

```
User types question
    ↓
Chatbot.tsx
    ↓ [POST /api/chatbot/chat]
chatbot.py
    ↓ [Check if agriculture-related]
    ├─ Yes → Call Gemini with context
    └─ No → Return polite decline
    ↓
Return response
    ↓
Display in chat interface
```

---

## 8. Key Features

### 8.1 Multi-Language Support
- **UI Translation**: 12 languages via I18nContext
- **Treatment Translation**: AI generates treatment in user's language
- **Real-time Switching**: Re-analyzes images when language changes

### 8.2 Multiple AI Models
- **Gemini**: Most accurate, cloud-based
- **PyTorch**: Fast, local, limited classes
- **Claude**: High quality, requires credits
- **Color-based**: Always available fallback

### 8.3 Disease Visualization
- **Heatmap**: Color-coded infected areas
- **Legend**: Blue (healthy) → Red (infected)
- **Severity Overlay**: Opacity based on severity

### 8.4 User Experience
- **Drag & Drop**: Easy image upload
- **Multiple Images**: Analyze multiple crops at once
- **History**: Track past analyses
- **Chatbot**: 24/7 agricultural advice

### 8.5 Authentication
- **JWT Tokens**: Secure authentication
- **Local Storage**: Persistent login
- **Optional Auth**: Can use without login

---

## 9. API Endpoints

### Backend API (Port 8001)

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/` | Health check | No |
| POST | `/analyze` | Analyze plant image | Optional |
| GET | `/history` | Get user history | Yes |
| POST | `/feedback` | Submit feedback | No |
| POST | `/api/chatbot/chat` | Chat with AI | No |
| GET | `/api/chatbot/health` | Chatbot health | No |

### Request/Response Examples

#### Analyze Image
```bash
POST /analyze
Content-Type: multipart/form-data

file: [image file]
language: "hi"
Authorization: Bearer [token] (optional)

Response:
{
  "crop": "टमाटर",
  "disease": "Late Blight",
  "severity": 85,
  "confidence": 92,
  "status": "Infected",
  "explanation": "...",
  "treatment": "तुरंत कॉपर-आधारित फंगीसाइड लगाएं...",
  "heatmap_b64": "data:image/jpeg;base64,..."
}
```

#### Chat with Bot
```bash
POST /api/chatbot/chat
Content-Type: application/json

{
  "message": "How to prevent tomato blight?",
  "history": []
}

Response:
{
  "response": "To prevent tomato blight: 1) Space plants 60-90cm apart...",
  "is_agriculture_related": true
}
```

---

## 10. Configuration

### 10.1 Environment Variables (`backend/.env`)

```bash
# Supabase (Database)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# AI APIs
GEMINI_API_KEY=AIzaSy...  # Google Gemini API
ANTHROPIC_API_KEY=sk-ant-...  # Claude API
HF_TOKEN=hf_...  # HuggingFace (optional)
```

### 10.2 Frontend Configuration

**Vite Config** (`vite.config.ts`):
```typescript
- Port: 8080
- Proxy: /api → http://localhost:8001
- Build output: dist/
```

**Tailwind Config** (`tailwind.config.ts`):
```typescript
- Custom colors
- Dark mode support
- Typography plugin
- Animations
```

### 10.3 Python Dependencies

```
fastapi - Web framework
uvicorn - ASGI server
supabase - Database client
python-multipart - File uploads
python-jose - JWT handling
opencv-python-headless - Image processing
torch, torchvision - Deep learning
google-generativeai - Gemini API
anthropic - Claude API
Pillow - Image manipulation
numpy - Numerical operations
```

### 10.4 Node Dependencies

```
react, react-dom - UI framework
react-router-dom - Routing
@tanstack/react-query - Data fetching
@radix-ui/* - UI components
tailwindcss - Styling
framer-motion - Animations
lucide-react - Icons
zod - Validation
```

---

## 11. Development Workflow

### 11.1 Starting the Application

**Backend**:
```bash
cd backend
source venv312/bin/activate  # Python 3.12 required for TensorFlow
python main.py
# Runs on http://localhost:8001
```

**Frontend**:
```bash
npm run dev
# Runs on http://localhost:8080
```

### 11.2 Testing

```bash
# Frontend tests
npm run test

# E2E tests
npx playwright test
```

### 11.3 Building for Production

```bash
# Frontend build
npm run build
# Output: dist/

# Backend deployment
# Use uvicorn with gunicorn for production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

---

## 12. Troubleshooting

### Common Issues

**1. Gemini API 404 Error**
- **Cause**: Model name changed
- **Fix**: Use `gemini-flash-latest` instead of `gemini-1.5-flash-latest`

**2. PyTorch Model Not Loading**
- **Cause**: Missing model file or wrong Python version
- **Fix**: Ensure `mobilenetv2_plant.pth` exists and use Python 3.12

**3. CORS Errors**
- **Cause**: Frontend origin not allowed
- **Fix**: Add origin to `allow_origins` in `backend/main.py`

**4. Storage Quota Exceeded**
- **Cause**: Too many images in localStorage
- **Fix**: System auto-trims to 20 records

**5. Claude API Credit Error**
- **Cause**: Insufficient credits
- **Fix**: Add $5 at https://console.anthropic.com/settings/billing

---

## 13. Future Enhancements

1. **Expand PyTorch Model**: Train on more crops (coffee, wheat, cucumber)
2. **Real-time Detection**: Video stream analysis
3. **Offline Mode**: Progressive Web App with service workers
4. **Weather Integration**: Location-based disease predictions
5. **Community Features**: Farmer forums and knowledge sharing
6. **Mobile Apps**: Native iOS/Android applications
7. **Drone Integration**: Aerial crop monitoring
8. **Blockchain**: Crop certification and traceability

---

## 14. Credits & License

**Developed by**: FarmLens Team
**AI Models**: Google Gemini, PyTorch MobileNetV2, Anthropic Claude
**Dataset**: PlantVillage (38 classes)
**UI Components**: shadcn/ui, Radix UI
**Icons**: Lucide React

---

**Last Updated**: April 2026
**Version**: 1.0.0
