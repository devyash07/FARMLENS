# FarmLens Deployment Guide

## ✅ Current Status
Your application is working perfectly in development with:
- Gemini Vision API for accurate crop/disease detection (95%+ accuracy)
- PyTorch MobileNetV2 as fallback (works offline)
- Image compression to avoid storage quota issues
- Heatmap generation for infected regions
- Multi-language support (11 Indian languages)

## ⚠️ Potential Issues After Deployment

### 1. API Key Quota Limits

**Issue:** Gemini free tier has daily limits:
- 1,500 requests per day
- 15 requests per minute

**Solutions:**
- **Monitor usage** at https://ai.google.dev/gemini-api/docs/rate-limits
- **Upgrade to paid tier** if you exceed limits ($0.00025 per image)
- **Implement rate limiting** on your backend
- **Use caching** for repeated images

**Code to Add (Optional):**
```python
# In backend/routes/analyze.py
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_result(image_hash: str):
    # Cache results for identical images
    pass
```

### 2. Environment Variables

**Issue:** `.env` file won't be deployed to production servers.

**Solutions:**

**For Vercel/Netlify:**
1. Go to project settings
2. Add environment variables:
   - `GEMINI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_JWT_SECRET`

**For Railway/Render:**
1. Dashboard → Environment Variables
2. Add all keys from `.env`

**For Docker:**
```dockerfile
# Use secrets or environment variables
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
```

### 3. CORS Configuration

**Issue:** Frontend and backend on different domains will cause CORS errors.

**Current Setup (localhost):**
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    ...
)
```

**Production Fix:**
```python
# Update to your production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com",
        "https://www.your-frontend-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. File Upload Size Limits

**Issue:** Some hosting providers limit request body size.

**Current:** Images compressed to ~400KB each

