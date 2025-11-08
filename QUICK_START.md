# 🚀 Quick Start for New Claude Code Session

## ⚠️ CRITICAL FIRST STEP: Check Your Branch!

**You MUST be on:** `claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu` (Worker v2)

### Quick Check:
```bash
git branch  # Should show * claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu
ls database/finn_link_extractor_function.sql  # Should exist
ls worker/worker_v2.py  # Should exist
```

### If you're on wrong branch:
```bash
git fetch origin
git checkout claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu
git pull origin claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu
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

- **Branch:** `claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu` (Worker v2!)
- **Latest commit:** `156c72c` - Add quick install SQL guide
- **Frontend:** https://jobbot-norway.netlify.app (auto-deploys)
- **Backend:** https://jobbot-backend-255588880592.us-central1.run.app
- **Database:** Supabase (ptrmidlhfdbybxmyovtm)
- **Worker v2:** Runs on user's PC at `~/jobbot-norway-public/worker/worker_v2.py`
- **New Architecture:** Link extraction (regex) → Individual Skyvern processing

---

## ✅ What's Done

- ✅ Frontend deployed (Netlify)
- ✅ Backend deployed (Cloud Run)
- ✅ Database setup (Supabase)
- ✅ Worker v1 running on local PC
- ✅ **Worker v2 with link extraction** (NEW!)
- ✅ Skyvern integrated (Docker, localhost:8000)
- ✅ Real-time Worker monitoring in Dashboard
- ✅ Comprehensive Jobs page with all metadata
- ✅ Duplicate prevention (UNIQUE constraint on user_id + url)
- ✅ SQL functions for link extraction (`extract_finn_job_links`, `create_jobs_from_finn_links`)

---

## 🎯 Next Priority

**IMMEDIATE:**
1. Install SQL functions in Supabase
   - File: `database/finn_link_extractor_function.sql`
   - Quick guide: `QUICK_INSTALL_SQL.md`
   - Execute in: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new

2. Test Worker v2
   - Run: `python3 worker/worker_v2.py`
   - Create scan task from Dashboard
   - Verify jobs appear instantly!

**NEXT TASKS:**
3. Test end-to-end job scanning flow with Worker v2
4. Improve Skyvern templates for better data extraction
5. Add AI job relevance analysis (Phase 4)
6. Cover letter generation
7. Application automation

---

## 🗂️ Key Files to Review

```bash
SESSION_CONTEXT.md                        # Full context (read this!)
CLAUDE.md                                 # Project rules (always follow!)
MIGRATION_V2.md                           # Worker v2 migration guide
QUICK_INSTALL_SQL.md                      # Quick SQL installation
database/jobs_table_schema_fixed.sql      # Jobs table schema
database/finn_link_extractor_function.sql # SQL functions for v2
worker/worker_v2.py                       # NEW Worker v2 (use this!)
worker/worker.py                          # Old Worker v1
worker/README_V2.md                       # Worker v2 documentation
worker/skyvern_templates/                 # Skyvern scraping templates
web-app/src/pages/Jobs.tsx                # Jobs display page
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

# Run worker v2 (on user's PC) - RECOMMENDED
cd ~/jobbot-norway-public/worker && python3 worker_v2.py

# Or old worker v1
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
- **Git workflow:** Always work on `claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu` (Worker v2 branch)
- **Testing:** Test locally before deploying
- **Autonomy:** Claude has full permissions (`--dangerously-skip-permissions`)
- **Current focus:** Worker v2 implementation and testing

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
