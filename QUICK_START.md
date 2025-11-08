# 🚀 Quick Start for New Claude Code Session

## ⚠️ CRITICAL FIRST STEP: Check Your Branch!

**You MUST be on:** `claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF`

### Quick Check:
```bash
git branch  # Should show * claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
wc -l README.md  # Should be 500+ lines (not 32 or 83!)
```

### If you're on wrong branch or README is too short:
```bash
git fetch origin
git checkout claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
git pull origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
```

**After switching, README.md will be 500+ lines and these files will appear:**
- SESSION_CONTEXT.md
- QUICK_START.md
- START_HERE_FIRST.md
- database/
- web-app/
- worker/

---

## 📖 Read This First

**Full context document:**
```bash
Read SESSION_CONTEXT.md
```
Or via web: https://github.com/SmmShaman/jobbot-norway-public/blob/claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF/SESSION_CONTEXT.md

**Previous session ended:** Token limit reached (~700k characters)
**Current status:** All changes committed and pushed ✅

---

## ⚡ Quick Facts

- **Branch:** `claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF`
- **Latest commit:** `db8c630` - Add session context documentation
- **Frontend:** https://jobbot-norway.netlify.app (auto-deploys)
- **Backend:** https://jobbot-backend-255588880592.us-central1.run.app
- **Database:** Supabase (ptrmidlhfdbybxmyovtm)
- **Worker:** Runs on user's PC at `~/jobbot-norway-public/worker/`

---

## ✅ What's Done

- ✅ Frontend deployed (Netlify)
- ✅ Backend deployed (Cloud Run)
- ✅ Database setup (Supabase)
- ✅ Worker running on local PC
- ✅ Skyvern integrated (Docker, localhost:8000)
- ✅ Real-time Worker monitoring in Dashboard
- ✅ Comprehensive Jobs page with all metadata
- ✅ Duplicate prevention (UNIQUE constraint on user_id + url)

---

## 🎯 Next Priority

**IMMEDIATE (User waiting):**
1. User needs to create `jobs` table in Supabase
   - File: `database/jobs_table_schema_fixed.sql`
   - Execute in: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new

**NEXT TASKS:**
2. Test end-to-end job scanning flow
3. Improve Skyvern templates for better data extraction
4. Add AI job relevance analysis (Phase 4)
5. Cover letter generation
6. Application automation

---

## 🗂️ Key Files to Review

```bash
SESSION_CONTEXT.md          # Full context (read this!)
CLAUDE.md                   # Project rules (always follow!)
database/jobs_table_schema_fixed.sql  # DB schema
web-app/src/pages/Jobs.tsx  # Jobs display page
worker/worker.py            # Worker logic
worker/skyvern_templates/   # Skyvern scraping templates
```

---

## 🔑 Environment Variables

**Locations:**
- Frontend: `web-app/.env` (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)
- Backend: Cloud Run env vars (SUPABASE_SERVICE_KEY, ALLOWED_ORIGINS)
- Worker: `worker/.env` (SUPABASE_SERVICE_KEY, SKYVERN_API_URL)

**NOTE:** User has all keys, ask if needed

---

## 🛠️ Common Commands

```bash
# Check current status
git status
git log --oneline -5

# Run frontend locally
cd web-app && npm run dev

# Run worker (on user's PC)
cd ~/jobbot-norway-public/worker && python3 worker.py

# Commit and push
git add .
git commit -m "✨ Your message"
git push
```

---

## 💬 User Preferences

- **Language:** Ukrainian (but comfortable with English)
- **Communication:** Explain technical decisions, use emojis in commits
- **Git workflow:** Always work on `claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF`
- **Testing:** Test locally before deploying
- **Autonomy:** Claude has full permissions (`--dangerously-skip-permissions`)

---

## 📞 Quick Links

- **GitHub:** https://github.com/SmmShaman/jobbot-norway-public
- **Netlify:** https://app.netlify.com/sites/jobbot-norway
- **Cloud Run:** https://console.cloud.google.com/run?project=jobbot-norway-442915
- **Supabase:** https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm

---

## ⚠️ Important Notes

1. **Worker runs on user's PC** - not in cloud
2. **Netlify auto-deploys** on git push
3. **Cloud Run** requires manual deploy (not set up for auto-deploy yet)
4. **Always read SESSION_CONTEXT.md** for full details before major changes
5. **Skyvern** must be running on user's PC (Docker, port 8000)

---

**Ready to continue?** Read `SESSION_CONTEXT.md` for complete context!
