# ⚡ ПОЧНИ ЗВІДСИ - Deployment за 5 хвилин

## 🎯 Що маємо зараз

✅ **Frontend** - задеплоєний на Netlify (працює!)
✅ **Backend** - код готовий, треба задеплоїти на Railway
✅ **Database** - Supabase налаштований
✅ **Документація** - повна, детальна

---

## 🚀 ЩО ТОБІ ТРЕБА ЗРОБИТИ ЗАРАЗ

### Крок 1: Встановити Railway CLI (30 секунд)

**Виберіть один варіант:**

```bash
# macOS
brew install railway

# Linux/WSL (якщо є Node.js)
npm i -g @railway/cli

# Універсальний спосіб (bash)
bash <(curl -fsSL cli.new)
```

**Перевір:**
```bash
railway --version
# Має показати щось типу: railway version 3.x.x
```

---

### Крок 2: Задеплоїти Backend (3 хвилини)

```bash
cd backend
./deploy_railway.sh
```

**Скрипт сам зробить:**
1. Запитає тебе авторизуватися (відкриє браузер)
2. Створить Railway project
3. Прив'яже до GitHub
4. Завантажить всі змінні з `.env`
5. Задеплоїть backend
6. Покаже твій URL

**⚠️ ВАЖЛИВО:** Скопіюй URL з виводу! Виглядає так:
```
https://jobbot-production-abc123.up.railway.app
```

---

### Крок 3: Оновити Netlify (1 хвилина)

#### Варіант A: Через Dashboard (простіше)

1. Йди: https://app.netlify.com
2. Твій сайт → **Site settings** → **Environment variables**
3. Знайди `VITE_API_URL` → **Edit**
4. Вставити Railway URL
5. **Save**
6. **Deploys** → **Trigger deploy**

#### Варіант B: Через CLI (швидше)

```bash
netlify login  # Якщо ще не логінився
netlify env:set VITE_API_URL https://твій-railway-url.railway.app
netlify deploy --prod
```

---

## ✅ Перевірити що працює

### 1. Backend Health Check

```bash
curl https://твій-railway-url.railway.app/health
```

**Має показати:**
```json
{"status": "healthy"}
```

### 2. Backend API Docs

Відкрий в браузері:
```
https://твій-railway-url.railway.app/docs
```

Має з'явитися інтерактивна документація FastAPI!

### 3. Frontend + Backend Разом

1. Йди на свій Netlify сайт (https://твій-сайт.netlify.app)
2. Login: `test@jobbot.no` / `Test123456`
3. **Dashboard** → Натисни **"Scan Jobs Now"**
4. Якщо працює → **ВСЕ ГОТОВО!** 🎉

---

## 📚 Якщо потрібна допомога

### Швидкі посилання:

- 🚀 **Швидкий старт** → `DEPLOY_NOW.md`
- 📖 **Детальна інструкція** → `ONE_COMMAND_SETUP.md`
- 🏗️ **Архітектура** → `ARCHITECTURE.md`
- 🧪 **Тестування API** → `backend/API_TESTING.md`
- 🚂 **Railway deployment** → `RAILWAY_DEPLOYMENT.md`

### Типові проблеми:

**Railway build fails:**
```bash
railway logs  # Дивись логи
```

**Frontend не може з'єднатися з backend:**
- Перевір що `VITE_API_URL` правильний в Netlify
- Перевір CORS в Railway:
  ```bash
  railway variables --set CORS_ORIGINS="https://твій-netlify-сайт.netlify.app"
  railway restart
  ```

**"No search URLs configured":**
- Йди в Settings → Search URLs tab
- Додай хоча б один NAV URL
- Збережи

---

## 💰 Вартість

- **Netlify**: $0 (безкоштовно)
- **Railway**: $5-10/month
- **Supabase**: $0 (free tier)
- **Azure OpenAI**: ~$1-5/month (pay-per-use)

**Разом: ~$6-15/month**

---

## 🎉 Наступні кроки після deployment

1. ✅ Завантажити своє резюме в Settings
2. ✅ Додати NAV search URLs
3. ✅ Натиснути "Scan Jobs Now"
4. ✅ Переглянути знайдені вакансії
5. ✅ Налаштувати Telegram notifications (опціонально)

---

## 🆘 Потрібна негайна допомога?

**Railway проблеми:**
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

**Netlify проблеми:**
- Docs: https://docs.netlify.com
- Support: https://answers.netlify.com

**Дивись також:**
- `ONE_COMMAND_SETUP.md` - повна troubleshooting секція
- `backend/API_TESTING.md` - як тестувати endpoints

---

## ⚡ TL;DR (Дуже швидка інструкція)

```bash
# 1. Встанови Railway CLI
brew install railway  # або npm i -g @railway/cli

# 2. Deploy backend
cd backend
./deploy_railway.sh
# Скопіюй URL з виводу!

# 3. Оновити Netlify
netlify env:set VITE_API_URL https://твій-railway-url
netlify deploy --prod

# 4. Тест
curl https://твій-railway-url/health
# Відкрий Netlify сайт → Login → Scan Jobs Now

# ✅ Готово!
```

---

**Все підготовлено! Просто виконай 3 кроки вище і система запрацює!** 🚀
