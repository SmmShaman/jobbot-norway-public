# ☁️ Cloud Deployment Guide - БЕЗ Локального ПК

**Дата:** 2025-11-10
**Мета:** Налаштувати JobBot Norway повністю в cloud без необхідності запускати Worker на локальному ПК

---

## 🎯 Нова Архітектура (100% Cloud)

```
┌─────────────────────────────────────────────────────────────┐
│                    КОРИСТУВАЧ (Browser)                     │
│              https://jobbot-norway.netlify.app              │
└────────────────────────┬────────────────────────────────────┘
                         │
           ┌─────────────┴──────────────┐
           │                            │
    ┌──────▼───────┐          ┌────────▼────────┐
    │   Frontend   │          │    Backend      │
    │   (Netlify)  │◄────────►│  (Cloud Run)    │
    └──────┬───────┘          └────────┬────────┘
           │                            │
           └──────────┬─────────────────┘
                      │
           ┌──────────▼──────────┐
           │   SUPABASE          │
           │  - PostgreSQL DB    │
           │  - Edge Functions   │
           │  - Storage          │
           └──────────┬──────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
  ┌─────▼────┐  ┌────▼─────┐  ┌───▼──────┐
  │  Azure   │  │ Telegram │  │Browserless│
  │  OpenAI  │  │   Bot    │  │  (Optional)│
  └──────────┘  └──────────┘  └───────────┘
```

**Ключові зміни:**
- ❌ Немає локального Worker на ПК
- ✅ Все працює в Supabase Edge Functions
- ✅ Azure OpenAI для AI аналізу
- ✅ Telegram bot для notifications
- ✅ Browserless.io (опціонально) для browser automation

---

## 📦 Компоненти системи

### 1. Supabase Edge Functions (Serverless)

**Створені функції:**

| Function | Призначення | API |
|----------|-------------|-----|
| `pdf-parser` | Парсинг PDF резюме через Azure OpenAI | POST /functions/v1/pdf-parser |
| `ai-evaluator` | Оцінка релевантності вакансії (0-100%) | POST /functions/v1/ai-evaluator |
| `telegram-notify` | Telegram сповіщення про нові вакансії | POST /functions/v1/telegram-notify |
| `job-scraper` | (TODO) Scraping вакансій з FINN.no | POST /functions/v1/job-scraper |

### 2. Database Tables

| Table | Призначення |
|-------|-------------|
| `user_profiles` | Parsed резюме користувача |
| `jobs` | Вакансії з relevance_score |
| `scan_tasks` | (legacy - може не знадобитися) |
| `applications` | (Phase 2) Подані заявки |

---

## 🚀 Крок 1: Встановити Supabase CLI

```bash
# MacOS/Linux
brew install supabase/tap/supabase

# Or via npm
npm install -g supabase

# Verify installation
supabase --version
```

---

## 🔑 Крок 2: Налаштувати Secrets в Supabase

**⚠️ ВАЖЛИВО:** Ці ключі НЕ ЗБЕРІГАЮТЬСЯ в git! Тільки в Supabase secrets.

### 2.1 Login до Supabase

```bash
supabase login
```

### 2.2 Link до вашого проекту

```bash
cd ~/jobbot-norway-public
supabase link --project-ref ptrmidlhfdbybxmyovtm
```

### 2.3 Налаштувати secrets

**Azure OpenAI Secrets:**

```bash
# Azure OpenAI Endpoint (user will provide their endpoint)
supabase secrets set AZURE_OPENAI_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com

# Azure OpenAI API Key (user will provide their key)
supabase secrets set AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here

# Azure OpenAI Deployment Name
supabase secrets set AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
```

**Telegram Bot Token:**

```bash
supabase secrets set TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

**⚠️ ВАЖЛИВО:** Використовуйте власні ключі! Не публікуйте їх в git!

**Supabase Service Key:**

```bash
# Get from: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/settings/api
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

### 2.4 Verify secrets

```bash
supabase secrets list
```

