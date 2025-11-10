# 🎯 JobBot Norway - Повний план реалізації

**Дата створення:** 2025-11-10
**Мета:** Створити повноцінний додаток для автоматизації пошуку роботи з AI аналізом

---

## Етап 1: PDF Parser & Профіль кандидата

### 1.1 Backend API для завантаження резюме
**Файл:** `backend/app/routers/profile.py`

```python
from fastapi import APIRouter, UploadFile, File
from app.services.resume_parser import ResumeParserService

router = APIRouter()

@router.post("/api/profile/upload-resume")
async def upload_resume(user_id: str, file: UploadFile = File(...)):
    """Upload and parse PDF/DOCX resume using Azure OpenAI"""
    # 1. Save file to Supabase Storage
    # 2. Extract text (PDF/DOCX/TXT)
    # 3. Parse with Azure OpenAI GPT-4
    # 4. Save structured profile to user_profiles table
    # 5. Return parsed profile
```

### 1.2 Resume Parser Service
**Файл:** `backend/app/services/resume_parser.py`

**Використовує існуючий код з:** `src/resume_analyzer.py`

**Функціонал:**
- Парсинг PDF (PyPDF2)
- Парсинг DOCX (python-docx)
- Витягування структурованої інформації через Azure OpenAI:
  - Особисті дані (ім'я, email, телефон, локація)
  - Досвід роботи (компанії, посади, обов'язки)
  - Освіта
  - Навички (технічні, мовні, soft skills)
  - Сертифікати
  - Кар'єрні цілі

### 1.3 Database Schema
**Файл:** `database/user_profiles_schema.sql`

```sql
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,

  -- Personal Info
  full_name TEXT,
  email TEXT,
  phone TEXT,
  location TEXT,

  -- Professional Summary
  professional_summary TEXT,
  career_objective TEXT,
  total_experience_years INTEGER,

  -- Work Experience (JSON array)
  work_experience JSONB DEFAULT '[]'::jsonb,

  -- Education (JSON array)
  education JSONB DEFAULT '[]'::jsonb,

  -- Skills
  technical_skills TEXT[] DEFAULT ARRAY[]::TEXT[],
  languages TEXT[] DEFAULT ARRAY[]::TEXT[],
  soft_skills TEXT[] DEFAULT ARRAY[]::TEXT[],
  certifications TEXT[] DEFAULT ARRAY[]::TEXT[],

  -- Metadata
  resume_file_url TEXT,
  parsed_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(user_id)
);
```

### 1.4 Frontend - Profile Upload
**Файл:** `web-app/src/pages/Profile.tsx`

**Функціонал:**
- Drag & Drop для PDF/DOCX
- Upload прогрес бар
- Відображення parsed профілю
- Редагування полів
- Збереження змін

---

## Етап 2: AI Evaluator - Оцінка релевантності

### 2.1 Workflow Integration
**Файл:** `worker/worker.py`

**Після скрапінгу вакансії додати:**

```python
def process_scan_task(self, task):
    # 1. Scrape job with Skyvern
    job_data = self.scrape_job(task['url'])

    # 2. Get user profile
    profile = self.get_user_profile(task['user_id'])

    # 3. AI Relevance Analysis
    relevance = self.analyze_relevance(job_data, profile)

    # 4. Save with relevance_score
    job_data['relevance_score'] = relevance['score']
    job_data['relevance_reasons'] = relevance['reasons']
    job_data['recommendation'] = relevance['recommendation']

    self.save_job(job_data)
```

### 2.2 AI Analyzer Service
**Файл:** `worker/services/ai_evaluator.py`

**Використовує:** `src/ai_analyzer.py`

**Промпт для Azure OpenAI:**

```
Ти експерт з HR і карєрного консультування.

ПРОФІЛЬ КАНДИДАТА:
- Професія: {profile.career_objective}
- Досвід: {profile.work_experience}
- Навички: {profile.technical_skills}
- Мови: {profile.languages}

ВАКАНСІЯ:
- Назва: {job.title}
- Компанія: {job.company}
- Опис: {job.description}
- Вимоги: {job.requirements}

ОЦІНИ РЕЛЕВАНТНІСТЬ (0-100%):

Приклади:
- Вихователька → Робітник фабрики = 20% (може фізично працювати, але немає досвіду)
- Вихователька → Диспетчер аеропорта = 0% (повністю різні професії)
- Python Developer → Senior Python Engineer = 90% (відповідає, є досвід)

Поверни JSON:
{
  "relevance_score": 85,
  "is_relevant": true,
  "match_reasons": ["має потрібний досвід", "знає мови"],
  "concerns": ["немає сертифіката X"],
  "recommendation": "APPLY"
}
```

### 2.3 Update Jobs Table
**Файл:** `database/update_jobs_add_relevance.sql`

```sql
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS relevance_score INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS relevance_reasons TEXT[] DEFAULT ARRAY[]::TEXT[];
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT 'PENDING';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMPTZ;
```

### 2.4 Frontend - Jobs Filter by Relevance
**Файл:** `web-app/src/pages/Jobs.tsx`

**Додати:**
- Фільтр по relevance_score (0-20%, 20-50%, 50-80%, 80-100%)
- Сортування по score
- Візуальні індикатори (червоний/жовтий/зелений)
- Badge з відсотком

---

## Етап 3: Автоматичне заповнення форм

### 3.1 Enhanced Skyvern Templates
**Файл:** `worker/skyvern_templates/job_application_template.json`

**Цілі:**
- Розпізнавання різних типів форм (text inputs, selects, checkboxes, radio buttons)
- Автоматичне прийняття cookies/GDPR
- Заповнення стандартних полів:
  - Ім'я, прізвище
  - Email, телефон
  - Адреса
  - CV upload
  - Мотиваційний лист
- Натискання кнопок submit

### 3.2 Application Worker
**Файл:** `worker/services/application_filler.py`

```python
class ApplicationFiller:
    def fill_application(self, job_url, user_profile):
        """Fill job application form using Skyvern"""

        # 1. Prepare form data from profile
        form_data = {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "email": profile.email,
            "phone": profile.phone,
            "cv_file": profile.resume_file_url,
            "cover_letter": self.generate_cover_letter(job, profile)
        }

        # 2. Skyvern task with adaptive form filling
        task = {
            "url": job_url,
            "navigation_goal": "Fill and submit job application",
            "data_extraction_goal": "Extract confirmation message",
            "form_data": form_data,
            "auto_accept_cookies": True,
            "auto_accept_terms": True
        }

        # 3. Execute with Skyvern
        result = self.skyvern_client.run_task(task)

        # 4. Save application record
        self.save_application(job_id, result)
```

### 3.3 Cover Letter Generator
**Файл:** `worker/services/cover_letter_generator.py`

**Використовує:** `src/ai_cover_letter_generator.py`

**Функціонал:**
- Генерація персоналізованого cover letter
- На основі job description + user profile
- Azure OpenAI GPT-4
- Збереження в Supabase Storage

### 3.4 Applications Table
**Файл:** `database/applications_schema.sql`

```sql
CREATE TABLE applications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  job_id UUID REFERENCES jobs NOT NULL,

  status TEXT DEFAULT 'PENDING',
  -- PENDING, APPLYING, SUBMITTED, FAILED

  cover_letter_url TEXT,
  submitted_at TIMESTAMPTZ,
  confirmation_message TEXT,
  screenshot_url TEXT,

  error_message TEXT,
  retry_count INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Етап 4: Dashboard Enhancements

### 4.1 Profile Management Page
**Файл:** `web-app/src/pages/Profile.tsx`

**Секції:**
- Upload Resume (PDF/DOCX)
- View Parsed Profile
- Edit Profile Fields
- Preview Resume

### 4.2 Jobs Page Improvements
**Файл:** `web-app/src/pages/Jobs.tsx`

**Фічі:**
- Relevance Score визуалізація (progress bar)
- Фільтр по AI recommendation (APPLY/REVIEW/SKIP)
- Quick Apply button для high-relevance jobs
- View Application Status

### 4.3 Applications Page
**Файл:** `web-app/src/pages/Applications.tsx`

**Функціонал:**
- List всіх submitted applications
- Статус (Pending/Submitted/Failed)
- Retry failed applications
- View cover letters
- Download confirmations

### 4.4 Analytics Dashboard
**Файл:** `web-app/src/pages/Dashboard.tsx`

**Метрики:**
- Total jobs scanned
- High relevance jobs (>70%)
- Applications submitted
- Success rate
- Charts (Recharts)

---

## Етап 5: Intelligent Form Recognition

### 5.1 Skyvern Multi-Template System
**Папка:** `worker/skyvern_templates/forms/`

**Templates:**
- `finn_no_application.json` - FINN.no специфічна форма
- `nav_no_application.json` - NAV.no форма
- `generic_job_form.json` - Загальна форма
- `linkedin_easy_apply.json` - LinkedIn Easy Apply

**Адаптивний підхід:**
```python
def detect_form_type(url, page_html):
    """Detect which template to use based on URL and page structure"""

    if 'finn.no' in url:
        return 'finn_no_application'
    elif 'nav.no' in url:
        return 'nav_no_application'
    elif 'linkedin.com' in url:
        return 'linkedin_easy_apply'
    else:
        # Use AI to analyze form structure
        return analyze_form_with_ai(page_html)
```

### 5.2 Cookies & Consent Handler
**Файл:** `worker/services/consent_handler.py`

**Skyvern goals:**
```json
{
  "pre_navigation_goals": [
    "Accept all cookies if banner appears",
    "Accept privacy policy if required",
    "Accept terms and conditions if checkbox present"
  ]
}
```

**Універсальні селектори:**
- "Accept all", "Godta alle", "Aksepter"
- Cookies banner dismiss buttons
- GDPR consent checkboxes

---

## Етап 6: Testing & Quality Assurance

### 6.1 Test Jobs List
**Файл:** `worker/test_jobs.json`

```json
[
  {
    "title": "Python Developer",
    "url": "https://finn.no/job/...",
    "expected_relevance": 85
  },
  {
    "title": "Factory Worker",
    "url": "https://finn.no/job/...",
    "expected_relevance": 20
  }
]
```

### 6.2 End-to-End Test
**Файл:** `tests/e2e_test.py`

**Workflow:**
1. Upload test resume (PDF)
2. Verify profile parsed correctly
3. Trigger job scan
4. Verify jobs scraped
5. Verify relevance scores calculated
6. Test application submission (dry-run)
7. Verify application saved

---

## Розгортання і налаштування

### Environment Variables

**Backend (Cloud Run):**
```bash
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=...
OPENAI_ENDPOINT=https://elvarika.openai.azure.com
OPENAI_KEY=...
AZURE_OPENAI_DEPLOYMENT_CHAT=gpt-4
```

**Worker (Local PC):**
```bash
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=...
SKYVERN_API_URL=http://localhost:8000
OPENAI_ENDPOINT=https://elvarika.openai.azure.com
OPENAI_KEY=...
```

**Frontend (Netlify):**
```bash
VITE_SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
VITE_SUPABASE_ANON_KEY=...
VITE_API_URL=https://jobbot-backend-255588880592.us-central1.run.app
```

---

## Пріоритети реалізації

### Фаза 1 (Необхідний мінімум):
1. ✅ PDF Parser + Profile Storage
2. ✅ AI Relevance Scoring (інтеграція в Worker)
3. ✅ Jobs table update (relevance_score field)
4. ✅ Profile page в Dashboard

### Фаза 2 (Автоматизація):
5. ✅ Cover Letter Generator
6. ✅ Application Filler (Skyvern)
7. ✅ Applications tracking
8. ✅ Enhanced Skyvern templates

### Фаза 3 (Покращення):
9. ⏳ Multi-form recognition
10. ⏳ Cookies/Consent automation
11. ⏳ Analytics dashboard
12. ⏳ Email/Telegram notifications

---

## Технічні рішення

### PDF Parsing
**Бібліотека:** PyPDF2 + python-docx
**AI:** Azure OpenAI GPT-4
**Чому:** Вже використовується в проекті, добре справляється з structured extraction

### AI Relevance Scoring
**Модель:** Azure OpenAI GPT-4
**Промпт:** Few-shot learning з прикладами (вихователька → різні вакансії)
**Шкала:** 0-100%

### Form Filling
**Інструмент:** Skyvern
**Чому:**
- AI-powered (GPT-4V)
- Адаптується до змін UI
- Розуміє різні типи форм
- Вже інтегровано в проект

### Storage
**Files:** Supabase Storage (PDFs, cover letters, screenshots)
**Database:** PostgreSQL (Supabase)
**Чому:** Все в одному місці, integrated auth, RLS security

---

## Часові оцінки

- **Фаза 1:** 6-8 годин (базова інтеграція)
- **Фаза 2:** 8-10 годин (автоматизація applications)
- **Фаза 3:** 6-8 годин (покращення UX)

**Загалом:** 20-26 годин розробки

---

## Ризики і мітігація

### Ризик 1: AI може неправильно оцінити релевантність
**Мітігація:**
- Few-shot prompting з багатьма прикладами
- Manual override в UI
- Feedback loop для покращення

### Ризик 2: Skyvern може не розпізнати складні форми
**Мітігація:**
- Множинні templates для популярних сайтів
- Fallback to manual application
- Логування проблемних форм для аналізу

### Ризик 3: Anti-bot захист на сайтах
**Мітігація:**
- Skyvern використовує real browser
- Random delays between actions
- Rotate user agents

---

**Автор:** Claude Code
**Версія:** 1.0
**Дата:** 2025-11-10
