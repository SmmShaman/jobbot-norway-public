# JobBot Norway - Web Application Architecture

## 🎯 Огляд системи

Мультиюзерний веб-додаток для автоматизації пошуку роботи в Норвегії з AI-аналізом та автоматичним заповненням форм.

---

## 🏗️ Технологічний стек

### Frontend (Netlify)
- **React 18** + TypeScript
- **Vite** - швидкий build tool
- **TanStack Query** - управління server state
- **Zustand** - локальний state management
- **Tailwind CSS** + **shadcn/ui** - UI компоненти
- **React Router v6** - маршрутизація

### Backend (Supabase)
- **Supabase PostgreSQL** - головна база даних
- **Supabase Storage** - зберігання резюме, cover letters, screenshots
- **Supabase Auth** - аутентифікація користувачів
- **Supabase Edge Functions** - serverless API endpoints
- **Row Level Security (RLS)** - безпека даних на рівні БД

### AI & Automation
- **Azure OpenAI (GPT-4)** - аналіз релевантності, генерація cover letters
- **Skyvern** - розпізнавання HTML форм та автоматичне заповнення
- **Python FastAPI microservice** - інтеграція з Skyvern (Railway/Render)

---

## 📊 Структура бази даних (Supabase)

### Таблиці

#### 1. `users` (extends Supabase Auth)
```sql
CREATE TABLE public.profiles (
  id UUID REFERENCES auth.users PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  full_name TEXT,
  email TEXT,
  phone TEXT,
  fnr TEXT, -- Norwegian ID
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 2. `user_settings`
```sql
CREATE TABLE public.user_settings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,

  -- Search settings
  nav_search_urls TEXT[], -- Array of pre-filtered NAV URLs
  finn_search_urls TEXT[],
  keywords TEXT[],
  exclude_keywords TEXT[],
  preferred_locations TEXT[],

  -- Resume & Profile
  resume_storage_path TEXT, -- Supabase Storage path
  unified_profile JSONB, -- AI-analyzed resume data
  skills TEXT[],
  experience_years INT,

  -- Application settings
  min_relevance_score INT DEFAULT 70,
  auto_apply_threshold INT DEFAULT 85,
  max_applications_per_day INT DEFAULT 5,
  require_manual_approval BOOLEAN DEFAULT true,

  -- NAV credentials (encrypted)
  nav_fnr TEXT,
  nav_password_encrypted TEXT,

  -- Telegram notifications
  telegram_chat_id TEXT,
  telegram_enabled BOOLEAN DEFAULT false,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3. `jobs`
```sql
CREATE TABLE public.jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,

  -- Job details
  url TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  company TEXT,
  description TEXT,
  location TEXT,
  source TEXT, -- 'nav.no', 'finn.no'
  posted_date DATE,

  -- AI Analysis
  relevance_score INT DEFAULT 0,
  ai_analysis JSONB, -- Full AI response
  match_reasons TEXT[],
  concerns TEXT[],
  recommendation TEXT, -- 'APPLY', 'SKIP', 'REVIEW'

  -- Status
  status TEXT DEFAULT 'NEW', -- NEW, ANALYZED, APPROVED, APPLIED, REJECTED, REPORTED

  -- Form filling data
  application_form_html TEXT,
  skyvern_task_id TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Indexes
  INDEX idx_jobs_user_status (user_id, status),
  INDEX idx_jobs_relevance (user_id, relevance_score DESC)
);
```

#### 4. `cover_letters`
```sql
CREATE TABLE public.cover_letters (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,

  content TEXT NOT NULL,
  language TEXT DEFAULT 'norwegian',
  word_count INT,

  -- Storage
  pdf_path TEXT, -- Supabase Storage path
  txt_path TEXT,

  -- Generation metadata
  ai_model TEXT DEFAULT 'gpt-4',
  generation_prompt TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 5. `applications`
```sql
CREATE TABLE public.applications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
  cover_letter_id UUID REFERENCES public.cover_letters(id),

  -- Application details
  application_url TEXT,
  status TEXT DEFAULT 'PENDING', -- PENDING, SUCCESS, FAILED, REPORTED

  -- Form filling results
  skyvern_result JSONB,
  screenshot_path TEXT, -- Supabase Storage

  -- NAV reporting
  nav_reported BOOLEAN DEFAULT false,
  nav_report_date TIMESTAMPTZ,
  nav_response JSONB,

  -- Error tracking
  error_message TEXT,
  retry_count INT DEFAULT 0,

  submitted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 6. `monitoring_logs`
