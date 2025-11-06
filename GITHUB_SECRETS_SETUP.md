# GitHub Secrets - Налаштування

Відкрий: https://github.com/SmmShaman/jobbot-norway-public/settings/secrets/actions

Натисни **"New repository secret"** для кожного:

---

## 🔑 Google Cloud Secrets

### 1. GCP_PROJECT_ID
**Name:** `GCP_PROJECT_ID`
**Value:**
```
jobbot-claude
```

### 2. GCP_SA_KEY
**Name:** `GCP_SA_KEY`
**Value:** (Скопіюй ВЕСЬ JSON з Cloud Shell команди `cat ~/key.json`)

```json
{
  "type": "service_account",
  "project_id": "jobbot-claude",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "github-actions@jobbot-claude.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

---

## 🗄️ Supabase Secrets

> **Отримати значення:** Відкрий `/home/user/jobbot-norway-public/RENDER_ENV_VARS.txt`

### 3. SUPABASE_URL
**Name:** `SUPABASE_URL`
**Value:** `https://ptrmidlhfdbybxmyovtm.supabase.co`

### 4. SUPABASE_SERVICE_KEY
**Name:** `SUPABASE_SERVICE_KEY`
**Value:** (з файлу RENDER_ENV_VARS.txt, рядок SUPABASE_SERVICE_KEY)

### 5. SUPABASE_JWT_SECRET
**Name:** `SUPABASE_JWT_SECRET`
**Value:** (з файлу RENDER_ENV_VARS.txt)

---

## 🤖 Azure OpenAI Secrets

> **Отримати значення:** Відкрий `/home/user/jobbot-norway-public/RENDER_ENV_VARS.txt`

### 6. AZURE_OPENAI_ENDPOINT
**Name:** `AZURE_OPENAI_ENDPOINT`
**Value:** (з файлу RENDER_ENV_VARS.txt)

### 7. AZURE_OPENAI_KEY
**Name:** `AZURE_OPENAI_KEY`
**Value:** (з файлу RENDER_ENV_VARS.txt)

### 8. AZURE_OPENAI_DEPLOYMENT
**Name:** `AZURE_OPENAI_DEPLOYMENT`
**Value:** `Jobbot-gpt-4.1-mini`

### 9. AZURE_OPENAI_API_VERSION
**Name:** `AZURE_OPENAI_API_VERSION`
**Value:** `2024-12-01-preview`

---

## 🔐 Security Secrets

> **Отримати значення:** Відкрий `/home/user/jobbot-norway-public/RENDER_ENV_VARS.txt`

### 10. ENCRYPTION_KEY
**Name:** `ENCRYPTION_KEY`
**Value:** (з файлу RENDER_ENV_VARS.txt)

### 11. JWT_SECRET
**Name:** `JWT_SECRET`
**Value:** (з файлу RENDER_ENV_VARS.txt)

---

## 📱 Integration Secrets

> **Отримати значення:** Відкрий `/home/user/jobbot-norway-public/RENDER_ENV_VARS.txt`

### 12. TELEGRAM_BOT_TOKEN
**Name:** `TELEGRAM_BOT_TOKEN`
**Value:** (з файлу RENDER_ENV_VARS.txt)

### 13. SPACY_API_KEY
**Name:** `SPACY_API_KEY`
**Value:** (з файлу RENDER_ENV_VARS.txt)

### 14. SKYVERN_API_URL
**Name:** `SKYVERN_API_URL`
**Value:** `http://localhost:8000`

---

## ✅ Перевірка

Після додавання всіх 14 secrets, перевір:

1. Відкрий https://github.com/SmmShaman/jobbot-norway-public/settings/secrets/actions
2. Маєш бачити 14 secrets:
   - GCP_PROJECT_ID
   - GCP_SA_KEY
   - SUPABASE_URL
   - SUPABASE_SERVICE_KEY
   - SUPABASE_JWT_SECRET
   - AZURE_OPENAI_ENDPOINT
   - AZURE_OPENAI_KEY
   - AZURE_OPENAI_DEPLOYMENT
   - AZURE_OPENAI_API_VERSION
   - ENCRYPTION_KEY
   - JWT_SECRET
   - TELEGRAM_BOT_TOKEN
   - SPACY_API_KEY
   - SKYVERN_API_URL

---

## 🚀 Наступний крок

Після додавання всіх secrets, просто зміни будь-який файл в `backend/` і запуш:

```bash
# Зробити тестову зміну
echo "# Cloud Run ready" >> backend/README.md

# Закомітити
git add .
git commit -m "Test Cloud Run deployment"
git push
```

GitHub Action автоматично запуститься і задеплоїть на Cloud Run!

Моніторинг: https://github.com/SmmShaman/jobbot-norway-public/actions
