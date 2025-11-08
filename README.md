# 🤖 JobBot Norway - Job Application Automation

> **Automated job searching, AI analysis, and application submission for Norwegian job market**

---

# ⚠️⚠️⚠️ FOR NEW CLAUDE CODE SESSION - READ THIS FIRST! ⚠️⚠️⚠️

## 🚨 CRITICAL: Update Repository IMMEDIATELY!

**If this README is shorter than 400 lines, you are on an OLD version!**

### DO THIS NOW (before reading anything else):

```bash
git fetch origin
git checkout claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
git pull origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
```

### Then read README.md again - it should be 500+ lines!

**After updating you will see:**
- ✅ Complete setup instructions
- ✅ SESSION_CONTEXT.md with full project history
- ✅ QUICK_START.md with quick reference
- ✅ Step-by-step guide what to do first
- ✅ Example first message to send user

**If you skip git pull, you will:**
- ❌ Miss critical files (SESSION_CONTEXT.md, QUICK_START.md, database/, web-app/, worker/)
- ❌ Not know what was already done
- ❌ Not know what to do next
- ❌ Waste time working on old code

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

### Step 2: Get API Keys from User
**⚠️ You DON'T have access to secrets! Ask user for:**
```
"Щоб продовжити роботу, мені потрібні API ключі. Будь ласка, надай:

1. SUPABASE_SERVICE_KEY (з https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/settings/api)
   - Копіювати 'service_role' key

2. Для Google Cloud (якщо потрібен деплой):
   - Або gcp-key.json файл
   - Або виконай: gcloud auth login (якщо gcloud вже налаштований)

3. Netlify автоматично деплоїться з git push ✅ (не потрібно)"
```

**ВАЖЛИВО:** Ключі треба просити щоразу в новій сесії - вони НЕ зберігаються між сесіями!

### Step 3: Read Context Files
After updating, these files will appear:
```bash
# Quick overview (read first!)
Read QUICK_START.md

# Full context (read for details)
Read SESSION_CONTEXT.md

# Project rules (always follow!)
Read CLAUDE.md
```

### Step 4: Understand Hybrid Architecture
**🔑 Критично важливо:**

**Ти (браузерна сесія Claude Code) маєш доступ до:**
- ✅ GitHub репозиторію
- ✅ Netlify (через git push - автоматично)
- ✅ Google Cloud Run (через gcloud CLI, якщо користувач надав ключі)
- ✅ Supabase (через API з ключами від користувача)

**Ти НЕ маєш доступу до:**
- ❌ Локального ПК користувача (~/jobbot-norway-public/worker/)
- ❌ Skyvern (localhost:8000 на ПК користувача)
- ❌ Docker на ПК користувача

**Для роботи з локальним Worker/Skyvern:**
Користувач використовує **окрему сесію "Claude Code Terminal"** на своєму ПК:
```bash
# На локальному ПК користувач запускає:
cd ~/jobbot-norway-public
claude --dangerously-skip-permissions

# Ця локальна сесія може:
# - Запускати Worker (python3 worker/worker.py)
# - Налаштовувати Skyvern
# - Виконувати git pull для оновлення
```

**Твоя роль (браузерна сесія):**
- Розробка Frontend/Backend коду
- Зміни в базі даних (SQL скрипти)
- Деплой на Netlify (git push)
- Деплой на Cloud Run (gcloud commands)
- Інструкції для користувача щодо локального Worker

### Step 5: Read Full Context
```bash
Read SESSION_CONTEXT.md  # Детальна історія
Read QUICK_START.md      # Швидкий довідник
```

### Step 6: YOUR FIRST ACTION - Start Here!

**🎯 ПЕРШЕ ЩО ТРЕБА ЗРОБИТИ:**

1. **Привітайся з користувачем українською:**
```
"Привіт! Я продовжую роботу над JobBot Norway.

Я прочитав SESSION_CONTEXT.md і розумію що ми зробили.

Перш ніж продовжити, скажи будь ласка:
1. Ти вже створив таблицю jobs в Supabase? (виконав database/jobs_table_schema_fixed.sql)
2. Worker працює на твоєму ПК зараз?
3. Якщо є якісь проблеми або питання - розкажи!

Після цього я продовжу з наступного пріоритетного завдання."
```

2. **Залежно від відповіді користувача:**