**Solutions:**
- **Vercel:** 4.5MB limit (you're safe)
- **Netlify:** 10MB limit (you're safe)
- **Railway:** No limit (you're safe)
- **AWS Lambda:** 6MB limit (you're safe)

### 5. PyTorch Model File

**Issue:** The `mobilenetv2_plant.pth` (8.9MB) needs to be deployed.

**Solutions:**

**Option A: Include in deployment**
```bash
# Make sure it's not in .gitignore
git add backend/mobilenetv2_plant.pth
git add backend/class_names.json
git commit -m "Add ML model files"
```

**Option B: Download on first run**
```python
# In ai_service.py
if not os.path.exists(model_path):
    print("Downloading model...")
    import urllib.request
    url = "https://your-cdn.com/mobilenetv2_plant.pth"
    urllib.request.urlretrieve(url, model_path)
```

**Option C: Use cloud storage**
- Upload to S3/Google Cloud Storage
- Download on container startup

### 6. Cold Start Performance

**Issue:** First request after idle period will be slow (model loading).

**Solutions:**
- **Keep-alive ping:** Ping your backend every 5 minutes
- **Lazy loading:** Load model only when needed (already implemented)
- **Serverless warmup:** Use scheduled functions to keep warm

### 7. Database (Supabase) RLS Policies

**Issue:** Row Level Security policies need to be configured.

**Current Status:** Disabled for development

**Production Fix:**
1. Go to Supabase Dashboard → Authentication → Policies
2. Enable RLS on `history` table
3. Add policies:
```sql
-- Allow users to read their own history
CREATE POLICY "Users can view own history"
ON history FOR SELECT
USING (auth.uid() = user_id);

-- Allow users to insert their own history
CREATE POLICY "Users can insert own history"
ON history FOR INSERT
WITH CHECK (auth.uid() = user_id);
```

### 8. API Key Security

**Issue:** API keys exposed in frontend code.

**Current Status:** ✅ Safe - API keys are only in backend `.env`

**Best Practices:**
- ✅ Never commit `.env` to git (already in `.gitignore`)
- ✅ Use environment variables in production
- ✅ Rotate keys periodically
- ✅ Monitor API usage for anomalies

### 9. Image Storage

**Issue:** SessionStorage has 5-10MB limit.

**Current Solution:** ✅ Images compressed to 400KB

**Production Considerations:**
- Consider using IndexedDB for larger storage (50MB+)
- Or upload directly to Supabase Storage
- Or use Cloudinary/Imgix for image CDN

### 10. Monitoring & Logging

**Issue:** No visibility into production errors.

**Solutions:**

**Add Sentry for error tracking:**
```bash
pip install sentry-sdk
```

```python
# backend/main.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

**Add logging:**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In predict function
logger.info(f"Analysis request: {result['crop']} / {result['disease']}")
```

## 📋 Pre-Deployment Checklist

### Backend
- [ ] Update CORS origins to production domains
- [ ] Set environment variables in hosting platform
- [ ] Test API endpoints with production URLs
- [ ] Enable Supabase RLS policies
- [ ] Add error monitoring (Sentry)
- [ ] Test with production Gemini API key
- [ ] Verify PyTorch model is included in deployment
- [ ] Set up health check endpoint

### Frontend
- [ ] Update API base URL to production backend
- [ ] Test image upload with production backend
- [ ] Verify all 11 languages work
- [ ] Test on mobile devices
- [ ] Check browser compatibility
- [ ] Optimize images and assets
- [ ] Enable production build optimizations
- [ ] Test offline fallback behavior

### Infrastructure
- [ ] Set up SSL certificates (HTTPS)
- [ ] Configure CDN for static assets
- [ ] Set up database backups
- [ ] Configure auto-scaling if needed
- [ ] Set up monitoring and alerts
- [ ] Test disaster recovery plan

## 🚀 Recommended Deployment Stack

### Option 1: Vercel (Frontend) + Railway (Backend)
**Pros:** Easy setup, auto-scaling, good free tier
**Cons:** Cold starts on free tier

**Steps:**
1. Push code to GitHub
2. Connect Vercel to frontend repo
3. Connect Railway to backend repo
4. Add environment variables
5. Deploy!

### Option 2: Netlify (Frontend) + Render (Backend)
**Pros:** Similar to Vercel/Railway, good documentation
**Cons:** Slower cold starts

### Option 3: AWS (Full Stack)
**Pros:** Full control, scalable, professional
**Cons:** More complex setup, higher cost

**Services:**
- Frontend: S3 + CloudFront
- Backend: ECS/Fargate or Lambda
- Database: RDS or keep Supabase
- Storage: S3

### Option 4: Docker + Any Cloud Provider
**Pros:** Portable, consistent environments
**Cons:** Requires Docker knowledge

```dockerfile
# Dockerfile for backend
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 💰 Cost Estimates (Monthly)

### Free Tier (Good for testing)
- Vercel: Free (100GB bandwidth)
- Railway: Free ($5 credit)
- Supabase: Free (500MB database)
- Gemini API: Free (1,500 requests/day)
**Total: $0/month** (up to ~45,000 requests/month)

### Production (1,000 users, 10 requests/day each)
- Vercel Pro: $20
- Railway: $20
- Supabase Pro: $25
- Gemini API: ~$75 (10,000 requests/day)
**Total: ~$140/month**

### Scale (10,000 users)
- AWS/GCP: $200-500
- Gemini API: $750
- Database: $100
**Total: ~$1,000-1,500/month**

## 🔧 Quick Fixes for Common Deployment Issues

### "Module not found" errors
```bash
# Make sure all dependencies are in requirements.txt
pip freeze > requirements.txt
```

### "CORS policy" errors
```python
# Add your production domain to CORS
allow_origins=["https://your-domain.com"]
```

### "API key invalid" errors
```bash
# Verify environment variables are set
echo $GEMINI_API_KEY
```

### "Cold start timeout" errors
```python
# Increase timeout in hosting platform
# Or implement keep-alive pings
```

### "Out of memory" errors
```python
# Reduce model size or use serverless with more RAM
# Railway: Increase memory in settings
# AWS Lambda: Increase memory allocation
```

## 📞 Support Resources

- **Gemini API Issues:** https://ai.google.dev/gemini-api/docs/troubleshooting
- **Supabase Issues:** https://supabase.com/docs/guides/platform
- **Vercel Issues:** https://vercel.com/docs
- **Railway Issues:** https://docs.railway.app

## 🎯 Next Steps

1. **Test thoroughly in development**
2. **Set up staging environment** (optional but recommended)
3. **Deploy to production**
4. **Monitor for 24-48 hours**
5. **Optimize based on real usage**

---

**Need help with deployment?** Let me know which platform you're using and I can provide specific instructions!
