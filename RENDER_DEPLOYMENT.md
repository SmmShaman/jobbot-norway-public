# 🎨 Render Backend Deployment Guide

## Чому Render?

✅ **Безкоштовний tier** - $0/month (750 годин)
✅ **Простіше ніж Railway** - GUI-based setup
✅ **Auto-deploy з GitHub** - push → auto-redeploy
✅ **EU datacenter** - Frankfurt (близько до Норвегії)
✅ **Не потрібна кредитка** для free tier

---

## 🚀 Quick Start (5 хвилин)

### Крок 1: Запусти helper script

```bash
cd backend
./deploy_render.sh
```

Скрипт проведе тебе через весь процес!

**АБО** слідуй мануальній інструкції нижче ↓

---

## 📋 Manual Deployment (Покроково)

### Крок 1: Створи Render Account (1 хвилина)

1. Йди на: https://dashboard.render.com
2. Sign up з GitHub (рекомендую)
3. Підтверди email

✅ Готово! Не потрібна кредитка.

---

### Крок 2: Підключи GitHub Repository (2 хвилини)

1. **Dashboard** → **New +** → **Web Service**

2. Підключи GitHub:
   - "Configure account"
   - Select repositories
   - Вибери: `SmmShaman/jobbot-norway-public`
   - Install & Authorize

3. Вибери repository зі списку:
   - `SmmShaman/jobbot-norway-public`
   - Click **Connect**

---

### Крок 3: Налаштуй Web Service (3 хвилини)

#### Basic Settings

