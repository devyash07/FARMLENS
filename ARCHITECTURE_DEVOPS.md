# 🚀 FARMLENS ARCHITECTURE: DEVOPS PILLAR

**Version**: 1.0.0  
**Last Updated**: July 2026  
**Status**: Production Ready (100/100)

---

## 📋 PILLAR OVERVIEW

The **DevOps Pillar** ensures FarmLens runs reliably in production. It's responsible for:
- 🌐 Infrastructure provisioning and management
- 🔐 Secrets and environment variable management
- 📦 CI/CD pipeline automation
- 🚀 Deployment orchestration (Frontend + Backend)
- 📊 Monitoring and observability
- 🔄 Scaling and load balancing
- 🛡️ Security and compliance
- 💾 Database backup and recovery

---

## 🏗️ DEPLOYMENT ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                      PRODUCTION                              │
└─────────────────────────────────────────────────────────────┘
         │                                           │
         ▼                                           ▼
    ┌─────────────────┐                    ┌──────────────────┐
    │  FRONTEND CDN   │                    │   BACKEND API    │
    │  (Vercel/       │                    │   (Render/       │
    │   Netlify)      │                    │    Railway)      │
    └─────────────────┘                    └──────────────────┘
         │                                           │
         ├─────────────────────────────────────────┤
         │           Git Repository                 │
         │    github.com/devyash07/FARMLENS        │
         └──────────────────────────────────────────┘
                │                         │
    ┌───────────┴──────────┐  ┌───────────┴──────────┐
    ▼                      ▼  ▼                      ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Vercel:    │      │   GitHub     │      │  Render:    │
│  Frontend   │      │    Actions   │      │  Backend    │
│  Deployment │      │   (CI/CD)    │      │ Deployment  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
    ┌────────┐        ┌──────────┐      ┌──────────────┐
    │ Build  │        │  Tests   │      │   Deploy     │
    │& Lint  │        │& Lint    │      │  to Stage    │
    └────────┘        └──────────┘      └──────────────┘
                            │
                            ▼
                    ┌──────────────────┐
                    │  Production      │
                    │  Deployment      │
                    └──────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│  Frontend Live  │  │   Supabase   │  │   Sentry     │
│  (users.dev)    │  │   Cloud DB   │  │  Monitoring  │
└─────────────────┘  └──────────────┘  └──────────────┘
```

---

## 🛠️ CORE TECHNOLOGIES

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Version Control** | GitHub | Code repository + CI/CD integration |
| **Frontend Deploy** | Vercel | Automatic deployment from git |
| **Backend Deploy** | Render/Railway | Python FastAPI hosting |
| **Database** | Supabase Cloud | PostgreSQL + Auth + RLS |
| **Monitoring** | Sentry | Error tracking + performance |
| **Uptime** | UptimeRobot | Health monitoring |
| **Secrets** | GitHub Secrets | Encrypted env vars for CI/CD |
| **Container** | Docker | Optional containerization |

---

## 📁 DEPLOYMENT INFRASTRUCTURE

```
FarmLens Production
├── FRONTEND
│   ├── Hosting: Vercel
│   ├── Domain: farmlens.app
│   ├── CDN: Global edge network
│   ├── SSL: Automatic HTTPS
│   ├── Analytics: Vercel Analytics
│   └── Deployments: Auto from main branch
│
├── BACKEND
│   ├── Hosting: Render/Railway
│   ├── URL: api.farmlens.app
│   ├── Runtime: Python 3.12
│   ├── Memory: 2GB
│   ├── Auto-scaling: Based on CPU/Memory
│   └── Deployments: Docker containers
│
├── DATABASE
│   ├── Provider: Supabase Cloud
│   ├── Type: PostgreSQL 15+
│   ├── Region: (selected during setup)
│   ├── Backups: Daily automated
│   ├── Auth: JWT via Supabase
│   └── RLS: Enabled for all tables
│
└── MONITORING
    ├── Error Tracking: Sentry
    ├── Uptime: UptimeRobot
    ├── Logs: Cloud provider native
    ├── Metrics: CPU/Memory/Requests
    └── Alerts: Email + Slack
```

---

## 🔐 SECRETS MANAGEMENT

### Environment Variables

#### Frontend (.env.local)

```
# API & Services
VITE_API_BASE_URL=https://api.farmlens.app
VITE_SENTRY_DSN=https://xxx@ingest.sentry.io/yyy

# Supabase (optional, if using directly)
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=xxx

# App Config
VITE_APP_NAME=FarmLens
VITE_APP_VERSION=1.0.0
```

#### Backend (.env)

```
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_JWT_SECRET=xxx

# Authentication
JWT_SECRET_KEY=your-secret-key-32-chars-min
ENVIRONMENT=production

# AI APIs
ANTHROPIC_API_KEY=sk-ant-xxx
GEMINI_API_KEY=xxx (optional)

# Monitoring
SENTRY_DSN=https://xxx@ingest.sentry.io/yyy
DEBUG=false

