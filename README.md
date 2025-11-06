# JobBot Norway - Automated Job Search & Application System

**Автоматична система пошуку роботи в Норвегії з AI аналізом** 🇳🇴

---

## 🚀 Quick Start - Deploy Now!

### **⚡ 3 простих кроки для deployment:**

**Читай:** `DEPLOY_NOW.md` - Займе 5 хвилин!

```bash
cd backend
./deploy_railway.sh
```

**Альтернатива:** Детальна інструкція → `ONE_COMMAND_SETUP.md`

---

## 📱 What is JobBot Norway?

**Multi-user web application** для автоматизації пошуку роботи в Норвегії:

### ✨ Features

- 🔍 **Automatic Job Scanning** - Моніторинг NAV.no та FINN.no
- 🤖 **AI Relevance Analysis** - GPT-4 аналізує релевантність вакансій
- 📊 **Personal Dashboard** - Статистика та моніторинг
- ⚙️ **Settings Management** - Профіль, резюме, налаштування пошуку
- 📝 **Cover Letter Generation** - AI-генерація мотиваційних листів (норвезькою)
- 🔐 **Multi-user System** - Кожен користувач має ізольовані дані
- 📱 **Telegram Notifications** - Сповіщення про нові вакансії
- 🎯 **Smart Filtering** - Автоматична фільтрація за skills та preferences

---

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- React 18 + TypeScript + Vite
- TanStack Query (React Query)
- Tailwind CSS
- Supabase Auth
- Deploy: **Netlify**

**Backend:**
- FastAPI (Python 3.10)
- Azure OpenAI GPT-4
- Supabase (PostgreSQL + Storage)
- BeautifulSoup4 (Scraping)
- Deploy: **Railway**

**Database:**
- Supabase PostgreSQL
- Row Level Security (RLS)
- Real-time subscriptions

### System Flow

```
User → Netlify Frontend → Railway Backend → Supabase Database
                              ↓
                         Azure OpenAI GPT-4
                              ↓
                    NAV.no / FINN.no Scraping
```

---

## 📂 Project Structure

```
jobbot-norway-public/
├── web-app/              # React frontend
│   ├── src/
│   │   ├── pages/        # Dashboard, Jobs, Settings
│   │   ├── components/   # UI components
│   │   ├── hooks/        # React Query hooks
│   │   └── lib/          # Supabase client
│   └── netlify.toml      # Netlify config
│
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py       # FastAPI app
│   │   ├── routers/      # API endpoints
│   │   └── services/     # Business logic
│   │       ├── ai_service.py       # Azure OpenAI
│   │       ├── scraper_service.py  # Job scraping
│   │       └── database.py         # Supabase ops
│   ├── railway.toml      # Railway config
│   └── deploy_railway.sh # Auto-deployment script
│
├── src/                  # Legacy Python modules (N8N workflows)
│   ├── ai_analyzer.py
│   ├── deep_job_analyzer.py
│   └── ...
│
├── supabase/
│   └── migrations/       # Database schema
│
└── workflows/            # N8N workflow JSONs (legacy)
```

---

## 🚀 Deployment

### Option 1: Automated (Recommended)

```bash
# 1. Backend to Railway
cd backend
./deploy_railway.sh

# 2. Update Netlify
netlify env:set VITE_API_URL https://твій-railway-url.railway.app
netlify deploy --prod
```

### Option 2: Manual GUI

**Детальні інструкції:**
- Backend → Railway: `RAILWAY_DEPLOYMENT.md`
- Frontend → Netlify: `NETLIFY_SETUP.md`
- Database → Supabase: `NEXT_STEPS.md`

### Option 3: One Command

```bash
./QUICK_DEPLOY.sh
```

---

## 📚 Documentation

### Setup Guides
- 🚀 **DEPLOY_NOW.md** - Quick 5-minute deployment
- 📖 **ONE_COMMAND_SETUP.md** - Complete deployment guide (3 варіанти)
- 🏗️ **ARCHITECTURE.md** - System architecture
- 🗄️ **NEXT_STEPS.md** - Database setup

### Backend Docs
- 📘 **backend/README.md** - Full backend documentation
- 🧪 **backend/API_TESTING.md** - API testing guide
- 🚂 **RAILWAY_DEPLOYMENT.md** - Railway deployment