**Якщо jobs table НЕ створена:**
```
"Окей, давай створимо таблицю jobs в Supabase.

Відкрий: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new

Я зараз дам тобі SQL скрипт для виконання..."

Read database/jobs_table_schema_fixed.sql
# Показати користувачу і попросити виконати
```

**Якщо jobs table УЖЕ створена:**
```
"Чудово! Таблиця готова. Тепер давай протестуємо E2E flow:
1. Ти запустиш Worker на своєму ПК
2. Я допоможу налаштувати
3. Протестуємо сканування вакансій з FINN.no
4. Перевіримо що вони з'являються в Dashboard"
```

---

## 📊 Current Status (2025-11-08)

### ✅ Completed (Code Ready)
- ✅ Frontend deployed to Netlify (auto-deploy on push)
- ✅ Backend deployed to Google Cloud Run
- ✅ Supabase tables: users, settings, scan_tasks, monitoring_logs
- ✅ Worker code ready (`worker/worker.py`)
- ✅ Skyvern templates created
- ✅ Real-time Worker monitoring in Dashboard
- ✅ Comprehensive Jobs page with all metadata (30+ fields)
- ✅ SQL schema for jobs table with duplicate prevention

### ⏳ Pending (Requires User Action)
- ⏳ **CRITICAL:** User needs to create `jobs` table in Supabase
  - File: `database/jobs_table_schema_fixed.sql`
  - Execute in: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
  - **ASK USER IF DONE!**
- ⏳ Worker running on user's local PC
  - **ASK USER: "Worker працює зараз?"**

### 🎯 Next Tasks (After jobs table created)
1. ✅ Test end-to-end job scanning flow
2. Improve Skyvern templates (test with real FINN.no pages)
3. Add AI job relevance analysis (Phase 4)
4. Cover letter generation
5. Application automation

### 🚨 IMPORTANT: First Thing to Do
**Ask user about current status BEFORE continuing:**
- Is jobs table created? ✅ / ❌
- Is Worker running? ✅ / ❌
- Any errors or issues?

**Then proceed based on user's answer!**

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

## 🔐 Environment Variables & Setup

### Supabase Keys (де взяти?)

**Зайти в Supabase Dashboard:**
https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/settings/api

**Скопіювати:**
- `Project URL` → використовувати як `SUPABASE_URL`
- `anon public` key → для Frontend (`VITE_SUPABASE_ANON_KEY`)
- `service_role` key → для Backend і Worker (`SUPABASE_SERVICE_KEY`) ⚠️ СЕКРЕТНИЙ!

---

### Frontend (`web-app/.env`)

**Створити файл:**
```bash
cd web-app
cat > .env << 'EOF'
VITE_SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
VITE_SUPABASE_ANON_KEY=<скопіювати_з_supabase>
VITE_API_URL=https://jobbot-backend-255588880592.us-central1.run.app
EOF
```

**Netlify Dashboard (для продакшн):**
1. Відкрити: https://app.netlify.com/sites/jobbot-norway/configuration/env
2. Додати змінні:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_URL`

---

### Backend (Cloud Run)

**Налаштувати через gcloud CLI:**
```bash
gcloud run services update jobbot-backend \
  --region=us-central1 \
  --set-env-vars="SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co" \
  --set-env-vars="SUPABASE_SERVICE_KEY=<скопіювати_з_supabase>" \
  --set-env-vars="ALLOWED_ORIGINS=https://jobbot-norway.netlify.app"
```

**Або через Console:**
https://console.cloud.google.com/run/detail/us-central1/jobbot-backend/variables-and-secrets

---

### Worker (`worker/.env`)

**На локальному ПК користувача:**
```bash
cd ~/jobbot-norway-public/worker
cat > .env << 'EOF'
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=<скопіювати_з_supabase>
SKYVERN_API_URL=http://localhost:8000
EOF
```

**⚠️ ВАЖЛИВО:**
- `.env` файли в `.gitignore` - НЕ коммітити!
- `SUPABASE_SERVICE_KEY` має повний доступ - зберігати в секреті!
- Попросити користувача надати ключі якщо не знаєш

---

### Google Cloud Authentication (для деплою Backend)

**Варіант 1: gcloud CLI (якщо вже налаштований):**
```bash
# Перевірити чи є доступ:
gcloud auth list

# Якщо є активний акаунт - можна деплоїти:
gcloud run deploy jobbot-backend \
  --source ./backend \
  --region us-central1 \
  --project jobbot-norway-442915
