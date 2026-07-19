# 📊 FarmLens Monitoring & Observability Setup

This guide explains how to set up production monitoring for FarmLens.

---

## 🔍 Error Tracking with Sentry

Sentry provides real-time error tracking, performance monitoring, and crash reporting.

### Backend Setup (FastAPI)

1. **Create Sentry Project**
   - Go to [sentry.io](https://sentry.io) and create account
   - Create new project → Select "Python" → Name it "FarmLens Backend"
   - Copy your DSN (looks like: `https://abc123@o123456.ingest.sentry.io/7891011`)

2. **Configure Backend**
   ```bash
   cd backend
   
   # Add to .env file
   echo "SENTRY_DSN=https://your-dsn-here" >> .env
   echo "ENVIRONMENT=production" >> .env
   ```

3. **Verify Setup**
   ```bash
   # Start backend
   python -m uvicorn main:app --reload
   
   # Check logs - should see:
   # ✅ Sentry initialized for production environment
   ```

4. **Test Error Tracking**
   - Trigger an error in your API
   - Check Sentry dashboard - error should appear within seconds
   - View stack traces, request data, user context

### Frontend Setup (React)

1. **Create Sentry Project**
   - In Sentry dashboard → Create new project
   - Select "React" → Name it "FarmLens Frontend"
   - Copy your DSN

2. **Configure Frontend**
   ```bash
   cd seed-to-insight-ui
   
   # Add to .env.local file
   echo "VITE_SENTRY_DSN=https://your-dsn-here" >> .env.local
   ```

3. **Verify Setup**
   ```bash
   # Start frontend
   npm run dev
   
   # Check browser console - should see:
   # ✅ Sentry initialized for development environment
   ```

4. **Test Error Tracking**
   ```typescript
   // In your React component
   import * as Sentry from "@sentry/react";
   
   // Manually capture error
   Sentry.captureException(new Error("Test error"));
   ```

---

## 🚨 Uptime Monitoring with UptimeRobot

UptimeRobot checks if your API is online and alerts you when it goes down.

### Setup (Free Forever Plan)

1. **Create Account**
   - Go to [uptimerobot.com](https://uptimerobot.com)
   - Sign up for free account (50 monitors included)

2. **Add Health Check Monitor**
   - Click "+ Add New Monitor"
   - Configure:
     ```
     Monitor Type: HTTP(s)
     Friendly Name: FarmLens API
     URL: https://your-api-domain.com/health
     Monitoring Interval: 5 minutes
     ```

3. **Add Keyword Monitoring** (Recommended)
   - Enable "Keyword Monitoring"
   - Keyword to Check: `healthy`
   - Alert if Keyword: NOT Found
   - This ensures the API returns valid JSON, not just HTTP 200

4. **Configure Alerts**
   - Email: Your email address
   - SMS: Your phone number (optional)
   - Slack: Your webhook URL (optional)
   - Alert When: Down for 2 minutes (default)

5. **Test Monitor**
   - Click "Test" button on your monitor
   - Should show: ✅ Up (200 OK)
   - Response time should be < 1000ms

### Multiple Environments

Create separate monitors for each environment:

```
Production API:  https://api.farmlens.com/health
Staging API:     https://staging-api.farmlens.com/health
Development API: http://dev-api.farmlens.com/health
```

---

## 📈 What Gets Monitored

### Sentry Tracks:
- ✅ Backend errors (Python exceptions)
- ✅ Frontend errors (React crashes, unhandled promises)
- ✅ Performance issues (slow API calls)
- ✅ Request/response data
- ✅ User context (email, ID, IP)
- ✅ Stack traces and breadcrumbs
- ✅ Release versions
- ✅ Session replays (when errors occur)

### UptimeRobot Tracks:
- ✅ API uptime (99.9% SLA)
- ✅ Response times
- ✅ SSL certificate expiry
- ✅ Keyword presence (validates JSON response)
- ✅ HTTP status codes
- ✅ Downtime duration

---

## 🎯 Alert Configuration

### Sentry Alert Rules

1. **High Priority Errors**
   - Go to Alerts → Create Alert Rule
   - Condition: "An event is seen"
   - Filter: `level:error`
   - Action: Send email + Slack notification

2. **Rate Limit Exceeded**
   - Condition: "An event is seen"
   - Filter: `http.status_code:429`
   - Action: Send email to admin

3. **Database Connection Failed**
   - Condition: "An event is seen"
   - Filter: `message:"Supabase"`
   - Action: Critical alert (SMS + email)

### UptimeRobot Alerts

1. **API Down**
   - Alert When: Monitor down for 2 minutes
   - Notify: Email + SMS
   - Re-alert: Every 30 minutes until resolved

2. **Slow Response**
   - Alert When: Response time > 5000ms
   - Notify: Email only
   - Re-alert: Once per hour

---

## 📊 Health Endpoint Details

FarmLens provides a comprehensive health check endpoint at `/health`:

```bash
curl https://your-api.com/health
```

**Response:**
```json
{
  "status": "healthy",
  "environment": "production",
  "ml_model": {
    "primary_method": "Fine-tuned EfficientNet (66 classes)",
    "finetuned_model_exists": true,
    "legacy_model_exists": true,
    "active_model": "best_farmlens_finetuned.keras",
    "tensorflow_available": true
  },
  "pytorch_available": false,
  "backup_apis": {
    "claude_configured": true,
    "gemini_configured": false
  },
  "supabase_configured": true
}
```

**What UptimeRobot Checks:**
- ✅ HTTP 200 status code
- ✅ Keyword "healthy" present in response
- ✅ Response time < 5 seconds
- ✅ Valid JSON format

---

## 🔧 Testing Your Setup

### 1. Test Sentry Error Tracking

**Backend:**
```bash
# SSH into your server
curl -X POST http://localhost:8000/api/test-error

# Check Sentry dashboard - error should appear
```

**Frontend:**
```typescript
// Add to any component temporarily
useEffect(() => {
  throw new Error("Test Sentry integration");
}, []);
```

### 2. Test Rate Limiting

```bash
# Trigger rate limit (10 requests/minute)
for i in {1..15}; do
  curl -X POST http://localhost:8000/analyze \
    -F "file=@test.jpg" \
    -F "language=en"
done

# Should see:
# - First 10: Success (200)
# - Last 5: Rate limited (429)
# - Sentry tracks 429 errors
```

### 3. Test UptimeRobot

```bash
# Simulate downtime
sudo systemctl stop farmlens-api

# Wait 2 minutes → Should receive alert
# Restart service
sudo systemctl start farmlens-api

# Should receive "service is back up" notification
```

---

## 📱 Mobile Alerts

### Recommended Apps:
- **UptimeRobot App** (iOS/Android) - Push notifications
- **Sentry Mobile App** (iOS/Android) - Error alerts
- **PagerDuty** (optional, for teams) - On-call rotation

---

## 💰 Pricing

### Free Tier (Sufficient for Small Projects)
- **Sentry**: 5,000 errors/month
- **UptimeRobot**: 50 monitors, 5-minute intervals

### Paid Plans (For Production)
- **Sentry Developer**: $26/month - 50k errors, performance monitoring
- **UptimeRobot Pro**: $7/month - 1-minute intervals, SMS alerts

---

## 🚀 Quick Start Checklist

- [ ] Create Sentry account
- [ ] Create backend Sentry project
- [ ] Add `SENTRY_DSN` to backend `.env`
- [ ] Create frontend Sentry project  
- [ ] Add `VITE_SENTRY_DSN` to frontend `.env.local`
- [ ] Test Sentry by triggering an error
- [ ] Create UptimeRobot account
- [ ] Add `/health` endpoint monitor
- [ ] Enable keyword monitoring ("healthy")
- [ ] Configure email/SMS alerts
- [ ] Test monitor by stopping API
- [ ] Set up Slack integration (optional)
- [ ] Configure alert rules in Sentry
- [ ] Install mobile apps for alerts

---

## 📞 Support

- **Sentry Docs**: https://docs.sentry.io/platforms/python/guides/fastapi/
- **UptimeRobot Docs**: https://blog.uptimerobot.com/web-monitoring-api-create-monitor/
- **FarmLens Issues**: https://github.com/devyash07/FARMLENS/issues

---

**Pro Tip**: Set up monitoring BEFORE going to production. You want to catch errors in staging, not from angry users! 😊
