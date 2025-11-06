# 🚀 DEPLOY ЗАРАЗ - 3 ПРОСТИХ КРОКИ

## ⚡ Швидкий старт

### 🎯 Мета

Задеплоїти JobBot Norway backend на Railway за **5 хвилин**.

---

## Крок 1: Встанови Railway CLI (1 хвилина)

**Виконай одну з команд:**

```bash
# macOS
brew install railway

# Linux/WSL (потрібен Node.js)
npm i -g @railway/cli

# Або через bash
bash <(curl -fsSL cli.new)
```

**Перевір:**
```bash
railway --version
```

---

## Крок 2: Запусти автоматичний deployment (3 хвилини)

```bash
cd backend
./deploy_railway.sh
```

**Скрипт зробить:**
1. ✅ Авторизує тебе в Railway (відкриє браузер)
2. ✅ Створить новий Railway project
3. ✅ Прив'яже до GitHub
4. ✅ Завантажить всі змінні з `.env`
5. ✅ Задеплоїть backend
6. ✅ Покаже твій URL

**Скопіюй URL з виводу!** Він виглядає так:
```
https://jobbot-production-abc123.up.railway.app
```

---

## Крок 3: Оновити Netlify (1 хвилина)

### Варіант A: Через Dashboard (простіше)

1. Йди на: https://app.netlify.com
2. Твій сайт → **Site settings** → **Environment variables**
3. Знайди `VITE_API_URL`
4. Edit → Вставити Railway URL
5. Save
6. **Deploys** → **Trigger deploy**

### Варіант B: Через CLI (швидше)

```bash
netlify env:set VITE_API_URL https://твій-railway-url.railway.app
netlify deploy --prod
```

---

## ✅ Готово!

### Перевір що працює:

**Backend:**
```bash
curl https://твій-railway-url.railway.app/health
```

Має відповісти:
```json
{"status": "healthy"}
```

**Frontend:**
1. Відкрий свій Netlify сайт
2. Login: `test@jobbot.no` / `Test123456`
3. **Dashboard** → Натисни **"Scan Jobs Now"**
4. Має запрацювати! 🎉

---

## 🆘 Якщо щось не працює

### Railway build fails

```bash
# Дивись логи
railway logs

# Перевір змінні
railway variables

# Restart
railway restart
```

### Netlify не може з'єднатися

**Перевір CORS:**
```bash
railway variables --set CORS_ORIGINS="https://твій-netlify-сайт.netlify.app"
railway restart
```

---

## 📚 Детальна документація

- **Railway deployment**: `RAILWAY_DEPLOYMENT.md`
- **Одна команда для всього**: `ONE_COMMAND_SETUP.md`
- **API тестування**: `backend/API_TESTING.md`
- **Backend документація**: `backend/README.md`

---

## 💰 Вартість

- **Railway Free tier**: $5 credit/month
- **Netlify**: Безкоштовно
- **Суммарно**: $0-5/month

---

## 🎯 Наступні кроки

Після успішного deployment:

1. ✅ Завантажити resume в Settings
2. ✅ Додати NAV search URLs в Settings
3. ✅ Натиснути "Scan Jobs Now"
4. ✅ Переглянути знайдені вакансії в Jobs
5. 🎉 Profit!

---

**Все готово для deployment! Просто виконай 3 кроки вище.** 🚀
