# ⚡ Render Quick Setup - З GitHub Action

## 🎯 Що маємо:

✅ Render account створено
✅ Render API Key додано в GitHub Secrets
✅ GitHub Action створено (автоматично deploy при push)

---

## 📋 Крок 3: Створи Web Service в Render (ОДИН РАЗ - 3 хвилини)

Це треба зробити **тільки один раз**. Після цього GitHub Action буде автоматично оновлювати сервіс.

### 3.1 Створи Service

1. **Йди на:** https://dashboard.render.com

2. **Клікни:** "New +" (зверху справа) → **"Web Service"**

3. **Підключи GitHub repository:**
   - Якщо вже підключений: вибери `SmmShaman/jobbot-norway-public`
   - Якщо НЕ підключений: клікни "Configure account" → вибери репозиторій

4. **Заповни форму:**

   **Name:** `jobbot-backend` (або будь-яка назва)

   **Region:** `Frankfurt (EU Central)` ← Вибери це (близько до Норвегії)

   **Branch:** `claude/netlify-ui-011CUqJXNw4wkoYPis8TAkxF`

   **Root Directory:** `backend` ← ВАЖЛИВО!

   **Runtime:** Python 3 (має визначитися автоматично)

   **Build Command:** `pip install -r requirements.txt`

   **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Instance Type:**
   - Вибери **"Free"** ($0/month)

6. **Advanced → Health Check Path:**
   - Введи: `/health`

7. **Прокрути вниз** до секції **"Environment Variables"**

---

### 3.2 Додай Environment Variables

**⚠️ ВАЖЛИВО:** Додай всі ці змінні!

Клікни **"Add Environment Variable"** для кожної:

```bash
# Supabase
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0cm1pZGxoZmRieWJ4bXlvdnRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjQzNDc0OSwiZXhwIjoyMDc4MDEwNzQ5fQ.46uj0VMvxoWvApNTDdifgpfkbDv5fBhU3GfUjIGIwtU
SUPABASE_JWT_SECRET=your-jwt-secret-here

# Azure OpenAI (використовуй свої значення з backend/.env!)
AZURE_OPENAI_ENDPOINT=твій-endpoint
AZURE_OPENAI_KEY=твій-ключ
AZURE_OPENAI_DEPLOYMENT=твоє-deployment
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Security
ENCRYPTION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
JWT_SECRET=jobbot_norway_secret_key_2024

# API
API_HOST=0.0.0.0
API_PORT=10000
DEBUG=false

# CORS (ДОДАЙ СВІЙ NETLIFY URL!)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://твій-netlify-сайт.netlify.app
```

**💡 Порада:** Використовуй "Bulk Edit" → вставити все разом!

---

### 3.3 Create Service

8. **Клікни** "Create Web Service" (зелена кнопка внизу)

9. **Чекай 2-3 хвилини** поки Render build backend

10. **Статус зміниться на** 🟢 **"Live"**

---

### 3.4 Скопіюй Service URL

Після deployment побачиш URL:

```
https://jobbot-backend-abc123.onrender.com
```

**📋 СКОПІЮЙ ЦЕЙ URL!** Він потрібен для наступного кроку.

---

### 3.5 Отримай Service ID

Тепер треба отримати Service ID для GitHub Action:

1. **В Render Dashboard** → твій service `jobbot-backend`

2. **Подивись на URL в браузері**, він виглядає так:
   ```
   https://dashboard.render.com/web/srv-abc123xyz
                                      ^^^^^^^^^^^
                                      Це Service ID
   ```

3. **Service ID** - це частина після `srv-`, наприклад: `srv-abc123xyz`

4. **📋 СКОПІЮЙ Service ID!**

---

## 📋 Крок 4: Додай Service ID в GitHub Secrets (30 секунд)

1. **Йди на GitHub:** https://github.com/SmmShaman/jobbot-norway-public

2. **Settings** → **Secrets and variables** → **Actions**

3. **"New repository secret"**

4. **Заповни:**
   - **Name:** `RENDER_SERVICE_ID`
   - **Secret:** `srv-abc123xyz` (твій Service ID)

5. **"Add secret"**

✅ Готово!

---

## 📋 Крок 5: Оновити Netlify з Render URL (1 хвилина)

Тепер підключи frontend до backend:

### Варіант A: Netlify Dashboard

