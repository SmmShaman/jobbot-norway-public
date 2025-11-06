# 🚀 ONE-COMMAND DEPLOYMENT

## Автоматичний deployment за 5 хвилин

### Передумови

Тобі потрібно мати:
- ✅ GitHub account (вже є)
- ✅ Netlify account (вже є - frontend працює)
- ⚠️ Railway account (створи тут: https://railway.app)

---

## Варіант 1: Повністю Автоматичний (CLI)

### Крок 1: Встанови Railway CLI

**macOS:**
```bash
brew install railway
```

**Linux/WSL:**
```bash
npm i -g @railway/cli
```

**Windows:**
```bash
npm i -g @railway/cli
```

### Крок 2: Авторизуйся в Railway

```bash
railway login
```

Відкриється браузер → Authorize CLI → Готово!

### Крок 3: Запусти автоматичний deployment

```bash
cd backend
./deploy_railway.sh
```

**Скрипт автоматично:**
- ✅ Створить Railway project
- ✅ Прив'яже до GitHub repo
- ✅ Завантажить всі env vars з `.env`
- ✅ Задеплоїть backend
- ✅ Покаже URL

### Крок 4: Оновити Netlify

Після deployment отримаєш Railway URL. Оновити Netlify:

**Автоматично (якщо є Netlify CLI):**
```bash
netlify env:set VITE_API_URL https://твій-railway-url.railway.app
netlify deploy --prod
```

**Вручну:**
1. https://app.netlify.com → Твій сайт
2. Site settings → Environment variables
3. Оновити `VITE_API_URL` → Railway URL
4. Deploys → Trigger deploy

---

## Варіант 2: Через Railway Dashboard (GUI)

### Крок 1: Створи Railway Project

1. Йди на: https://railway.app
2. **New Project**
3. **Deploy from GitHub repo**
4. Authorize GitHub
5. Вибери: `SmmShaman/jobbot-norway-public`
6. Branch: `claude/netlify-ui-011CUqJXNw4wkoYPis8TAkxF`

### Крок 2: Налаштуй Project

1. **Root Directory**: `backend`
2. Railway автоматично визначить Python

### Крок 3: Додай Environment Variables

Railway → Variables → Raw Editor → Вставити:

```bash
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0cm1pZGxoZmRieWJ4bXlvdnRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjQzNDc0OSwiZXhwIjoyMDc4MDEwNzQ5fQ.46uj0VMvxoWvApNTDdifgpfkbDv5fBhU3GfUjIGIwtU
SUPABASE_JWT_SECRET=your-jwt-secret-here
AZURE_OPENAI_ENDPOINT=<твій-endpoint>
AZURE_OPENAI_KEY=<твій-ключ>
AZURE_OPENAI_DEPLOYMENT=<твоє-deployment-ім'я>
AZURE_OPENAI_API_VERSION=2024-12-01-preview
ENCRYPTION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
JWT_SECRET=jobbot_norway_secret_key_2024
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://jobbotnetlify.netlify.app
```

**⚠️ ВАЖЛИВО:** Замінити `<твій-endpoint>`, `<твій-ключ>`, `<твоє-deployment-ім'я>` на реальні значення з `backend/.env`!

### Крок 4: Deploy!

1. Click **Deploy**
2. Чекай 2-3 хвилини
3. Railway покаже URL: **Copy це URL!**

### Крок 5: Оновити Netlify

1. https://app.netlify.com
2. Твій сайт → Site settings → Environment variables
3. Edit `VITE_API_URL` → Paste Railway URL
4. Save
5. Deploys → Trigger deploy

---

## Варіант 3: Один скрипт для всього

Якщо вже маєш Railway CLI:

```bash
./QUICK_DEPLOY.sh
```

Цей скрипт зробить **ВСЕ автоматично**!

---

## Після Deployment

### Перевір Backend

```bash
# Railway URL (замінити на свій)
RAILWAY_URL="https://твій-app.railway.app"

# Health check
curl $RAILWAY_URL/health

# API docs
open $RAILWAY_URL/docs  # або просто відкрий в браузері
```

Має показати:
```json
{
  "status": "healthy"
}
```

### Перевір Frontend

1. Відкрий свій Netlify сайт
2. Login: `test@jobbot.no` / `Test123456`
3. Йди в **Dashboard**
4. Натисни **"Scan Jobs Now"**
5. Має запрацювати! 🎉

---

## Troubleshooting

### Railway build fails

**Перевір логи:**
```bash
railway logs
```

**Типові проблеми:**
- Missing dependencies → Check `requirements.txt`
- Python version → Railway uses Python 3.10 by default
- Port binding → Railway auto-injects `$PORT`

### "Could not connect to backend"

**Перевір:**
1. Railway service запущений: `railway status`
2. CORS налаштований: Netlify URL в `CORS_ORIGINS`
3. Netlify `VITE_API_URL` правильний

**Fix:**
```bash
railway variables --set CORS_ORIGINS="https://твій-netlify-сайт.netlify.app"
railway restart
```

### Netlify не бачить API

**Перевір Environment Variables:**
```bash
# Netlify CLI
netlify env:list

# Має бути:
# VITE_API_URL = https://твій-railway-url.railway.app
```

**Fix:**
```bash
netlify env:set VITE_API_URL https://твій-railway-url.railway.app
netlify deploy --prod
```

---

## Моніторинг

### Railway Logs (real-time)

```bash
railway logs --follow
```

### Railway Metrics

Dashboard → Metrics → Переглянь:
- CPU usage
- Memory usage
- Request rate
- Response time

### Netlify Logs

Dashboard → Deploys → Build logs

---

## Вартість

### Railway
- **Free tier**: $5 credit/month
- **Developer plan**: $5/month + usage
- **Estimated cost**: ~$5-10/month

### Netlify
- **Free tier**: 100GB bandwidth/month
- JobBot використовує: ~1-2GB/month
- **Cost**: $0 (Free tier достатньо!)

---

## Швидкі команди

### Railway

```bash
# Status
railway status

# Logs
railway logs

# Variables
railway variables

# Restart
railway restart

# Open dashboard
railway open

# Get URL
railway domain
```

### Netlify

```bash
# Status
netlify status

# Logs
netlify logs

# Deploy
netlify deploy --prod

# Open dashboard
netlify open
```

---

## ✅ Checklist

### Railway Deployment
- [ ] Railway account створено
- [ ] Railway CLI встановлено
- [ ] `railway login` виконано
- [ ] `./deploy_railway.sh` запущено
- [ ] Environment variables додані
- [ ] Backend успішно deployed
- [ ] Railway URL скопійовано

### Netlify Update
- [ ] Railway URL скопійовано
- [ ] Netlify env vars оновлено (`VITE_API_URL`)
- [ ] Netlify redeploy зроблено
- [ ] Frontend відкривається
- [ ] Login працює

### Testing
- [ ] `curl https://railway-url/health` → OK
- [ ] Frontend → Dashboard відображається
- [ ] Settings → Profile збереження працює
- [ ] "Scan Jobs Now" кнопка працює
- [ ] Jobs відображаються після скану

**Коли всі ✅ → СИСТЕМА ПРАЦЮЄ!** 🎉

---

## Потрібна допомога?

### Railway
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

### Netlify
- Docs: https://docs.netlify.com
- Support: https://answers.netlify.com

### JobBot
- Check logs: `railway logs` та `netlify logs`
- API docs: `https://твій-railway-url/docs`
- Test endpoints: See `backend/API_TESTING.md`