```sql
CREATE TABLE public.monitoring_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,

  -- Scan info
  scan_type TEXT, -- 'MANUAL', 'SCHEDULED'
  jobs_found INT DEFAULT 0,
  jobs_analyzed INT DEFAULT 0,
  applications_sent INT DEFAULT 0,
  nav_reports_sent INT DEFAULT 0,

  -- Status
  status TEXT, -- 'RUNNING', 'COMPLETED', 'FAILED'
  error_message TEXT,

  duration_seconds INT,

  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);
```

### Supabase Storage Buckets

```javascript
// Storage structure
buckets: {
  'resumes': {
    public: false,
    path: '{user_id}/resume_{timestamp}.pdf'
  },
  'cover-letters': {
    public: false,
    path: '{user_id}/{job_id}/cover_letter.pdf'
  },
  'screenshots': {
    public: false,
    path: '{user_id}/applications/{application_id}/screenshot.png'
  }
}
```

---

## 🔄 Архітектура системи

```
┌─────────────────────────────────────────────────────────────┐
│                     NETLIFY (Frontend)                       │
│  React Dashboard + TanStack Query + Supabase Client         │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──── Supabase Auth (Login/Register)
             │
             ├──── Supabase Realtime (Live updates)
             │
             ↓
┌─────────────────────────────────────────────────────────────┐
│                   SUPABASE (Backend)                         │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL  │  │   Storage    │  │ Edge Funcs   │      │
│  │   + RLS     │  │  (Files)     │  │  (Serverless)│      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────┐
│          PYTHON MICROSERVICE (Railway/Render)                │
│                                                              │
│  ┌─────────────────────────────────────────────┐           │
│  │  FastAPI Server                              │           │
│  │                                              │           │
│  │  ├─ /api/scan-jobs (trigger scraping)       │           │
│  │  ├─ /api/analyze-job (AI relevance)         │           │
│  │  ├─ /api/generate-letter (AI cover letter)  │           │
│  │  ├─ /api/fill-form (Skyvern)                │           │
│  │  └─ /api/report-nav (NAV automation)        │           │
│  └─────────────────────────────────────────────┘           │
│                                                              │
│  ┌─────────────────────────────────────────────┐           │
│  │  Skyvern Integration                         │           │
│  │  (Local Playwright + Built-in LLM)          │           │
│  └─────────────────────────────────────────────┘           │
│                                                              │
│  ┌─────────────────────────────────────────────┐           │
│  │  Azure OpenAI Client                         │           │
│  │  (GPT-4 for analysis & generation)          │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Безпека

### Row Level Security (RLS) Policies

```sql
-- Users can only see their own data
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own jobs"
  ON public.jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own jobs"
  ON public.jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Similar policies for all tables
```

### Encrypted credentials
- NAV passwords зберігаються зашифровані (AES-256)
- FNR зберігається захищено з RLS
- Telegram tokens в environment variables

---

## 🎨 Frontend структура

```
web-app/
├── src/
│   ├── components/
│   │   ├── Dashboard/
│   │   │   ├── DashboardOverview.tsx
│   │   │   ├── JobsTable.tsx
│   │   │   ├── ApplicationsTable.tsx
│   │   │   └── MonitoringChart.tsx
│   │   ├── Settings/
│   │   │   ├── UserProfile.tsx
│   │   │   ├── SearchSettings.tsx
│   │   │   ├── ResumeUpload.tsx
│   │   │   └── NavCredentials.tsx
│   │   ├── Jobs/
│   │   │   ├── JobCard.tsx
│   │   │   ├── JobDetails.tsx
│   │   │   ├── RelevanceScore.tsx
│   │   │   └── ApprovalButtons.tsx
│   │   └── Auth/
│   │       ├── Login.tsx
│   │       └── Register.tsx
│   ├── hooks/
│   │   ├── useJobs.ts
│   │   ├── useApplications.ts
│   │   ├── useMonitoring.ts
│   │   └── useSupabase.ts
│   ├── lib/
│   │   ├── supabase.ts
│   │   ├── api.ts
│   │   └── types.ts
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Jobs.tsx
│   │   ├── Applications.tsx
│   │   ├── Settings.tsx
│   │   └── Reports.tsx
│   └── App.tsx
├── public/
└── index.html
```

---

## ⚙️ Backend (Python) структура

```
backend/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings
│   ├── models/
│   │   ├── job.py
│   │   ├── user.py
│   │   └── application.py
│   ├── services/
│   │   ├── scraper.py          # NAV/FINN scraping
│   │   ├── ai_analyzer.py      # Azure OpenAI integration
│   │   ├── cover_letter.py     # AI letter generation
│   │   ├── skyvern_client.py   # Skyvern integration
│   │   └── nav_reporter.py     # NAV automation
│   ├── routers/
│   │   ├── jobs.py
│   │   ├── applications.py
│   │   ├── monitoring.py
│   │   └── webhooks.py
│   └── utils/
│       ├── supabase_client.py
│       └── encryption.py
├── requirements.txt
└── Dockerfile
```

---

## 🔄 Робочий процес (Workflow)

### 1. Автоматичний моніторинг

```
[CRON Job в Supabase Edge Function - кожні 2 години]
   ↓