**Expected output:**
```
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY
AZURE_OPENAI_DEPLOYMENT
TELEGRAM_BOT_TOKEN
SUPABASE_SERVICE_ROLE_KEY
```

---

## 📊 Крок 3: Створити Database Tables

### 3.1 Create user_profiles table

```bash
# Open Supabase SQL Editor:
# https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new

# Copy and execute content from:
# database/user_profiles_schema.sql
```

Або через CLI:

```bash
supabase db reset  # Reset local DB (optional)
supabase db push   # Push migrations to remote
```

### 3.2 Update jobs table with relevance fields

```bash
# Execute SQL from:
# database/update_jobs_add_relevance_fields.sql
```

---

## 🚀 Крок 4: Deploy Edge Functions

### 4.1 Deploy всі функції

```bash
cd ~/jobbot-norway-public

# Deploy всі функції одночасно
supabase functions deploy pdf-parser
supabase functions deploy ai-evaluator
supabase functions deploy telegram-notify

# Or deploy all at once:
supabase functions deploy
```

### 4.2 Verify deployment

```bash
# List deployed functions
supabase functions list
```

**Expected output:**
```
┌─────────────────┬────────┬─────────────────────────────────────────┐
│ Name            │ Status │ URL                                     │
├─────────────────┼────────┼─────────────────────────────────────────┤
│ pdf-parser      │ active │ https://[project].functions.supabase.co/pdf-parser      │
│ ai-evaluator    │ active │ https://[project].functions.supabase.co/ai-evaluator    │
│ telegram-notify │ active │ https://[project].functions.supabase.co/telegram-notify │
└─────────────────┴────────┴─────────────────────────────────────────┘
```

---

## 🧪 Крок 5: Test Edge Functions

### 5.1 Test PDF Parser

```bash
curl -X POST \
  'https://ptrmidlhfdbybxmyovtm.functions.supabase.co/pdf-parser' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "file_url": "https://example.com/resume.pdf",
    "user_id": "user-uuid-here"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "profile": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "technical_skills": ["Python", "JavaScript"],
    ...
  },
  "message": "Resume parsed successfully"
}
```

### 5.2 Test AI Evaluator

```bash
curl -X POST \
  'https://ptrmidlhfdbybxmyovtm.functions.supabase.co/ai-evaluator' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_id": "job-uuid-here",
    "user_id": "user-uuid-here"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "relevance": {
    "relevance_score": 85,
    "is_relevant": true,
    "match_reasons": ["має Python досвід", "знає Norwegian"],
    "recommendation": "APPLY"
  }
}
```

### 5.3 Test Telegram Notification

```bash
curl -X POST \
  'https://ptrmidlhfdbybxmyovtm.functions.supabase.co/telegram-notify' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "chat_id": "YOUR_TELEGRAM_CHAT_ID",
    "type": "new_job",
    "job": {
      "title": "Python Developer",
      "company": "Tech Corp",
      "relevance_score": 90,
      "ai_recommendation": "APPLY",
      "url": "https://finn.no/job/123"
    }
  }'
```

---

## 🔗 Крок 6: Інтеграція з Frontend

### 6.1 Update Frontend API client

**Файл:** `web-app/src/lib/api.ts`

```typescript
// Add Edge Functions endpoints
export const edgeFunctions = {
  parseResume: async (fileUrl: string, userId: string) => {
    const { data, error } = await supabase.functions.invoke('pdf-parser', {
      body: { file_url: fileUrl, user_id: userId }
    })
    return { data, error }
  },

  evaluateJob: async (jobId: string, userId: string) => {
    const { data, error } = await supabase.functions.invoke('ai-evaluator', {
      body: { job_id: jobId, user_id: userId }
    })
    return { data, error }
  },

  sendTelegramNotification: async (chatId: string, job: any) => {
    const { data, error } = await supabase.functions.invoke('telegram-notify', {
      body: { chat_id: chatId, type: 'new_job', job }
    })
    return { data, error }
  }
}
```