| Setting | Value |
|---------|-------|
| **Name** | `jobbot-backend` (або будь-яке ім'я) |
| **Region** | Frankfurt (EU Central) - найближче до Норвегії |
| **Branch** | `claude/netlify-ui-011CUqJXNw4wkoYPis8TAkxF` |
| **Root Directory** | `backend` |
| **Runtime** | Python 3 (auto-detected) |

#### Build & Deploy

| Setting | Value |
|---------|-------|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

#### Instance Type

Вибери: **Free** ($0/month)

**Free tier включає:**
- 750 hours/month
- 512 MB RAM
- Shared CPU
- Auto-sleep після 15 хв неактивності

**⚠️ Примітка:** Service засипає після 15 хв. Перший запит після сну займе ~30-60 секунд (cold start).

#### Advanced Settings

**Health Check Path:** `/health`

**Environment Variables:** Додамо на наступному кроці ↓

---

### Крок 4: Додай Environment Variables (3 хвилини)

Перед створенням сервісу додай змінні:

#### Required Variables

```bash
# Supabase
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=твій-service-key
SUPABASE_JWT_SECRET=твій-jwt-secret

# Azure OpenAI (ВАЖЛИВО: використовуй свої ключі з backend/.env!)
AZURE_OPENAI_ENDPOINT=https://твій-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=твій-ключ
AZURE_OPENAI_DEPLOYMENT=твоє-deployment-ім'я
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Security
ENCRYPTION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
JWT_SECRET=jobbot_norway_secret_key_2024

# API Settings
API_HOST=0.0.0.0
API_PORT=10000
DEBUG=false

# CORS (ВАЖЛИВО: додай свій Netlify URL!)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://твій-netlify-сайт.netlify.app
```

**Де взяти ключі?**
- Всі значення є в `backend/.env`
- Або запусти `./deploy_render.sh` - він покаже всі змінні

**Як додати в Render:**
1. В формі створення сервісу → Environment
2. Кожна змінна: Key = Value
3. Або використай "Bulk Edit" та вставити все разом

---

### Крок 5: Create Web Service (1 хвилина)

1. Натисни **Create Web Service**
2. Render почне build
3. Чекай 2-3 хвилини
4. Status зміниться на **Live** 🟢

---

### Крок 6: Скопіюй Service URL (30 секунд)

Після deployment твій URL буде:
```
https://jobbot-backend.onrender.com
```

**АБО** твоє custom ім'я:
```
https://твоє-ім'я.onrender.com
```

**Скопіюй цей URL** - він потрібен для наступного кроку!

---

### Крок 7: Перевір Health Check (30 секунд)

```bash
curl https://твій-render-url.onrender.com/health
```

**Має відповісти:**
```json
{
  "status": "healthy"
}
```

**Якщо помилка:**
- Чекай ще 1-2 хвилини (service стартує)
- Перевір логи: Dashboard → твій service → Logs

---

### Крок 8: Оновити Netlify (2 хвилини)

#### Варіант A: Dashboard (простіше)

1. Йди: https://app.netlify.com
2. Твій сайт → **Site settings** → **Environment variables**
3. Знайди `VITE_API_URL`
4. **Edit** → Вставити Render URL
5. **Save**
6. **Deploys** → **Trigger deploy**

#### Варіант B: CLI (швидше)

```bash
netlify env:set VITE_API_URL https://твій-render-url.onrender.com
netlify deploy --prod
```

---

### Крок 9: Test End-to-End (2 хвилини)

1. Відкрий свій Netlify сайт
2. Login: `test@jobbot.no` / `Test123456`
3. **Dashboard** → Click **"Scan Jobs Now"**
4. Чекай 30-60 секунд (cold start якщо service спав)
5. Має запрацювати! 🎉

---

## 🔄 Auto-Deploy з GitHub

Render автоматично redeploy при кожному push!

**Workflow:**
```
1. Змінюєш код локально
2. git commit && git push
3. Render визначає зміни в branch
4. Автоматично rebuilds backend
5. Новий deployment live за 2-3 хвилини
```

**Налаштування:**
- Dashboard → твій service → Settings → Build & Deploy
- **Auto-Deploy**: Yes (за замовчуванням)

---

## 📊 Monitoring & Logs

### Real-time Logs

**Dashboard → твій service → Logs**

Бачиш:
- Build logs
- Runtime logs
- Error messages
- API requests

### Metrics

**Dashboard → твій service → Metrics**

Відстежуй:
- Response time
- Memory usage
- CPU usage
- HTTP status codes

---

## 💰 Cost Breakdown

### Free Tier (Рекомендую для старту)

- **Price**: $0/month
- **Hours**: 750/month (достатньо для 1 сервісу 24/7)
- **RAM**: 512 MB
- **CPU**: Shared
- **Sleep**: Після 15 хв неактивності
- **Wake up**: 30-60 секунд

**Ідеально для:**
- Testing
- Development
- Low-traffic projects
- MVP

### Starter Tier ($7/month)

- **No sleep** - працює 24/7
- 512 MB RAM
- Shared CPU
- Faster response time

### Standard Tier ($25/month)

- 2 GB RAM
- 1 CPU
- Production-ready
- Zero downtime deploys

**Порівняння з Railway:**
- Railway: $5-10/month (немає free tier)
- Render: $0/month (free tier) або $7/month (starter)

---

## ⚠️ Free Tier Limitations

### Sleep After Inactivity

**Проблема:**
- Service засипає після 15 хв без requests
- Перший request після сну: 30-60 секунд cold start

**Рішення 1: Upgrade до Starter ($7/month)**
- No sleep
- Працює 24/7

**Рішення 2: Ping Service (залишається на Free)**

Створи cron job який ping кожні 10 хвилин:

```bash
# Використай cron-job.org (безкоштовно)
# URL: https://твій-render-url.onrender.com/health
# Interval: Every 10 minutes
```

**Рішення 3: Прийняти cold start**
- Якщо користувачів мало
- 30-60 сек очікування прийнятне
- Безкоштовно!

---

## 🔒 Security Best Practices

### Environment Variables

✅ **DO:**
- Зберігай secrets в Render env vars
- Використовуй різні ключі для dev/prod
- Регулярно rotate secrets

❌ **DON'T:**
- Commit secrets в git
- Share secrets publicly
- Use same keys for multiple projects

### CORS Configuration

Додай **тільки** свій Netlify domain:

```bash
CORS_ORIGINS=https://твій-сайт.netlify.app
```

Не використовуй `*` (wildcard) в production!

---

## 🐛 Troubleshooting

### Build Fails

**Symptom:** Build failed in Render Dashboard

**Check:**
```bash
# Render Dashboard → Logs → Build tab
```

**Common issues:**
- Missing dependencies in `requirements.txt`
- Python version mismatch
- Syntax errors in code

**Fix:**
```bash
# Test locally first
cd backend
pip install -r requirements.txt
python -m pytest
```

### Service Crashes

**Symptom:** Service shows as "Down" або постійні restarts

**Check logs:**
```
Dashboard → Logs → Runtime
```

**Common issues:**
- Missing environment variables
- Supabase connection error
- Azure OpenAI key invalid
- Port binding error

**Fix:**
1. Verify all env vars set correctly
2. Test connections locally
3. Check Supabase/Azure quotas

### CORS Errors

**Symptom:** Frontend shows CORS error in browser console

**Error:**
```
Access to fetch at 'https://...' from origin 'https://...' has been blocked by CORS
```

**Fix:**
```bash
# Render Dashboard → Environment
# Update CORS_ORIGINS with your Netlify URL
CORS_ORIGINS=https://твій-netlify-сайт.netlify.app

# Then redeploy:
Dashboard → Manual Deploy → Deploy latest commit
```

### Slow Response (Cold Start)

**Symptom:** Перший request після неактивності займає 30-60 секунд

**Причина:** Free tier - service засипає після 15 хв

**Options:**
1. **Accept it** (безкоштовно, OK для low traffic)
2. **Setup ping** (cron-job.org ping кожні 10 хв)
3. **Upgrade to Starter** ($7/month - no sleep)

### Database Connection Issues

**Symptom:** 500 errors, "could not connect to Supabase"

**Check:**
```bash
# Test locally
cd backend
./start_dev.sh
# Try making API request
```

**Fix:**
- Verify `SUPABASE_URL` correct
- Verify `SUPABASE_SERVICE_KEY` correct
- Check Supabase project is active
- Check database RLS policies

---

## 📈 Scaling

### When to upgrade from Free?

Upgrade коли:
- ❌ Cold starts annoying users
- ❌ Need 24/7 availability
- ❌ Traffic > 750 hours/month
- ❌ Need more RAM (>512 MB)

### Upgrade Path

**Free → Starter ($7/month):**
```
Dashboard → Settings → Instance Type → Starter
```

**Starter → Standard ($25/month):**
```
Dashboard → Settings → Instance Type → Standard
```

---

## 🎯 Next Steps

After successful deployment:

1. ✅ Test all Settings operations
2. ✅ Upload resume
3. ✅ Add NAV search URLs
4. ✅ Run "Scan Jobs Now"
5. ✅ Check Jobs page for results
6. ✅ Setup Telegram notifications (optional)
7. 🔮 Consider ping service if cold starts annoying
8. 🔮 Monitor usage in Render Dashboard

---

## 📚 Additional Resources

**Render Docs:**
- Getting Started: https://render.com/docs
- Python Guide: https://render.com/docs/deploy-fastapi
- Environment Variables: https://render.com/docs/environment-variables
- Troubleshooting: https://render.com/docs/troubleshooting

**Render Community:**
- Community Forum: https://community.render.com
- Status Page: https://status.render.com

**JobBot Resources:**
- API Testing: `backend/API_TESTING.md`
- Backend Docs: `backend/README.md`
- Quick Start: `START_HERE.md`

---

## 🎉 Summary

**You now have:**
- ✅ Backend deployed on Render (FREE!)
- ✅ Auto-deploy з GitHub
- ✅ Health monitoring
- ✅ EU datacenter (close to Norway)
- ✅ 750 hours/month (достатньо для 24/7)

**Total monthly cost:**
- Frontend (Netlify): $0
- Backend (Render): $0
- Database (Supabase): $0
- Azure OpenAI: ~$1-5 (pay-per-use)

**Grand Total: $1-5/month!** 🎉

---

**Made with ❤️ for job seekers in Norway** 🇳🇴

**Render - це найкращий безкоштовний hosting для Python backend!**