[Викликає Python API: /api/scan-jobs]
   ↓
[Scraping NAV/FINN з персональних URLs користувача]
   ↓
[Зберігає нові вакансії в Supabase]
   ↓
[Trigger: AI аналіз кожної вакансії]
   ↓
[Azure OpenAI аналізує релевантність (0-100)]
   ↓
[Зберігає результат + оновлює статус]
   ↓
[Notification: Telegram + Dashboard Real-time update]
```

### 2. AI аналіз релевантності

```python
# Використовується існуючий промпт з ai_analyzer.py
prompt = f"""
Analyze this job posting for relevance to a candidate.

Job Title: {job_title}
Job Description: {job_description}
User Skills: {user_skills}
User Experience: {user_experience}

Respond with ONLY valid JSON:
{{
    "relevance_score": 85,
    "is_relevant": true,
    "match_reasons": ["Python experience matches", "Location is preferred"],
    "concerns": ["Requires 5 years, user has 3"],
    "recommendation": "APPLY"
}}
"""
```

### 3. Генерація Cover Letter

```
[User clicks "Generate Cover Letter" for job]
   ↓
[Python API: /api/generate-letter]
   ↓
[Завантажує unified_profile з Supabase]
   ↓
[Azure OpenAI генерує персоналізований лист (норвезька)]
   ↓
[Зберігає текст + PDF в Supabase Storage]
   ↓