1. https://app.netlify.com → твій сайт

2. **Site settings** → **Environment variables**

3. **Edit** `VITE_API_URL`:
   - Нове значення: `https://jobbot-backend-abc123.onrender.com` (твій Render URL)

4. **Save**

5. **Deploys** → **Trigger deploy**

### Варіант B: Netlify CLI

```bash
netlify env:set VITE_API_URL https://твій-render-url.onrender.com
netlify deploy --prod
```

---

## 🎉 ГОТОВО! Тепер все працює автоматично!

### Що відбувається далі:

```
Ти → git push → GitHub
                  ↓
            [GitHub Action автоматично]
                  ↓
            Render redeploy backend ✅
```

### Твій workflow НАЗАВЖДИ:

```bash
# 1. Змінюєш код
nano backend/app/main.py

# 2. Commit і push
git add .
git commit -m "Покращив backend"
git push

# 3. ⏰ Чекаєш 2-3 хвилини
# GitHub Action автоматично deploy на Render

# 4. 🎉 Готово! Backend оновлено!
```

**Більше НІКОЛИ не треба заходити в Render Dashboard для deployment!**

---

## 🧪 Тест системи (2 хвилини)

### 1. Перевір Backend

```bash
curl https://твій-render-url.onrender.com/health
```

**Має показати:**
```json
{"status": "healthy"}
```

⚠️ **Якщо це перший запит** після deployment, чекай 30-60 секунд (cold start).

### 2. Перевір API Docs

Відкрий в браузері:
```
https://твій-render-url.onrender.com/docs
```

Має з'явитися FastAPI Swagger UI з усіма endpoints!

### 3. Перевір Frontend + Backend

1. **Відкрий:** https://твій-netlify-сайт.netlify.app

2. **Login:** `test@jobbot.no` / `Test123456`

3. **Тести:**
   - ✅ Dashboard → "Scan Jobs Now" → працює!
   - ✅ Settings → Upload Resume → працює!
   - ✅ Settings → Add NAV URLs → працює!
   - ✅ Jobs page → Бачиш вакансії → працює!

🎉 **Якщо все працює - СИСТЕМА ГОТОВА!**

---

## 📊 Моніторинг

### GitHub Actions

Дивись статус deployments:

1. GitHub repo → **"Actions"** tab
2. Побачиш історію всіх deployments
3. Зелений ✅ = успішно, Червоний ❌ = помилка

### Render Dashboard

Дивись логи:

1. https://dashboard.render.com
2. Твій service → **"Logs"** tab
3. Real-time логи backend

---

## 🐛 Troubleshooting

### GitHub Action fails

**Перевір:**
1. GitHub → Actions → дивись error message
2. Можливо неправильний `RENDER_SERVICE_ID`
3. Або API Key expired

**Fix:**
- Перевір що Service ID правильний
- Regenerate Render API Key якщо треба

### Backend не відповідає

**Перевір:**
1. Render Dashboard → Logs
2. Можливо environment variables неправильні
3. Або cold start (чекай 60 сек)

**Fix:**
- Render Dashboard → Environment → перевір всі змінні
- Manual Deploy → Deploy latest commit

### Frontend не може з'єднатися

**Перевір:**
1. Netlify env vars → `VITE_API_URL` правильний?
2. Render env vars → `CORS_ORIGINS` містить Netlify URL?

**Fix:**
```bash
# Netlify
netlify env:set VITE_API_URL https://correct-render-url.onrender.com

# Render Dashboard
# Update CORS_ORIGINS → add Netlify URL
# Manual Deploy
```

---

## 💰 Вартість

**Все безкоштовно:**
- ✅ Netlify: Free tier
- ✅ Render: Free tier (750 hours/month)
- ✅ GitHub Actions: Free tier (2000 minutes/month)
- ✅ Supabase: Free tier
- 💳 Azure OpenAI: ~$1-5/month (pay-per-use)

**Total: $1-5/month!** 🎉

---

## 🎯 Наступні кроки

Після успішного setup:

1. ✅ Завантажити своє резюме
2. ✅ Додати реальні NAV search URLs
3. ✅ Запустити "Scan Jobs Now"
4. ✅ Переглянути знайдені вакансії
5. ✅ Налаштувати Telegram notifications

**Система готова до використання!** 🚀

---

**Made with ❤️ - автоматичний deployment!**
