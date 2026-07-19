# 🌾 FarmLens - AI-Powered Crop Disease Detection

<div align="center">

![FarmLens Logo](public/logo.png)

**Empowering farmers with AI-driven crop disease detection and treatment recommendations**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Latest-ee4c2c.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Live Demo](#) | [Documentation](PROJECT_ARCHITECTURE.md) | [ML Model Docs](ML_MODEL_DOCUMENTATION.md) | [Deployment Guide](DEPLOYMENT_GUIDE.md)

</div>

---

## 📖 Overview

FarmLens is a comprehensive agricultural technology platform that uses advanced AI and machine learning to help farmers identify crop diseases quickly and accurately. Simply upload a photo of your plant, and our AI will:

- 🔍 **Identify the crop** with high accuracy
- 🦠 **Detect diseases** using multiple AI models
- 📊 **Assess severity** with visual heatmaps
- 💊 **Recommend treatments** in your language
- 🌍 **Support 12 languages** including 11 Indian languages

---

## ✨ Key Features

### 🤖 Multi-AI Detection System
- **Google Gemini Vision API** - Primary detection (95%+ accuracy)
- **PyTorch MobileNetV2** - Offline fallback (38 disease classes)
- **Anthropic Claude** - Backup AI model
- **Color-based Analysis** - Always-available fallback

### 🌐 Multi-Language Support
Supports **12 languages**:
- English, Hindi, Bengali, Telugu, Marathi, Tamil
- Gujarati, Kannada, Punjabi, Odia, Malayalam

### 📊 Visual Disease Analysis
- **Heatmap Generation** - Color-coded infected areas
- **Severity Assessment** - Percentage-based severity scores
- **Confidence Metrics** - AI confidence levels

### 💬 Agricultural Chatbot
- 24/7 AI-powered farming assistant
- Context-aware responses
- Agriculture-specific knowledge base

### 📱 User-Friendly Interface
- Drag & drop image upload
- Real-time language switching
- Dark/Light theme support
- Mobile-responsive design
- Analysis history tracking

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+** (for TensorFlow support)
- **Node.js 18+** and npm
- **Git**

### 1. Clone Repository
```bash
git clone https://github.com/devyash07/seed-to-insight-ui.git
cd seed-to-insight-ui
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment (Python 3.12)
python3.12 -m venv venv312
source venv312/bin/activate  # On Windows: venv312\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys:
# - GEMINI_API_KEY (required)
# - SUPABASE_URL, SUPABASE_ANON_KEY (optional)
# - ANTHROPIC_API_KEY (optional)

# Start backend server
python main.py
# Backend runs on http://localhost:8001
```

### 3. Frontend Setup
```bash
# In a new terminal, from project root
npm install

# Start development server
npm run dev
# Frontend runs on http://localhost:8080
```

### 4. Access Application
Open your browser and navigate to:
```
http://localhost:8080
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) | Complete technical architecture, API docs, data flow |
| [ML_MODEL_DOCUMENTATION.md](ML_MODEL_DOCUMENTATION.md) | ML model training, testing, and evaluation details |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production deployment guide and troubleshooting |

---

## 🏗️ Project Structure

```
seed-to-insight-ui/
├── backend/                    # Python FastAPI backend
│   ├── routes/                # API endpoints
│   │   ├── analyze.py        # Image analysis
│   │   ├── chatbot.py        # AI chatbot
│   │   ├── feedback.py       # User feedback
│   │   └── history.py        # Analysis history
│   ├── services/             # Business logic
│   │   ├── ai_service.py     # AI prediction engine
│   │   └── storage_service.py # Image storage
│   ├── utils/                # Utilities
│   │   └── auth.py           # JWT authentication
│   ├── main.py               # FastAPI app
│   ├── mobilenetv2_plant.pth # PyTorch model (8.9MB)
│   ├── class_names.json      # 38 disease classes
│   └── requirements.txt      # Python dependencies
│
├── src/                       # React frontend
│   ├── components/           # UI components
│   │   ├── ui/              # shadcn/ui components
│   │   ├── landing/         # Landing page sections
│   │   ├── Navbar.tsx       # Navigation
│   │   ├── Footer.tsx       # Footer
│   │   └── Chatbot.tsx      # AI chatbot widget
│   ├── contexts/            # React contexts
│   │   ├── AuthContext.tsx  # Authentication
│   │   ├── ThemeContext.tsx # Theme management
│   │   └── I18nContext.tsx  # Internationalization
│   ├── pages/               # Page components
│   │   ├── Index.tsx        # Landing page
│   │   ├── Login.tsx        # Authentication
│   │   ├── Result.tsx       # Analysis results
│   │   ├── Profile.tsx      # User profile
│   │   └── Feedback.tsx     # Feedback form
│   └── lib/                 # Utilities
│
├── public/                   # Static assets
├── PROJECT_ARCHITECTURE.md   # Technical documentation
├── ML_MODEL_DOCUMENTATION.md # ML model docs
├── DEPLOYMENT_GUIDE.md       # Deployment guide
└── package.json             # Node dependencies
```

---

## 🔧 Technology Stack

### Frontend
- **React 18.3** with TypeScript
- **Vite** - Build tool
- **Tailwind CSS** + **shadcn/ui** - Styling
- **React Router** - Navigation
- **TanStack Query** - Data fetching
- **Framer Motion** - Animations

### Backend
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **PyTorch** - Deep learning
- **OpenCV** - Image processing
- **Supabase** - Database (optional)

### AI/ML
- **Google Gemini Vision API** - Primary AI
- **PyTorch MobileNetV2** - Local ML model
- **Anthropic Claude** - Backup AI
- **PlantVillage Dataset** - Training data (38 classes)

---

## 🎯 How It Works

### 1. Image Upload
User uploads a plant image through the web interface

### 2. AI Analysis Pipeline
```
Gemini Vision API (Primary)
    ↓ (if fails)
PyTorch MobileNetV2 (Fallback)
    ↓ (if fails)
Claude API (Backup)
    ↓ (if fails)
Color-based Analysis (Last Resort)
```

### 3. Disease Detection
AI identifies:
- Crop type (e.g., Tomato, Potato, Corn)
- Disease name (e.g., Late Blight, Rust)
- Severity percentage (0-100%)
- Confidence score (0-100%)

### 4. Heatmap Generation
Visual representation showing:
- Healthy areas (blue/green)
- Infected areas (yellow/red)
- Severity overlay

### 5. Treatment Recommendations
AI generates treatment advice in user's selected language:
- Immediate actions
- Fungicide/pesticide recommendations
- Prevention measures
- Follow-up care

---

## 🌱 Supported Crops & Diseases

### Crops (14)
Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, Tomato

### Disease Categories (38 total)
- **Fungal**: Rust, Blight, Mildew, Mold, Scab, Rot
- **Bacterial**: Bacterial Spot
- **Viral**: Mosaic Virus, Leaf Curl
- **Pests**: Spider Mites
- **Healthy**: Healthy plant states

*See [ML_MODEL_DOCUMENTATION.md](ML_MODEL_DOCUMENTATION.md) for complete list*

---

## 🔑 API Keys Setup

### Required
- **GEMINI_API_KEY** - Get from [Google AI Studio](https://ai.google.dev/)
  - Free tier: 1,500 requests/day
  - Required for chatbot and primary disease detection

### Optional
- **SUPABASE_URL** & **SUPABASE_ANON_KEY** - Get from [Supabase](https://supabase.com/)
  - For user authentication and history storage
  - App works without it (uses localStorage)

- **ANTHROPIC_API_KEY** - Get from [Anthropic](https://console.anthropic.com/)
  - Backup AI model
  - Requires $5 minimum credit

---

## 📊 Performance

### Accuracy
- **Gemini Vision API**: 95%+ accuracy
- **PyTorch Model**: 85-95% accuracy (on trained classes)
- **Overall System**: 90%+ accuracy

### Speed
- **Gemini API**: 2-5 seconds per image
- **PyTorch Model**: 50-100ms per image (CPU)
- **Heatmap Generation**: 200-500ms

### Supported Image Formats
- JPEG, PNG, WEBP
- Max size: 10MB (auto-compressed to ~400KB)
- Recommended: 224×224 to 1024×1024 pixels

---

## 🧪 Testing

### Run Frontend Tests
```bash
npm run test
```

### Run E2E Tests
```bash
npx playwright test
```

### Test ML Model
```bash
cd backend
python test_model.py
```

---

## 🚀 Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

### Quick Deploy Options

#### Option 1: Vercel (Frontend) + Railway (Backend)
```bash
# Frontend
vercel deploy

# Backend
railway up
```

#### Option 2: Docker
```bash
# Build and run
docker-compose up
```

#### Option 3: Manual
- Frontend: Build with `npm run build`, deploy `dist/` folder
- Backend: Run with `uvicorn main:app --host 0.0.0.0 --port 8001`

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **PlantVillage Dataset** - Training data for ML model
- **Google Gemini** - Primary AI vision model
- **PyTorch** - Deep learning framework
- **shadcn/ui** - UI component library
- **FastAPI** - Backend framework

---

## 📧 Contact & Support

- **GitHub**: [@devyash07](https://github.com/devyash07)
- **Repository**: [seed-to-insight-ui](https://github.com/devyash07/seed-to-insight-ui)
- **Issues**: [Report a bug](https://github.com/devyash07/seed-to-insight-ui/issues)

---

## 🗺️ Roadmap

- [ ] Expand ML model to 100+ disease classes
- [ ] Add real-time video analysis
- [ ] Implement offline PWA mode
- [ ] Weather-based disease predictions
- [ ] Community forum for farmers
- [ ] Mobile apps (iOS/Android)
- [ ] Drone integration for field monitoring
- [ ] Blockchain-based crop certification

---

<div align="center">

**Made with ❤️ for farmers worldwide**

⭐ Star this repo if you find it helpful!

</div>
# Latest update