```

**Варіант 2: Service Account Key (якщо gcloud не налаштований):**
```bash
# Попросити користувача надати gcp-key.json:
"Для деплою на Cloud Run потрібен файл gcp-key.json.
Будь ласка, надай його або виконай: gcloud auth login"

# Після отримання:
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-key.json
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
```

**Варіант 3: Попросити користувача задеплоїти вручну:**
```
"Я підготував зміни в backend/.
Будь ласка, виконай на своєму ПК:

cd ~/jobbot-norway-public
git pull
cd backend
gcloud run deploy jobbot-backend --source . --region us-central1"
```

---

### Netlify Deployment (автоматичний!)

**✅ Не потрібні ключі!** Netlify автоматично деплоїться з git push.

**Що відбувається:**
```bash
git push origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
→ GitHub webhook → Netlify
→ Автоматично: npm install → npm run build → deploy
→ Live: https://jobbot-norway.netlify.app
```

**Для зміни env vars (якщо потрібно):**
Попросити користувача зайти в:
https://app.netlify.com/sites/jobbot-norway/configuration/env

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

**⚠️ Worker працює ТІЛЬКИ на локальному ПК користувача!**

**Опція 1: Користувач запускає вручну**
```bash
cd ~/jobbot-norway-public/worker
pip install -r requirements.txt
python3 worker.py
```

**Опція 2: Через локальну сесію Claude Code Terminal**
Користувач може запустити Claude Code локально для автоматизації:
```bash
# На локальному ПК:
cd ~/jobbot-norway-public
claude --dangerously-skip-permissions

# В локальній сесії Claude може виконувати команди:
# - Setup Worker
# - Налаштувати Skyvern
# - Запустити Docker
# - Виконати git pull для оновлень
```

**Приклад інструкцій для локальної сесії Claude:**
```
"Виконай setup Worker:
1. cd worker
2. pip install -r requirements.txt
3. Створи .env файл з ключами
4. Перевір що Skyvern працює: curl http://localhost:8000/api/v1/health
5. Запусти Worker: python3 worker.py"
```

**Skyvern + Docker (локально):**
```bash
# Перевірити чи працює:
docker ps | grep skyvern

# Запустити якщо не працює:
docker-compose up -d skyvern

# Перевірити доступність:
curl http://localhost:8000/api/v1/health
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

## ⚡ Quick Start Checklist for New Session

**Copy-paste this checklist in your first message:**

```
[ ] git pull origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
[ ] Read SESSION_CONTEXT.md
[ ] Read QUICK_START.md
[ ] Ask user for SUPABASE_SERVICE_KEY (if needed)
[ ] Ask user: "Ти вже створив jobs table в Supabase?"
[ ] Ask user: "Worker працює зараз на твоєму ПК?"
[ ] Based on answers → proceed with next task
```

---

## 💬 Example First Message (для нової сесії)

**Скопіюй це і відправ як перше повідомлення:**

```
Привіт! Я продовжую роботу над JobBot Norway. 👋

Я щойно:
✅ Оновив репозиторій (git pull)
✅ Прочитав SESSION_CONTEXT.md
✅ Зрозумів що ми вже зробили

Перш ніж продовжити, скажи будь ласка:

1. **Таблиця jobs в Supabase:**
   - Ти вже виконав SQL з database/jobs_table_schema_fixed.sql?
   - Або треба це зробити зараз?

2. **Worker на локальному ПК:**
   - Він зараз працює?
   - Або треба його запустити?

3. **API ключі:**
   - Якщо потрібен доступ до Supabase для роботи, дай мені SUPABASE_SERVICE_KEY

4. **Є якісь проблеми чи питання?**

Розкажи статус, і я одразу продовжу з потрібного місця! 🚀
```

---

## ⚡ Quick Commands

```bash
# Update repository
git pull origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF

# Check status
git status
git log --oneline -5

# Read context
Read SESSION_CONTEXT.md
Read QUICK_START.md

# Run locally
cd web-app && npm run dev          # Frontend
cd backend && uvicorn app.main:app --reload  # Backend
cd worker && python3 worker.py     # Worker (on user's PC)
```

---

**Last Updated:** 2025-11-08
**Status:** ✅ All components deployed and working
**Next:** Create jobs table in Supabase, test E2E flow

---

*Ready for AI-assisted development! 🚀*