### Frontend Docs
- 📗 **README_WEB.md** - Frontend documentation
- 🎨 **NETLIFY_SETUP.md** - Netlify setup

---

## 🧪 Local Development

### Frontend

```bash
cd web-app
npm install
npm run dev
# http://localhost:5173
```

### Backend

```bash
cd backend
./start_dev.sh
# http://localhost:8000/docs
```

### Database

1. Create Supabase project
2. Run SQL migration from `supabase/migrations/001_initial_schema.sql`
3. Create storage buckets (resumes, cover-letters, screenshots)
4. Update `.env` files with Supabase credentials

---

## 🔑 Environment Variables

### Frontend (`web-app/.env`)

```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=https://your-railway-url.railway.app
```

### Backend (`backend/.env`)

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=your-deployment
```

**Full list:** See `RAILWAY_DEPLOYMENT.md`

---

## 🎯 Usage

1. **Sign Up** → Create account at your Netlify URL
2. **Settings** → Add profile, upload resume, configure search URLs
3. **Scan Jobs** → Click "Scan Jobs Now" on Dashboard
4. **Review Jobs** → AI analyzes and scores each job
5. **Apply** → Approve relevant jobs for application

---

## 🔮 Features Roadmap

### ✅ Implemented
- Multi-user authentication
- Job scraping (NAV + FINN)
- AI relevance analysis
- Dashboard statistics
- Settings management
- Resume upload

### 🚧 In Progress
- Skyvern integration for auto-applying
- Telegram notifications
- Cover letter generation UI

### 📅 Planned
- NAV automatic reporting
- BankID integration
- Email notifications
- Job recommendations
- Application tracking

---

## 🤖 Legacy N8N Workflows

Оригінальна система була на N8N workflows (`workflows/` directory).

**Зараз замінено на:**
- N8N → **React + FastAPI Web App**
- Локальні workflow JSONs → **Cloud-based Supabase**
- Manual triggers → **Automatic scheduling**

**Legacy modules in `src/`** integrated into `backend/app/services/`.

---

## 👥 Multi-User Support

Система підтримує необмежену кількість користувачів:
- Кожен має ізольовані дані (Row Level Security)
- Персональні налаштування
- Власне резюме та профіль
- Індивідуальні search URLs

---

## 🔒 Security

- ✅ Supabase Row Level Security (RLS)
- ✅ Encrypted NAV credentials
- ✅ HTTPS only in production
- ✅ Environment variables for secrets
- ✅ CORS protection
- ✅ Input validation

---

## 💰 Cost Estimate

- **Netlify**: Free tier (достатньо)
- **Railway**: $5-10/month
- **Supabase**: Free tier (500MB database)
- **Azure OpenAI**: Pay-per-use (~$1-5/month)

**Total: ~$6-15/month**

---

## 🆘 Support & Troubleshooting

### Common Issues

**Backend не відповідає:**
```bash
railway logs
railway restart
```

**Frontend не може з'єднатися:**
- Перевір `VITE_API_URL` в Netlify env vars
- Перевір CORS в Railway variables

**AI analysis fails:**
- Verify Azure OpenAI credentials
- Check quota limits

**Повна troubleshooting guide:** `ONE_COMMAND_SETUP.md`

---

## 📊 Stats

- **Lines of Code**: ~15,000
- **Python Modules**: 70+
- **API Endpoints**: 15+
- **React Components**: 20+
- **Database Tables**: 6
- **Test User**: test@jobbot.no / Test123456

---

## 🏆 Credits

Built with:
- FastAPI
- React + Vite
- Supabase
- Azure OpenAI
- Railway
- Netlify

**Developed by Claude AI** 🤖 in collaboration with human guidance.

---

## 📄 License

MIT License - See LICENSE file

---

## 🚀 Get Started Now!

```bash
# Clone repo
git clone https://github.com/SmmShaman/jobbot-norway-public
cd jobbot-norway-public

# Deploy backend (5 min)
cd backend
./deploy_railway.sh

# Update frontend (2 min)
# Follow instructions in terminal

# ✅ Done! Visit your Netlify URL
```

**Детальна інструкція:** `DEPLOY_NOW.md`

---

**Made with ❤️ for job seekers in Norway** 🇳🇴
