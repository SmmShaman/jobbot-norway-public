# 🤖 JobBot Norway - Job Application Automation

> **Automated job searching, AI analysis, and application submission for Norwegian job market**

---

## ⚠️ FOR NEW CLAUDE CODE SESSION - START HERE!

**IMPORTANT:** If you're continuing work on this project, follow these steps:

### Step 1: Update Repository (CRITICAL!)
```bash
# You might be on an old version. Update first!
git fetch origin
git checkout claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
git pull origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
```

### Step 2: Read Context Files
After updating, these files will appear:
```bash
# Quick overview (read first!)
Read QUICK_START.md

# Full context (read for details)
Read SESSION_CONTEXT.md

# Project rules (always follow!)
Read CLAUDE.md
```

### Step 3: Continue Work
Check the TODO list in SESSION_CONTEXT.md for next tasks.

---

## 📊 Current Status (2025-11-08)

### ✅ Completed
- Frontend deployed to Netlify (auto-deploy on push)
- Backend deployed to Google Cloud Run
- Database setup in Supabase with all tables
- Worker running on local PC with Skyvern integration
- Real-time Worker monitoring in Dashboard
- Comprehensive Jobs page with all metadata (30+ fields)
- Duplicate prevention (UNIQUE constraint on user_id + url)

### 🎯 Next Priority
1. User needs to create `jobs` table in Supabase
   - File: `database/jobs_table_schema_fixed.sql`
   - Execute in Supabase SQL Editor
2. Test end-to-end job scanning flow
3. Improve Skyvern templates
4. Add AI job relevance analysis

---

## 🏗️ Architecture

```
Cloud (Netlify + Cloud Run + Supabase)
              ↕
       scan_tasks table (queue)
              ↕
    Local PC (Worker + Skyvern)
```

**Hybrid approach:**
- Frontend/Backend in cloud
- Worker + Skyvern on user's local PC (for browser automation)

---

## 🔗 Important Links

- **Frontend:** https://jobbot-norway.netlify.app
- **Backend:** https://jobbot-backend-255588880592.us-central1.run.app
- **Supabase:** https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm
- **GitHub:** https://github.com/SmmShaman/jobbot-norway-public

---

## 📁 Repository Structure

```
jobbot-norway-public/
├── backend/              # FastAPI backend (Cloud Run)
├── web-app/             # React frontend (Netlify)
├── worker/              # Python Worker (runs on local PC)
│   ├── worker.py        # Main worker script
│   └── skyvern_templates/  # Scraping templates
├── database/            # SQL schemas
│   └── jobs_table_schema_fixed.sql  # Jobs table (use this!)
├── SESSION_CONTEXT.md   # Full context for continuation
├── QUICK_START.md       # Quick reference
└── CLAUDE.md            # Project rules
```

---

## 🚀 Technologies

- **Frontend:** React + TypeScript + Vite + TailwindCSS
- **Backend:** FastAPI + Python
- **Database:** Supabase (PostgreSQL)
- **Worker:** Python + Skyvern (AI browser automation)
- **Deployment:** Netlify (frontend), Google Cloud Run (backend)

---

## 🔐 Environment Variables

### Frontend (`web-app/.env`)
```bash
VITE_SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
VITE_SUPABASE_ANON_KEY=<anon_key>
VITE_API_URL=https://jobbot-backend-255588880592.us-central1.run.app
```

### Backend (Cloud Run env vars)
```bash
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=<service_role_key>
ALLOWED_ORIGINS=https://jobbot-norway.netlify.app
```

### Worker (`worker/.env`)
```bash
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=<service_role_key>
SKYVERN_API_URL=http://localhost:8000
```

---

## 🛠️ Development

### Run Frontend Locally
```bash
cd web-app
npm install
npm run dev  # http://localhost:5173
```

### Run Backend Locally
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload  # http://localhost:8000
```

### Run Worker (on user's PC)
```bash
cd ~/jobbot-norway-public/worker
pip install -r requirements.txt
python3 worker.py
```

---

## 📝 Git Workflow

**Current branch:** `claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF`

**Commit format:**
```bash
git commit -m "✨ Feature description"
git commit -m "🔧 Fix description"
git commit -m "🔒 Security change"
```

**Deploy:**
- Frontend: Auto-deploys on `git push` (Netlify)
- Backend: Manual deploy via `gcloud run deploy`
- Worker: `git pull` on local PC

---

## 🐛 Troubleshooting

**If SESSION_CONTEXT.md or QUICK_START.md not found:**
```bash
# You're on an old version! Update:
git pull origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF

# Or read directly from GitHub:
# https://github.com/SmmShaman/jobbot-norway-public/blob/claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF/SESSION_CONTEXT.md
```

**Worker can't find Skyvern:**
```bash
# Make sure Skyvern is running:
docker-compose up skyvern
curl http://localhost:8000/api/v1/health
```

---

## 📞 Support

**Repository:** https://github.com/SmmShaman/jobbot-norway-public
**Owner:** SmmShaman
**Branch:** `claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF`

---

## ⚡ Quick Commands

```bash
# Check current status
git status
git log --oneline -5

# Update to latest
git pull origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF

# Read context
cat SESSION_CONTEXT.md
cat QUICK_START.md

# Run locally
cd web-app && npm run dev          # Frontend
cd backend && uvicorn app.main:app --reload  # Backend
cd worker && python3 worker.py     # Worker
```

---

**Last Updated:** 2025-11-08
**Status:** ✅ All components deployed and working
**Next:** Create jobs table in Supabase, test E2E flow

---

*Ready for AI-assisted development! 🚀*