### 6.2 Update Environment Variables

**Netlify Dashboard:**
https://app.netlify.com/sites/jobbot-norway/configuration/env

**Додати:**
```bash
VITE_SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
```

---

## 📱 Крок 7: Налаштувати Telegram Bot

### 7.1 Get your Chat ID

1. Відкрий Telegram
2. Знайди бота: `@soknad_bot`
3. Натисни `/start`
4. Надішли `/chatid`
5. Бот поверне твій chat_id

### 7.2 Save Chat ID в Settings

**В Dashboard додати поле:**
- Settings → Telegram Chat ID: `ваш_chat_id`

**Database update:**

```sql
ALTER TABLE settings
ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT;
```

---

## 🔄 Крок 8: Workflow Integration

### Повний workflow:

```
1. User uploads PDF resume
   ↓
2. Frontend → Edge Function (pdf-parser)
   ↓
3. Azure OpenAI parses resume
   ↓
4. Save to user_profiles table
   ↓
5. User clicks "Scan Jobs"
   ↓
6. Backend scrapes FINN.no (через job-scraper function)
   ↓
7. For each job → Edge Function (ai-evaluator)
   ↓
8. Azure OpenAI calculates relevance (0-100%)
   ↓
9. Update jobs table with relevance_score
   ↓
10. If relevance > 70% → Edge Function (telegram-notify)
   ↓
11. User sees jobs in Dashboard sorted by relevance
```

---

## 💰 Cost Estimation (Monthly)

### Supabase
- **Free tier:** 500MB Database, 2GB Storage, 2M Edge Function invocations
- **Pro tier ($25/mo):** 8GB Database, 100GB Storage, unlimited functions

### Azure OpenAI
- **GPT-4-mini:** ~$0.0001 per 1K tokens
- **Estimated:** 100 jobs/day × 2K tokens = $0.02/day = $0.60/month

### Browserless (if needed)
- **Free tier:** 6 hours/month
- **Paid:** $29/month unlimited

**Total (без Browserless):** $0-25/month залежно від Supabase tier

---

## 🐛 Troubleshooting

### Error: "Function deployment failed"

```bash
# Check logs
supabase functions logs pdf-parser --limit 50

# Redeploy
supabase functions deploy pdf-parser --no-verify-jwt
```

### Error: "Missing secret"

```bash
# Verify secrets are set
supabase secrets list

# Re-set missing secret
supabase secrets set AZURE_OPENAI_API_KEY=your_key_here
```

### Error: "CORS blocked"

**Fix in Edge Function:**
```typescript
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// Add to all responses
return new Response(data, { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
```

---

## 📚 Useful Commands

```bash
# View function logs
supabase functions logs pdf-parser --follow

# Test locally
supabase functions serve pdf-parser

# List secrets
supabase secrets list

# Unset secret
supabase secrets unset SECRET_NAME

# Database migrations
supabase db diff -f new_migration
supabase db push
```

---

## ✅ Checklist

- [ ] Supabase CLI встановлено
- [ ] Logged in: `supabase login`
- [ ] Linked project: `supabase link`
- [ ] Secrets налаштовані (5 secrets)
- [ ] Database tables створені (user_profiles, jobs updated)
- [ ] Edge Functions deployed (3 functions)
- [ ] Edge Functions tested (curl tests pass)
- [ ] Frontend updated (api.ts)
- [ ] Telegram bot налаштований (chat_id отримано)
- [ ] E2E test workflow (upload PDF → scan jobs → get notifications)

---

## 🎉 Done!

Тепер ваш JobBot Norway працює **100% в cloud** без необхідності запускати Worker на локальному ПК!

**Next steps:**
1. Створити Profile page в Dashboard
2. Додати relevance filtering в Jobs page
3. Налаштувати автоматичні сповіщення в Telegram
4. (Phase 2) Додати автоматичне заповнення форм

---

**Автор:** Claude Code
**Версія:** 1.0
**Дата:** 2025-11-10
