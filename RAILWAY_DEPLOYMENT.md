# 🚂 Railway Backend Deployment Guide

## Overview

This guide will help you deploy the JobBot Norway FastAPI backend to Railway.app.

## Prerequisites

- GitHub account
- Railway account (sign up at https://railway.app)
- Backend code pushed to GitHub (✅ Already done!)

---

## Step 1: Create Railway Project (5 minutes)

### 1.1 Connect GitHub

1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account
5. Select repository: `SmmShaman/jobbot-norway-public`
6. Select branch: `claude/netlify-ui-011CUqJXNw4wkoYPis8TAkxF`

### 1.2 Configure Deployment

1. **Root Directory**: Set to `backend`
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Railway will auto-detect Python and use these settings.

---

## Step 2: Add Environment Variables (10 minutes)

Go to your Railway project → **Variables** tab → Add all these variables:

### Supabase
```bash
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0cm1pZGxoZmRieWJ4bXlvdnRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjQzNDc0OSwiZXhwIjoyMDc4MDEwNzQ5fQ.46uj0VMvxoWvApNTDdifgpfkbDv5fBhU3GfUjIGIwtU
SUPABASE_JWT_SECRET=generate_random_secret_here
```

### Azure OpenAI
```bash
AZURE_OPENAI_ENDPOINT=https://YOUR-ENDPOINT.openai.azure.com/
AZURE_OPENAI_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_DEPLOYMENT=your-gpt-deployment-name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

**NOTE**: Use your actual Azure OpenAI credentials from `backend/.env`

### Security
```bash
ENCRYPTION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
JWT_SECRET=jobbot_norway_secret_key_2024
```

### API Settings
```bash
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://jobbot-norway.netlify.app,https://YOUR-NETLIFY-SITE.netlify.app
```

### Skyvern (Optional - for future)
```bash
SKYVERN_API_URL=http://localhost:8000
SKYVERN_API_KEY=
SKYVERN_HEADLESS=false
```

**IMPORTANT**: Replace `YOUR-NETLIFY-SITE` in CORS_ORIGINS with your actual Netlify domain!

---

## Step 3: Deploy (2 minutes)

1. Click **"Deploy"** button
2. Wait 2-3 minutes for build
3. Railway will automatically:
   - Install dependencies
   - Start FastAPI server
   - Assign a public URL

### Get Your API URL

Once deployed, Railway will show your URL:
```
https://jobbot-norway-production.up.railway.app
```

**Copy this URL** - you'll need it for frontend configuration!

---

## Step 4: Update Frontend Environment Variables (5 minutes)

### 4.1 Update Netlify Environment Variables

Go to Netlify → Your site → **Site settings** → **Environment variables**

Update `VITE_API_URL`:
```bash
VITE_API_URL=https://jobbot-norway-production.up.railway.app
```

**Save** and trigger a new deploy in Netlify.

### 4.2 Update Local Development

Edit `web-app/.env`:
```bash
VITE_API_URL=https://jobbot-norway-production.up.railway.app
```

Or keep localhost for local backend testing:
```bash
VITE_API_URL=http://localhost:8000
```

---

## Step 5: Test Backend (10 minutes)

### 5.1 Check Health Endpoint

Open in browser:
```
https://YOUR-RAILWAY-URL.railway.app/health
```

Should see:
```json
{
  "status": "healthy"
}
```

### 5.2 Check API Documentation

Open:
```
https://YOUR-RAILWAY-URL.railway.app/docs
```

You should see FastAPI Swagger UI with all endpoints:
- `/api/scan-jobs` - Trigger job scanning
- `/api/settings/profile/{user_id}` - Get/update profile
- `/api/settings/settings/{user_id}` - Get/update settings
- `/api/settings/resume/{user_id}` - Upload resume
- `/api/dashboard-stats/{user_id}` - Get dashboard stats

### 5.3 Test from Frontend

1. Go to your Netlify site
2. Login with test credentials: `test@jobbot.no` / `Test123456`
3. Go to **Settings** page
4. Try updating profile → Should save successfully
5. Go to **Dashboard**
6. Click **"Scan Jobs Now"** → Should work!

---

## Step 6: Configure CORS (if needed)

If you see CORS errors in browser console:

1. Go to Railway → Your project → **Variables**
2. Update `CORS_ORIGINS`:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://YOUR-NETLIFY-SITE.netlify.app
```
3. Redeploy

---

## Troubleshooting

### ❌ Build Fails

**Check Railway logs:**
```
Railway Dashboard → Deployments → View Logs
```

Common issues:
- Missing dependencies in `requirements.txt`
- Syntax errors in Python code
- Wrong root directory (should be `backend`)

**Solution**: Fix code, commit, push → Railway auto-redeploys

### ❌ "Internal Server Error" (500)

**Check Runtime logs:**
```
Railway Dashboard → View Logs (running deployment)
```

Common issues:
- Missing environment variables
- Supabase connection failed
- Azure OpenAI key invalid

**Solution**: Verify all env vars are set correctly

### ❌ CORS Errors in Browser

**Symptoms:**
```
Access to fetch at 'https://...' from origin 'https://...' has been blocked by CORS
```

**Solution:**
1. Add your Netlify domain to `CORS_ORIGINS`
2. Redeploy backend

### ❌ "No search URLs configured"

**Symptoms:**
When clicking "Scan Jobs Now", error appears

**Solution:**
1. Go to Settings → Search URLs
2. Add at least one NAV or FINN search URL
3. Save settings
4. Try scanning again

---

## Cost Estimate

Railway offers:
- **Free tier**: $5 credit/month (good for testing)
- **Developer plan**: $5/month + usage ($0.000231/GB-hour)

Estimated cost for JobBot Norway: **$5-10/month**

---

## Monitoring

### Railway Dashboard

Monitor in Railway:
- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Deployments**: History of all deploys

### Health Checks

Set up health check monitoring:
1. Railway → Your service → **Settings**
2. Health Check Path: `/health`
3. Health Check Interval: 60 seconds

---

## Automatic Deployments

Railway automatically redeploys when you push to GitHub!

**Workflow:**
1. Make changes to backend code
2. Commit and push to `claude/netlify-ui-011CUqJXNw4wkoYPis8TAkxF`
3. Railway detects push → Rebuilds → Redeploys
4. ✅ New version live in ~2 minutes!

---

## Next Steps

After backend is deployed:

1. ✅ Test all Settings operations
2. ✅ Add search URLs in Settings
3. ✅ Upload resume
4. ✅ Run "Scan Jobs Now"
5. ✅ Check Jobs page for discovered jobs
6. 🔮 Set up Skyvern for automated applications (future phase)
7. 🔮 Configure Telegram notifications (future phase)

---

## Support

**Railway Issues:**
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

**JobBot Issues:**
- Check Railway logs first
- Verify all environment variables
- Test API endpoints with `/docs`

---

## Summary Checklist

- [ ] Railway project created
- [ ] GitHub connected
- [ ] Root directory set to `backend`
- [ ] All environment variables added
- [ ] Backend deployed successfully
- [ ] Health endpoint responding
- [ ] API docs accessible at `/docs`
- [ ] Netlify `VITE_API_URL` updated
- [ ] Frontend can communicate with backend
- [ ] Settings operations working
- [ ] "Scan Jobs Now" working

**When all checked ✅ → BACKEND IS LIVE! 🚀**
