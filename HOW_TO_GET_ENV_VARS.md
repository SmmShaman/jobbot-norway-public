# 🔑 Як отримати повні Environment Variables

## ⚠️ ВАЖЛИВО

Файл `RENDER_ENV_VARS.txt` з **ПОВНИМИ реальними ключами** НЕ в git (це секретно!).

Але ти вже маєш його локально! 📁

---

## 📋 Де знайти файл з ключами?

Файл створено локально:
```
/home/user/jobbot-norway-public/RENDER_ENV_VARS.txt
```

**Цей файл містить ВСІ твої реальні API ключі:**
- ✅ Supabase credentials
- ✅ Azure OpenAI keys
- ✅ Telegram Bot Token
- ✅ SpaCy API Key
- ✅ Security keys
- ✅ CORS з Netlify URL

---

## 🚀 Як використовувати для Render:

### Крок 1: Відкрий файл

```bash
cat /home/user/jobbot-norway-public/RENDER_ENV_VARS.txt
```

Або відкрий у текстовому редакторі.

### Крок 2: Скопіюй ВСІ змінні

Виділи весь текст між лініями `========` і скопіюй.

### Крок 3: Вставити в Render

1. Render Dashboard → Create Web Service
2. Environment section → **"Bulk Edit"** (або "Add from .env")
3. **Paste** всі змінні
4. Save → Create Service

✅ Готово!

---

## 📝 Якщо файл загубився

Ось що містить файл (БЕЗ секретів - тільки структура):

```bash
SUPABASE_URL=<твій Supabase URL>
SUPABASE_SERVICE_KEY=<твій Service Key>
SUPABASE_JWT_SECRET=<твій JWT Secret>
AZURE_OPENAI_ENDPOINT=<твій Azure endpoint>
AZURE_OPENAI_KEY=<твій Azure ключ>
AZURE_OPENAI_DEPLOYMENT=<твій deployment>
AZURE_OPENAI_API_VERSION=2024-12-01-preview
ENCRYPTION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
JWT_SECRET=jobbot_norway_secret_key_2024
API_HOST=0.0.0.0
API_PORT=10000
DEBUG=false
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://jobbotnetlify.netlify.app
TELEGRAM_BOT_TOKEN=<твій Telegram token>
SPACY_API_KEY=<твій SpaCy key>
SKYVERN_API_URL=http://localhost:8000
PYTHON_VERSION=3.10.12
```

**Якщо не пам'ятаєш ключі** - переглянь історію цієї розмови, я давав всі credentials раніше!

---

## 🔒 Безпека

**НІКОЛИ не пуш `RENDER_ENV_VARS.txt` в git!**

Файл вже в `.gitignore` ✅

Якщо випадково спробуєш запушити - GitHub заблокує (push protection).

---

## ℹ️ Для інших розробників

Якщо хтось клонує цей репозиторій:
- Вони побачать `backend/.env.example` з placeholders
- Вони НЕ побачать `RENDER_ENV_VARS.txt` (він локальний)
- Їм треба буде створити свої ключі

**Твої секрети залишаються тільки у тебе!** 🔐