[Зв'язує з job_id в таблиці cover_letters]
   ↓
[User може редагувати в dashboard]
```

### 4. Автоматичне заповнення форм (Skyvern)

```
[User approves application]
   ↓
[Python API: /api/fill-form]
   ↓
[Skyvern отримує URL вакансії + user data]
   ↓
[Skyvern LLM аналізує HTML форму]
   ↓
[Playwright автоматично заповнює поля]
   ↓
[Прикріплює резюме + cover letter]
   ↓
[Робить screenshot перед submit]
   ↓
[Відправляє форму]
   ↓
[Зберігає результат + screenshot в Supabase]
   ↓
[Оновлює статус application → SUCCESS]
```

### 5. Звітність в NAV

```
[Після успішної application]
   ↓
[Python API: /api/report-nav]
   ↓
[Playwright відкриває arbeidsplassen.nav.no]
   ↓
[BankID автентифікація з FNR]
   ↓
[Заповнює звіт про відправлену заявку]
   ↓
[Скріншот підтвердження]
   ↓
[Оновлює nav_reported = true]
```

---

## 📱 Dashboard Features

### Головна сторінка (Overview)
- **Статистика**: Знайдено вакансій / Проаналізовано / Відправлено заявок / Звітів NAV
- **Графік активності**: За останні 30 днів
- **Останні знайдені вакансії**: Топ-10 по relevance_score
- **Кнопка**: "Запустити пошук зараз"

### Вакансії (Jobs)
- **Фільтри**: Статус, Relevance score, Source, Date
- **Сортування**: По score, date, company
- **Дії для кожної вакансії**:
  - Переглянути повний опис
  - AI аналіз (score + пояснення)
  - Згенерувати cover letter
  - Approve/Reject
  - Перейти на сайт вакансії

### Заявки (Applications)
- **Таблиця всіх відправлених заявок**:
  - Job title + company
  - Дата відправки
  - Статус (Success/Failed)
  - Скріншот форми
  - Чи звітували в NAV
- **Фільтри**: По статусу, даті

### Налаштування (Settings)
1. **Профіль**:
   - Ім'я, email, phone, FNR
   - Завантаження резюме (PDF)
   - AI аналіз резюме → unified_profile

2. **Пошук**:
   - Персональні NAV URLs (pre-filtered)
   - FINN RSS feeds
   - Keywords / Exclude keywords
   - Preferred locations

3. **Automation**:
   - Min relevance score для відображення
   - Auto-apply threshold (>85 → auto apply)
   - Max applications per day
   - Require manual approval

4. **Інтеграції**:
   - NAV credentials (FNR + password) - encrypted
   - Telegram bot token + chat ID
   - Test connection buttons

### Звітність (Reports)
- **Щоденні звіти**: Скільки вакансій, заявок, NAV reports
- **Експорт**: CSV / Excel
- **Графіки**: Success rate, Response time

---

## 🚀 Deployment

### Frontend (Netlify)
```bash
# netlify.toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Backend (Railway/Render)
```bash
# Docker deploy
docker build -t jobbot-backend .
railway up  # або render deploy
```

### Supabase
- Create project on supabase.com
- Run migrations (SQL schema)
- Setup Storage buckets
- Deploy Edge Functions
- Configure Auth providers

---

## 📋 Environment Variables

### Frontend (.env)
```
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=xxx
VITE_API_URL=https://jobbot-api.railway.app
```

### Backend (.env)
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
AZURE_OPENAI_ENDPOINT=https://elvarika.openai.azure.com
AZURE_OPENAI_KEY=xxx
AZURE_OPENAI_DEPLOYMENT=gpt-4
SKYVERN_API_URL=http://localhost:8000
ENCRYPTION_KEY=xxx
```

---

## 🔧 Налаштування Skyvern

Skyvern буде запущений як частина Python backend:

```python
# skyvern_client.py
from skyvern import Skyvern

class SkyvernClient:
    def __init__(self):
        self.skyvern = Skyvern(
            headless=False,  # Для debugging
            use_builtin_llm=True  # Використовує вбудовану LLM
        )

    async def fill_application_form(self, job_url: str, user_data: dict):
        """
        Skyvern автоматично:
        1. Аналізує HTML форму з LLM
        2. Визначає які поля потрібно заповнити
        3. Заповнює форму з user_data
        4. Прикріплює файли
        5. Відправляє форму
        """
        task = await self.skyvern.execute(
            url=job_url,
            goal="Fill and submit job application form",
            data=user_data,
            files={
                "resume": user_data["resume_path"],
                "cover_letter": user_data["cover_letter_path"]
            }
        )
        return task.result
```

---

## 📊 Monitoring & Logging

- **Supabase Logs**: Всі запити до БД
- **Python Logging**: FastAPI structured logs
- **Frontend Error Tracking**: Sentry (optional)
- **Real-time Dashboard**: Supabase Realtime subscriptions

---

## 🎯 MVP Features (Phase 1)

✅ **Must Have:**
1. User registration/login (Supabase Auth)
2. Upload resume + AI analysis
3. Add personal search URLs (NAV/FINN)
4. Manual "Scan Now" button
5. View found jobs with AI relevance score
6. Generate cover letter for job
7. Manually approve application
8. View applications history

❌ **Later (Phase 2):**
- Automatic scheduled scanning (cron)
- Auto-apply for high-relevance jobs
- NAV automatic reporting
- Telegram notifications
- Advanced analytics

---

## 💾 Дані які потрібні від користувача

Для створення `.env` файлів мені потрібно:

### Supabase
- [ ] Supabase Project URL
- [ ] Supabase Anon Key
- [ ] Supabase Service Key

### Azure OpenAI
- [ ] ✅ Endpoint: https://elvarika.openai.azure.com
- [ ] Azure OpenAI Key
- [ ] Deployment name (наприклад: gpt-4)

### User specific (для кожного користувача)
- [ ] Full name
- [ ] Email
- [ ] Phone
- [ ] FNR (Norwegian ID)
- [ ] NAV password (для автоматичної звітності)
- [ ] Telegram Bot Token (optional)
- [ ] Telegram Chat ID (optional)
- [ ] Resume file (PDF)
- [ ] Персональні search URLs (NAV/FINN pre-filtered)

---

Готовий до реалізації! 🚀