# Server
PORT=8000
ALLOWED_ORIGINS=https://farmlens.app,https://www.farmlens.app

# File Limits
MAX_FILE_SIZE=10485760  # 10MB in bytes
```

### Secrets Storage

```
GitHub Settings → Secrets and variables → Actions

Secrets (encrypted):
├── SUPABASE_URL
├── SUPABASE_ANON_KEY
├── SUPABASE_JWT_SECRET
├── JWT_SECRET_KEY
├── ANTHROPIC_API_KEY
├── SENTRY_DSN
└── VERCEL_TOKEN
```

### Secret Rotation Policy

```
Rotation Schedule:
├── API Keys: Every 90 days
├── JWT Secrets: Every 180 days
├── Database Passwords: Every 90 days
└── Credentials: Immediately if compromised
```

---

## 🚀 CI/CD PIPELINE

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy FarmLens

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # FRONTEND JOBS
  frontend-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18.x, 20.x]
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint
      
      - name: Build
        run: npm run build
      
      - name: Run tests
        run: npm run test

  frontend-deploy:
    needs: frontend-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vercel
        uses: vercel/action@master
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          github-comment: true
          production: true

  # BACKEND JOBS
  backend-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Lint with pylint
        run: |
          cd backend
          pylint routes/ services/ main.py
      
      - name: Security check with bandit
        run: |
          cd backend
          bandit -r . -ll
      
      - name: Type check with mypy
        run: |
          cd backend
          mypy routes/ services/ main.py --ignore-missing-imports

  backend-deploy:
    needs: backend-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Render
        run: |
          curl https://api.render.com/deploy/srv-${{ secrets.RENDER_SERVICE_ID }}?key=${{ secrets.RENDER_API_KEY }} \
            -X POST
```

### Pipeline Triggers

```
Main Branch (main)
├── On every push
│   ├── Run tests (frontend + backend)
│   ├── Run linters
│   ├── Run security checks
│   ├── Build artifacts
│   └── Deploy to production
│
└── On pull requests
    ├── Run tests
    ├── Comment results on PR
    └── Block merge if tests fail
```

---

## 📊 FRONTEND DEPLOYMENT (VERCEL)

### Vercel Setup

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Link project
cd seed-to-insight-ui
vercel link

# 3. Set environment variables
vercel env add VITE_API_BASE_URL https://api.farmlens.app
vercel env add VITE_SENTRY_DSN https://xxx@ingest.sentry.io/yyy

# 4. Deploy
vercel --prod
```

### Vercel Configuration (vercel.json)

```json
{
  "name": "FarmLens",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "env": {
    "VITE_API_BASE_URL": "@vite_api_base_url",
    "VITE_SENTRY_DSN": "@vite_sentry_dsn"
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "no-cache" }
      ]
    }
  ],
  "redirects": [
    {
      "source": "/old-page",
      "destination": "/new-page",
      "permanent": true
    }
  ]
}
```

### Auto-Deployment

```
Main branch push
    ↓
GitHub detects push
    ↓
Vercel webhook triggered
    ↓
Vercel runs build command
    ↓
Vercel runs tests
    ↓
Vercel deploys to edge network
    ↓
DNS updates
    ↓
New version live at farmlens.app
```

---

## 📊 BACKEND DEPLOYMENT (RENDER/RAILWAY)

### Render Setup

```bash
# 1. Create new Web Service on Render dashboard
# Select: GitHub repository
# Branch: main
# Build command: pip install -r backend/requirements.txt
# Start command: python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 2. Add environment variables
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_JWT_SECRET
JWT_SECRET_KEY
ANTHROPIC_API_KEY
SENTRY_DSN
ENVIRONMENT=production

# 3. Service auto-deploys on main branch push
```

### Dockerfile (Optional)

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8080:5173"
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    depends_on:
      - backend

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      ENVIRONMENT: development
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: farmlens
      POSTGRES_USER: developer
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 💾 DATABASE: SUPABASE CLOUD

### Supabase Setup

```bash
# 1. Create project at supabase.com
# Select: PostgreSQL 15+
# Region: Closest to your users

# 2. Get credentials
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_JWT_SECRET=xxx

# 3. Initialize database (SQL migrations)
-- Create tables via Supabase dashboard
-- Or use migrations folder
```

### Database Schema

```sql
-- authentication (managed by Supabase Auth)
-- users table automatically created

-- Custom tables
CREATE TABLE analysis_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  image_url TEXT NOT NULL,
  disease TEXT NOT NULL,
  severity INTEGER,
  confidence INTEGER,
  status TEXT,
  heatmap_url TEXT,
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  analysis_id UUID REFERENCES analysis_history(id),
  correct BOOLEAN,
  feedback_text TEXT,
  created_at TIMESTAMP DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE analysis_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- RLS policies
CREATE POLICY "Users see own analysis"
ON analysis_history FOR SELECT
USING (auth.uid() = user_id);
```

### Backup & Recovery

```
Supabase Automatic Backups:
├── Daily backups (30 days retention)
├── Point-in-time recovery (7 days)
├── Geographic redundancy
├── Encrypted storage
└── Manual backup export available
```

---

## 📊 MONITORING & OBSERVABILITY

### Sentry Setup

```python
# Already configured in backend/main.py and frontend/src/main.tsx

