# Supabase Edge Functions

Serverless functions для JobBot Norway, що працюють в Supabase cloud.

## 📁 Functions Overview

| Function | Призначення | Trigger |
|----------|-------------|---------|
| `pdf-parser` | Парсинг PDF резюме через Azure OpenAI GPT-4 | Manual (POST request) |
| `ai-evaluator` | AI оцінка релевантності вакансії (0-100%) | Manual or Automatic after scraping |
| `telegram-notify` | Telegram сповіщення про релевантні вакансії | Automatic when job relevance > 70% |
| `job-scraper` | (TODO) FINN.no scraping без локального Worker | Scheduled or Manual |

---

## 🚀 Quick Start

### 1. Install Supabase CLI

```bash
npm install -g supabase
# or
brew install supabase/tap/supabase
```

### 2. Login & Link Project

```bash
supabase login
supabase link --project-ref ptrmidlhfdbybxmyovtm
```

### 3. Set Secrets

```bash
supabase secrets set AZURE_OPENAI_ENDPOINT=https://...
supabase secrets set AZURE_OPENAI_API_KEY=your_key
supabase secrets set AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
supabase secrets set TELEGRAM_BOT_TOKEN=your_token
```

### 4. Deploy Functions

```bash
# Deploy all
supabase functions deploy

# Or deploy individual
supabase functions deploy pdf-parser
supabase functions deploy ai-evaluator
supabase functions deploy telegram-notify
```

### 5. Test Functions

```bash
# Test locally
supabase functions serve pdf-parser

# View logs
supabase functions logs pdf-parser --follow
```

---

## 📖 Function Details

### pdf-parser

**Purpose:** Parse uploaded PDF/DOCX resume and extract structured profile.

**Request:**
```json
{
  "file_url": "https://supabase.co/storage/v1/object/resumes/user.pdf",
  "user_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "profile": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "technical_skills": ["Python", "JavaScript"],
    "work_experience": [...]
  }
}
```

**Saves to:** `user_profiles` table

---

### ai-evaluator

**Purpose:** Evaluate job relevance against user profile using AI.

**Request:**
```json
{
  "job_id": "uuid",
  "user_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "relevance": {
    "relevance_score": 85,
    "is_relevant": true,
    "match_reasons": ["має Python досвід", "знає Norwegian"],
    "concerns": ["немає AWS сертифіката"],
    "recommendation": "APPLY"
  }
}
```

**Updates:** `jobs` table with relevance_score, relevance_reasons, ai_recommendation

**Scoring:**
- 80-100%: APPLY (ідеальний матч)
- 50-79%: REVIEW (частково підходить)
- 0-49%: SKIP (не релевантний)

---

### telegram-notify

**Purpose:** Send Telegram notifications about new relevant jobs.

**Request (new_job):**
```json
{
  "chat_id": "123456789",
  "type": "new_job",
  "job": {
    "title": "Python Developer",
    "company": "Tech Corp",
    "relevance_score": 90,
    "ai_recommendation": "APPLY",
    "url": "https://finn.no/job/123"
  }
}
```

**Request (daily_summary):**
```json
{
  "chat_id": "123456789",
  "type": "daily_summary",
  "job": {
    "total_jobs": 50,
    "relevant_jobs": 15,
    "applications_sent": 5
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notification sent successfully"
}
```

---

## 🔒 Environment Variables (Secrets)

**Required secrets:**

| Secret | Description | Where to get |
|--------|-------------|--------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Azure Portal |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Azure Portal |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name (e.g., gpt-4.1-mini) | Azure Portal |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | @BotFather |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service key (for DB access) | Supabase Dashboard |

**Set via CLI:**

```bash
supabase secrets set SECRET_NAME=value
```

**List secrets:**

```bash
supabase secrets list
```

---

## 🧪 Testing

### Test Locally

```bash
# Start local Supabase (optional)
supabase start

# Serve function locally
supabase functions serve pdf-parser

# Test with curl
curl -X POST \
  'http://localhost:54321/functions/v1/pdf-parser' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"file_url": "https://...", "user_id": "..."}'
```

### Test Production

```bash
curl -X POST \
  'https://ptrmidlhfdbybxmyovtm.functions.supabase.co/pdf-parser' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"file_url": "https://...", "user_id": "..."}'
```

---

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
supabase functions logs pdf-parser --follow

# Last 50 entries
supabase functions logs pdf-parser --limit 50

# All functions
supabase functions logs
```

### Metrics

View in Supabase Dashboard:
https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/functions

---

## 🐛 Common Issues

### "Missing secret" error

```bash
# Verify secrets are set
supabase secrets list

# Re-set if missing
supabase secrets set AZURE_OPENAI_API_KEY=your_key
```

### CORS errors

All functions include CORS headers by default:

```typescript
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}
```

### Function timeout

Edge Functions have 150 second timeout. For long operations, use database queue pattern.

---

## 📚 Resources

- [Supabase Edge Functions Docs](https://supabase.com/docs/guides/functions)
- [Azure OpenAI API Docs](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

**See also:** `/CLOUD_DEPLOYMENT_GUIDE.md` for full deployment instructions
