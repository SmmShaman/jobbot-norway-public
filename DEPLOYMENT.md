# 🚀 JobBot Norway - Deployment Guide

## 📋 Quick Start Checklist

- [x] Supabase project created
- [x] Environment variables configured
- [ ] SQL migration run
- [ ] Storage buckets created
- [ ] Netlify connected
- [ ] Frontend deployed
- [ ] Backend deployed

---

## 🗄️ Крок 1: Налаштування Supabase Database

### Автоматичний спосіб (рекомендується):

```bash
# З кореня проекту:
python3 setup_database.py
```

Скрипт покаже інструкції для:
1. Запуску SQL міграції
2. Створення Storage buckets

### Ручний спосіб:

#### 1.1 Запуск SQL міграції

1. Відкрий: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql
2. Натисни **"New Query"**
3. Скопіюй весь вміст файлу: `supabase/migrations/001_initial_schema.sql`
4. Вставь в SQL Editor
5. Натисни **"RUN"** ▶️
6. Перевір результат - має бути успішно створено 6 таблиць

**Перевірка:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Має показати:
- applications
- cover_letters
- jobs
- monitoring_logs
- profiles
- user_settings

#### 1.2 Створення Storage Buckets

**Відкрий:** https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/storage/buckets

**Bucket 1: resumes**
```
Name: resumes
Public: NO (Private)
File size limit: 10 MB
Allowed MIME types: application/pdf
```

Після створення додай Policy:
```sql
-- В Storage → resumes → Policies → New Policy
CREATE POLICY "Users manage own resumes"
ON storage.objects FOR ALL
TO authenticated
USING (
  bucket_id = 'resumes' AND
  auth.uid()::text = (storage.foldername(name))[1]
)
WITH CHECK (
  bucket_id = 'resumes' AND
  auth.uid()::text = (storage.foldername(name))[1]
);
```

**Bucket 2: cover-letters**
```
Name: cover-letters
Public: NO (Private)
File size limit: 5 MB
Allowed MIME types: application/pdf, text/plain
```

**Bucket 3: screenshots**
```
Name: screenshots
Public: NO (Private)
File size limit: 5 MB
Allowed MIME types: image/png, image/jpeg
```

---

## 🌐 Крок 2: Налаштування Netlify

### 2.1 Підключення GitHub репозиторію

1. Відкрий: https://app.netlify.com
2. Натисни **"Add new site"** → **"Import an existing project"**
3. Вибери **"Deploy with GitHub"**
4. Авторизуй Netlify доступ до GitHub
5. Вибери репозиторій: **`SmmShaman/jobbot-norway-public`**

### 2.2 Налаштування Build

**Основні налаштування:**
```
Branch to deploy: claude/netlify-ui-011CUqJXNw4wkoYPis8TAkxF
Base directory: web-app
Build command: npm install && npm run build
Publish directory: web-app/dist
```

### 2.3 Environment Variables

В Netlify Dashboard → Site settings → Environment variables → Add:

```env
VITE_SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0cm1pZGxoZmRieWJ4bXlvdnRtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0MzQ3NDksImV4cCI6MjA3ODAxMDc0OX0.rdOIJ9iMnbz5uxmGrtxJxb0n1cwf6ee3ppz414IaDWM
VITE_API_URL=https://твій-backend.railway.app
```

(VITE_API_URL поки залиш як `https://example.com`, оновимо після deploy backend)

### 2.4 Deploy!

Натисни **"Deploy site"**

Після deploy (2-3 хвилини) отримаєш URL:
```
https://твій-сайт.netlify.app
```

### 2.5 (Опціонально) Custom Domain

Site settings → Domain management → Add custom domain

---

## 🐍 Крок 3: Налаштування Backend (Railway)

### 3.1 Створення проекту на Railway

1. Відкрий: https://railway.app
2. Натисни **"New Project"**
3. Вибери **"Deploy from GitHub repo"**
4. Вибери **`SmmShaman/jobbot-norway-public`**
5. Railway auto-detect Dockerfile

### 3.2 Налаштування Root Directory

В Railway project settings:
```
Root Directory: backend
```

### 3.3 Environment Variables

Додай всі змінні з `backend/.env`:

```env
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_from_supabase_dashboard
AZURE_OPENAI_ENDPOINT=https://ai-stuardbmw0250ai913492610772.cognitiveservices.azure.com
AZURE_OPENAI_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
DEBUG=false
CORS_ORIGINS=https://твій-сайт.netlify.app,http://localhost:3000
```

**NOTE:** Real credentials are configured locally in `backend/.env` (not committed to git)

### 3.4 Deploy Backend

Railway автоматично задеплоїть після push до GitHub.

Після deploy отримаєш URL:
```
https://твій-backend.up.railway.app
```

### 3.5 Оновлення Frontend ENV

Повернись в Netlify:
1. Site settings → Environment variables
2. Оновіть `VITE_API_URL` на Railway URL
3. Trigger redeploy: Deploys → Trigger deploy

---

## 🧪 Крок 4: Локальне тестування

### 4.1 Frontend

```bash
cd web-app

# Встановлення залежностей
npm install

# Запуск dev server
npm run dev
```

Відкрий: http://localhost:3000

### 4.2 Backend

```bash
cd backend

# Створення virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Встановлення залежностей
pip install -r requirements.txt

# Запуск dev server
uvicorn app.main:app --reload --port 8000
```

API доступне на: http://localhost:8000

**Перевірка API:**
```bash
curl http://localhost:8000/health
# Має повернути: {"status":"healthy"}
```

---

## ✅ Крок 5: Перевірка роботи

### 5.1 Тест реєстрації

1. Відкрий frontend URL
2. Натисни "Sign Up"
3. Зареєструйся з email та password
4. Перевір що з'явився в Supabase:
   - Dashboard → Authentication → Users
   - Dashboard → Table Editor → profiles

### 5.2 Тест Dashboard

1. Після логіна має відкритись Dashboard
2. Перевір що відображається:
   - Статистика (поки всі 0)
   - Кнопка "Scan Jobs Now"
   - Quick Start Guide

### 5.3 Тест Settings

1. Перейди в Settings
2. Завантаж резюме (PDF)
3. Перевір що файл з'явився в:
   - Supabase → Storage → resumes

---

## 🔄 Автоматичний Deploy

### Після налаштування:

**GitHub → Netlify (Frontend):**
```bash
git add .
git commit -m "Update frontend"
git push
# Netlify автоматично задеплоїть через 2-3 хвилини
```

**GitHub → Railway (Backend):**
```bash
git add .
git commit -m "Update backend"
git push
# Railway автоматично задеплоїть через 3-5 хвилин
```

---

## 🔧 Troubleshooting

### Frontend не запускається:

```bash
# Видали node_modules та reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend помилки:

```bash
# Перевір environment variables
cat backend/.env

# Перевір Supabase connection
python3 -c "from supabase import create_client; print('OK')"
```

### Netlify build fails:

1. Перевір Build logs в Netlify Dashboard
2. Переконайся що `web-app` має всі файли
3. Перевір Environment Variables

### Railway deploy fails:

1. Перевір Logs в Railway Dashboard
2. Переконайся що `backend/Dockerfile` існує
3. Перевір Environment Variables

---

## 📞 Потрібна допомога?

- 📖 [Architecture](ARCHITECTURE.md)
- 📋 [README](README_WEB.md)
- 💬 GitHub Issues

---

✅ **Готово! Система налаштована!** 🎉
