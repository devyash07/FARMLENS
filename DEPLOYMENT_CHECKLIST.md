# 🚀 FarmLens Production Deployment Checklist

## ✅ Security Fixes Completed

- [x] Removed debug endpoint `/debug/users`
- [x] Fixed all NPM vulnerabilities (react-router, glob, esbuild)
- [x] Verified `.env` files not tracked in git
- [x] Created production environment template

---

## 📋 Pre-Deployment Steps

### 1. Supabase Configuration

#### A. Generate New Production API Keys
⚠️ **NEVER reuse development keys in production!**

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Navigate to: **Settings → API**
3. Note down (copy to deployment platform):
   - `URL`: Your project URL
   - `anon public` key (for frontend)
   - `service_role` key (if needed for admin tasks)
4. Navigate to: **Settings → API → JWT Settings**
   - Copy the `JWT Secret`

#### B. Create Required Database Tables

Run these SQL commands in **Supabase SQL Editor**:

```sql
-- Analysis History Table
CREATE TABLE IF NOT EXISTS analysis_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  image_url TEXT NOT NULL,
  heatmap_url TEXT,
  disease_name TEXT NOT NULL,
  disease_key TEXT,
  crop TEXT,
  confidence FLOAT NOT NULL,
  severity FLOAT,
  analyzed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE analysis_history ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only read their own history
CREATE POLICY "Users can read own analysis history"
  ON analysis_history FOR SELECT
  USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own records
CREATE POLICY "Users can insert own analysis history"
  ON analysis_history FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  category TEXT NOT NULL CHECK (category IN ('bug', 'feature', 'improvement', 'other')),
  message TEXT NOT NULL,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only read their own feedback
CREATE POLICY "Users can read own feedback"
  ON feedback FOR SELECT
  USING (auth.uid() = user_id);

-- RLS Policy: Users can insert feedback
CREATE POLICY "Users can insert feedback"
  ON feedback FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON analysis_history(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_history(analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
```

#### C. Configure Storage Buckets (for images)

1. Go to **Storage** in Supabase Dashboard
2. Create buckets:
   - `crop-images` (for uploaded crop images)
   - `heatmaps` (for AI-generated heatmaps)
3. Set bucket policies to **Private** (only authenticated users)
4. Add RLS policies:

```sql
-- Allow authenticated users to upload their images
CREATE POLICY "Users can upload own images"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'crop-images' AND 
    auth.uid()::text = (storage.foldername(name))[1]
  );

-- Allow users to read their own images
CREATE POLICY "Users can read own images"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'crop-images' AND 
    auth.uid()::text = (storage.foldername(name))[1]
  );
```

---

### 2. AI API Keys

#### Get New Production Keys:

**Gemini API (Primary)**:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Set API quota limits (recommended: 60 requests/minute)

**Anthropic Claude API (Backup)**:
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create new API key
3. Set usage limits

**HuggingFace (Optional)**:
1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Create new token with "Read" access

---

### 3. Environment Variables Setup

**For Backend Deployment** (Render/Railway/Vercel):

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxxx...
SUPABASE_JWT_SECRET=your-jwt-secret

# AI Services
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-api03-...
HF_TOKEN=hf_...

# Application
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Optional: External model hosting
MODEL_URL=https://storage.googleapis.com/your-bucket/models/best_farmlens_finetuned.keras
```

**For Frontend Deployment** (Vercel/Netlify):

```bash
VITE_API_BASE_URL=https://api.your-domain.com
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJxxxx...
```

---

### 4. Deploy Backend

**Recommended Platforms**: Render, Railway, Fly.io

#### Deploy on Render:

1. Connect GitHub repository
2. Create new **Web Service**
3. Settings:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend`
   - **Environment**: Python 3.11+
4. Add all environment variables from Step 3
5. Deploy!

#### Health Check:
```bash
curl https://your-backend-url.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "environment": "production",
  "ml_model": {...},
  "supabase_configured": true
}
```

---

### 5. Deploy Frontend

**Recommended Platforms**: Vercel, Netlify

#### Deploy on Vercel:

1. Connect GitHub repository
2. Framework: **Vite**
3. Root Directory: `.` (project root)
4. Build Command: `npm run build`
5. Output Directory: `dist`
6. Add environment variables from Step 3
7. Deploy!

