# JobBot Norway - Web Application 🚀

Мультиюзерний веб-додаток для автоматизації пошуку роботи в Норвегії з AI-аналізом та автоматичним заповненням форм.

## 📋 Зміст

- [Огляд системи](#огляд-системи)
- [Технології](#технології)
- [Швидкий старт](#швидкий-старт)
- [Налаштування Supabase](#налаштування-supabase)
- [Розробка](#розробка)
- [Deployment](#deployment)
- [Структура проекту](#структура-проекту)

---

## 🎯 Огляд системи

**JobBot Norway** - це повнофункціональний веб-додаток, який:

- 🔍 **Автоматично знаходить** вакансії на NAV.no та FINN.no
- 🤖 **AI аналізує** релевантність (Azure OpenAI GPT-4)
- ✍️ **Генерує персоналізовані** cover letters норвезькою мовою
- 📝 **Автоматично заповнює** форми заявок (Skyvern)
- 📊 **Звітує** в NAV про відправлені заявки
- 📱 **Відправляє** сповіщення в Telegram

### Ключові особливості

✅ **Мультиюзер система** - кожен користувач має окремі налаштування
✅ **Real-time оновлення** - Supabase Realtime subscriptions
✅ **Безпека** - Row Level Security (RLS) на рівні бази даних
✅ **Масштабованість** - Serverless архітектура
✅ **AI-driven** - Використання GPT-4 для аналізу та генерації контенту

---

## 🛠️ Технології

### Frontend (Netlify)
- **React 18** + TypeScript
- **Vite** - швидкий build
- **TanStack Query** - data fetching
- **Tailwind CSS** - стилізація
- **Supabase JS Client** - база даних

### Backend (Railway/Render)
- **FastAPI** (Python)
- **Supabase** (PostgreSQL + Storage + Auth)
- **Azure OpenAI GPT-4** - AI аналіз
- **Skyvern** - автоматизація форм

### Інфраструктура
- **Supabase** - база даних, файли, auth
- **Netlify** - frontend hosting
- **Railway/Render** - backend API
- **GitHub Actions** - CI/CD

---

## 🚀 Швидкий старт

### Передумови

- Node.js 18+
- Python 3.11+
- Supabase account
- Azure OpenAI API key

### 1. Клонування репозиторію

```bash
git clone https://github.com/your-username/jobbot-norway-public.git
cd jobbot-norway-public
git checkout netlify-ui
```

### 2. Налаштування Supabase

**Детальні інструкції в:** [`supabase/README.md`](supabase/README.md)

Швидко:
1. Створи проект на [supabase.com](https://supabase.com)
2. Запусти SQL міграцію з `supabase/migrations/001_initial_schema.sql`
3. Створи Storage buckets: `resumes`, `cover-letters`, `screenshots`
4. Скопіюй Project URL та API keys

### 3. Frontend Setup

```bash
cd web-app

# Встановлення залежностей
npm install

# Створення .env
cp ../.env.web.example .env

# Заповни .env файл:
# VITE_SUPABASE_URL=твій_supabase_url
# VITE_SUPABASE_ANON_KEY=твій_anon_key
# VITE_API_URL=http://localhost:8000

# Запуск dev server
npm run dev
```

Frontend буде доступний на `http://localhost:3000`

### 4. Backend Setup

```bash
cd backend

# Створення virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Встановлення залежностей
pip install -r requirements.txt

# Створення .env
cp ../.env.backend.example .env

# Заповни .env файл з Supabase та Azure credentials

# Запуск dev server
uvicorn app.main:app --reload --port 8000
```

Backend API буде доступний на `http://localhost:8000`

### 5. Перший запуск

1. Відкрий `http://localhost:3000`
2. Зареєструйся (Sign Up)
3. Завантаж резюме в Settings
4. Додай search URLs (NAV/FINN)
5. Натисни "Scan Jobs Now" в Dashboard

---

## 📁 Структура проекту

```
jobbot-norway-public/
├── web-app/                   # React Frontend
│   ├── src/
│   │   ├── components/        # React компоненти
│   │   │   ├── Dashboard/
│   │   │   ├── Jobs/
│   │   │   ├── Applications/
│   │   │   └── Settings/
│   │   ├── hooks/             # React hooks
│   │   ├── lib/               # Supabase, API clients
│   │   ├── pages/             # Сторінки
│   │   ├── types/             # TypeScript types
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                   # FastAPI Backend
│   ├── app/
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── models/            # Data models
│   │   ├── utils/             # Utilities
│   │   ├── config.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── supabase/                  # Database
│   ├── migrations/            # SQL schemas
│   │   └── 001_initial_schema.sql
│   └── README.md
│
├── src/                       # Існуючий Python код (для інтеграції)
│   ├── ai_analyzer.py         # AI аналіз релевантності
│   ├── ai_cover_letter_generator.py
│   ├── multi_user_system.py
│   └── ...
│
├── ARCHITECTURE.md            # Детальна архітектура
├── netlify.toml               # Netlify config
└── README_WEB.md              # Цей файл
```

---

## 🗄️ Налаштування Supabase

### Крок 1: SQL Міграція

В Supabase Dashboard → SQL Editor:

```bash
# Скопіюй і запусти весь файл:
supabase/migrations/001_initial_schema.sql
```

Це створить:
- ✅ 6 таблиць з RLS policies
- ✅ Triggers для auto-updates
- ✅ Views для analytics
- ✅ Functions для user management

### Крок 2: Storage Buckets

В Supabase Dashboard → Storage:

1. Створи bucket `resumes` (Private, 10MB limit)
2. Створи bucket `cover-letters` (Private, 5MB limit)
3. Створи bucket `screenshots` (Private, 5MB limit)

**Детальні Storage policies в:** `supabase/README.md`

### Крок 3: Authentication

В Supabase Dashboard → Authentication → Providers:

- ✅ Enable Email provider
- ✅ Confirm email (optional)

---

## 💻 Розробка

### Frontend Development

```bash
cd web-app

# Dev mode з hot reload
npm run dev

# Type checking
npm run type-check

# Build для production
npm run build

# Preview production build
npm run preview
```

### Backend Development

```bash
cd backend

# Dev mode з hot reload
uvicorn app.main:app --reload

# Run з debug logging
DEBUG=true uvicorn app.main:app --reload

# Тести (TODO)
pytest
```

### Інтеграція існуючого коду

Існуючі Python модулі з `src/` використовуються в backend:

```python
# backend/app/services/ai_service.py
from ...src.ai_analyzer import analyze_job_relevance
from ...src.ai_cover_letter_generator import AICoverLetterGenerator
from ...src.multi_user_system import MultiUserJobSystem
```

---

## 🚀 Deployment

### Frontend (Netlify)

**Автоматичний deploy:**

1. Підключи GitHub репозиторій до Netlify
2. Branch: `netlify-ui`
3. Base directory: `web-app`
4. Build command: `npm install && npm run build`
5. Publish directory: `dist`

**Environment Variables в Netlify:**
```
VITE_SUPABASE_URL=твій_supabase_url
VITE_SUPABASE_ANON_KEY=твій_anon_key
VITE_API_URL=https://твій-backend.railway.app
```

### Backend (Railway)

**Deployment з GitHub:**

1. Створи новий проект на [railway.app](https://railway.app)
2. Deploy from GitHub → вибери репозиторій
3. Root directory: `backend`
4. Deploy

**Environment Variables в Railway:**
- Додай всі змінні з `.env.backend.example`

**Або Docker deploy:**

```bash
cd backend
docker build -t jobbot-backend .
railway up
```

### Database (Supabase)

Вже в хмарі! Нічого деплоїти не потрібно.

---

## 📊 Моніторинг та Логи

### Supabase Logs

Dashboard → Logs:
- Database queries
- Auth events
- Storage operations

### Backend Logs

Railway → Logs:
- API requests
- AI operations
- Errors

### Frontend Errors

Netlify → Functions logs:
- Build errors
- Deploy status

---

## 🔒 Безпека

### Що НЕ зберігати в git:

❌ `.env` файли
❌ `service_role` keys
❌ Azure OpenAI keys
❌ NAV passwords

### Що безпечно:

✅ `anon` key (обмежений через RLS)
✅ Project URL
✅ Frontend код

### Row Level Security (RLS)

Всі таблиці захищені RLS policies:
- Користувачі бачать тільки свої дані
- Ніхто не може читати чужі резюме чи заявки

---

## 🤝 Contributing

1. Створи feature branch: `git checkout -b feature/amazing-feature`
2. Commit changes: `git commit -m 'Add amazing feature'`
3. Push: `git push origin feature/amazing-feature`
4. Створи Pull Request

---

## 📝 TODO (Phase 2)

- [ ] Automatic scheduled scanning (cron jobs)
- [ ] Telegram bot integration
- [ ] Advanced analytics dashboard
- [ ] Email notifications
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Resume templates
- [ ] Interview tracking

---

## 📞 Support

При виникненні проблем:
- 📖 [Architecture Documentation](ARCHITECTURE.md)
- 💬 GitHub Issues
- 📧 Email: your-email@example.com

---

## 📜 License

MIT License - використовуй вільно!

---

**Made with ❤️ in Norway 🇳🇴**