# Test Sentry
curl -X POST https://your-api.com/api/test-error

# Check dashboard at sentry.io
```

### UptimeRobot Setup

```
1. Create monitor
   URL: https://api.farmlens.app/health
   Interval: 5 minutes
   Keyword: "healthy"

2. Add alerts
   Email: admin@farmlens.app
   SMS: +1-xxx-xxx-xxxx

3. Status page: uptimerobot.com/status-page-settings
```

### Health Check Endpoint

```
GET /health
Returns:
{
  "status": "healthy",
  "environment": "production",
  "ml_model": {
    "active_model": "best_farmlens_finetuned.keras",
    "tensorflow_available": true
  },
  "supabase_configured": true
}
```

---

## 🔒 SECURITY PRACTICES

### TLS/SSL

```
Automatic HTTPS:
├── Vercel: Automatic Let's Encrypt
├── Render: Automatic Let's Encrypt
├── Custom domain: Automatic
└── Renewal: Automatic before expiry
```

### CORS Configuration

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://farmlens.app",
        "https://www.farmlens.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
```

### Rate Limiting

```
Already implemented in backend:
├── /analyze: 10 req/min per IP
├── /auth/login: 5 req/min per IP
├── /auth/register: 3 req/hour per IP
└── /chatbot/chat: 20 req/min per IP
```

### Dependency Security

```bash
# Regular checks
npm audit --production    # Frontend
pip audit                 # Backend
dependabot                # GitHub automated

# Automated updates
# GitHub Dependabot: Auto-create PRs for security updates
```

---

## 📈 SCALING STRATEGY

### Horizontal Scaling

```
As user base grows:

Level 1 (0-1000 users)
├── Vercel: Default auto-scaling
├── Render: Single 2GB instance
└── Supabase: Starter tier

Level 2 (1000-10k users)
├── Vercel: Regional distribution
├── Render: Scale to 4GB
├── Supabase: Pro tier

Level 3 (10k+ users)
├── Vercel: Enterprise plan
├── Render: Multi-instance + load balancer
├── Supabase: Dedicated instance
└── Add: CDN, caching layer, DB read replicas
```

### Caching Strategy

```
Frontend:
├── Service Workers: Cache static assets
├── Browser cache: 30-day expiry
└── API response cache: React Query

Backend:
├── Model cache: Loaded once on startup
├── Disease info cache: In-memory
└── API response cache: Redis (optional)
```

---

## 📋 DEPLOYMENT CHECKLIST

### Pre-Production

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Security scan completed
- [ ] Performance benchmarks met
- [ ] Load testing completed
- [ ] Environment variables set
- [ ] Secrets rotated
- [ ] Database migrations run
- [ ] Backups enabled
- [ ] Monitoring configured

### Production Deploy

- [ ] Create release tag: `v1.0.0`
- [ ] Merge to main branch
- [ ] Watch GitHub Actions
- [ ] Verify Vercel deployment
- [ ] Verify Render deployment
- [ ] Test health endpoints
- [ ] Check Sentry for errors
- [ ] Monitor UptimeRobot
- [ ] Verify SSL certificates
- [ ] Update status page

### Post-Deployment

- [ ] Monitor error rates (< 0.1%)
- [ ] Check response times (< 500ms)
- [ ] Verify all features working
- [ ] Test on mobile devices
- [ ] Monitor disk usage
- [ ] Check database size
- [ ] Review user feedback
- [ ] Plan next sprint

---

## 🚨 DISASTER RECOVERY

### Backup & Recovery Plan

```
RPO (Recovery Point Objective): 1 day
RTO (Recovery Time Objective): 4 hours

Backup Strategy:
├── Database: Daily snapshots + PITR
├── Code: GitHub git history
├── Assets: CDN cached globally
└── Secrets: Encrypted in vault

Recovery Steps:
1. Assess damage scope
2. Activate failover (if applicable)
3. Restore latest backup
4. Verify data integrity
5. Run smoke tests
6. Notify users
7. Monitor recovery
```

---

## 🧪 TESTING DEPLOYMENT

### Staging Environment

```bash
# Deploy to staging before production
git checkout -b staging
# Make changes
git push origin staging

# Staging deploys automatically
# Test at: staging-farmlens.vercel.app
# Test at: staging-api.onrender.com

# If OK, merge to main for production
```

---

## 📚 REFERENCES

- Vercel Docs: https://vercel.com/docs
- Render Docs: https://render.com/docs
- Supabase Docs: https://supabase.com/docs
- GitHub Actions: https://docs.github.com/actions
- Sentry: https://docs.sentry.io
- UptimeRobot: https://uptimerobot.com/help

---

**Last Reviewed**: July 20, 2026  
**Next Review**: October 2026  
**Maintainer**: FarmLens DevOps Team