#### Test Deployment:
1. Visit `https://your-app.vercel.app`
2. Try demo login: `demo@farmlens.com` / `Demo@123`
3. Upload test image
4. Verify disease detection works

---

### 6. Configure Custom Domain (Optional)

#### For Vercel (Frontend):
1. Go to **Settings → Domains**
2. Add: `farmlens.com` or `www.farmlens.com`
3. Update DNS records (provided by Vercel)

#### For Render (Backend):
1. Go to **Settings → Custom Domains**
2. Add: `api.farmlens.com`
3. Update DNS: `CNAME api → your-app.onrender.com`

#### Update CORS Settings:
After domain setup, update `ALLOWED_ORIGINS` in backend environment:
```bash
ALLOWED_ORIGINS=https://farmlens.com,https://www.farmlens.com
```

---

### 7. Post-Deployment Verification

#### Test Core Features:
- [ ] User can register new account
- [ ] User can login with existing account
- [ ] User can upload crop image
- [ ] AI disease detection returns results
- [ ] Heatmap displays correctly
- [ ] Disease information panel shows details
- [ ] Analysis history saves to database
- [ ] Feedback submission works
- [ ] Multi-language switching works
- [ ] Chatbot responds to queries

#### Performance Tests:
```bash
# Test backend response time
curl -o /dev/null -s -w "Time: %{time_total}s\n" https://your-api.com/health

# Run Lighthouse on frontend
npx lighthouse https://your-app.com --view
```

Target scores:
- Performance: >85
- Accessibility: >90
- Best Practices: >90
- SEO: >90

---

### 8. Set Up Monitoring

#### Backend Monitoring:
1. **Render**: Built-in metrics available in dashboard
2. **Optional**: Add [Sentry](https://sentry.io) for error tracking
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
   ```

#### Frontend Monitoring:
1. **Vercel Analytics**: Enable in project settings
2. **Optional**: Add [Sentry](https://sentry.io) for frontend errors

#### Uptime Monitoring:
1. Set up [UptimeRobot](https://uptimerobot.com) (free)
2. Monitor: `https://your-api.com/health`
3. Alert email if down >5 minutes

---

### 9. Security Hardening

#### Supabase Security:
1. **Enable Email Confirmations**: Settings → Authentication
2. **Set Password Policy**: Min 6 chars, require special chars
3. **Configure Rate Limiting**: Settings → API → Rate Limits
4. **Enable IP Allowlisting** (optional): Settings → Database → Connection Pooling

#### Backend Security:
1. Ensure HTTPS only (no HTTP)
2. Verify CORS is restricted to your domain
3. Test authentication flows thoroughly

---

### 10. Documentation Updates

#### Update README.md:
- [ ] Add production URL
- [ ] Update demo credentials
- [ ] Add deployment badges
- [ ] Document environment variables

#### Create CHANGELOG.md:
```markdown
# Changelog

## v1.0.0 - Production Release (2025-01-XX)
- 🎉 Initial production deployment
- 🔒 Security hardening complete
- 🗄️ Supabase integration
- 🤖 AI-powered disease detection
- 🌍 11-language support
```

---

## 🎯 Final Deployment Command

```bash
# Commit any final changes
git add -A
git commit -m "Production ready: Final configuration"
git push origin main

# Tag release
git tag -a v1.0.0 -m "Production Release v1.0.0"
git push origin v1.0.0
```

---

## 📞 Troubleshooting

### Issue: "CORS Error"
**Fix**: Update `ALLOWED_ORIGINS` in backend to include your frontend domain

### Issue: "Supabase connection failed"
**Fix**: Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` are correct

### Issue: "Image upload fails"
**Fix**: Check Supabase storage buckets and RLS policies

### Issue: "AI detection not working"
**Fix**: Verify `GEMINI_API_KEY` is valid and has quota remaining

---

## 🎉 You're Production Ready!

**Estimated Deployment Time**: 30-45 minutes

After following this checklist:
- ✅ Your app is secure
- ✅ Your database is configured
- ✅ Your AI models are working
- ✅ Your users can register and login
- ✅ Everything is monitored

**Next Steps**: Marketing, user feedback, iterate! 🚀
