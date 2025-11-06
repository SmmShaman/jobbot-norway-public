# Google Cloud Run - Quick Setup

## Переваги над Render
✅ **Немає холодного старту** (min-instances=1)
✅ Free tier: 2M requests/місяць
✅ Швидкий і стабільний
✅ Автоскейлінг 1-10 інстансів

---

## 1️⃣ Створи Google Cloud Project

1. Відкрий https://console.cloud.google.com/
2. **Create Project** → Назва: `jobbot-norway`
3. Запиши **Project ID** (наприклад: `jobbot-norway-123456`)

---

## 2️⃣ Увімкни API

Запусти в Cloud Shell (кнопка `>_` вгорі):

```bash
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com
```

---

## 3️⃣ Створи Service Account

```bash
# Створити Service Account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# Дати права
gcloud projects add-iam-policy-binding jobbot-norway-123456 \
  --member="serviceAccount:github-actions@jobbot-norway-123456.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding jobbot-norway-123456 \
  --member="serviceAccount:github-actions@jobbot-norway-123456.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding jobbot-norway-123456 \
  --member="serviceAccount:github-actions@jobbot-norway-123456.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Створити JSON ключ
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@jobbot-norway-123456.iam.gserviceaccount.com

# Показати вміст (скопіюй ВЕСЬ JSON)
cat key.json
```

---

## 4️⃣ GitHub Secrets

Додай в https://github.com/SmmShaman/jobbot-norway-public/settings/secrets/actions:

### **GCP_PROJECT_ID**
```
jobbot-norway-123456
```

### **GCP_SA_KEY**
```json
{
  "type": "service_account",
  "project_id": "jobbot-norway-123456",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "github-actions@jobbot-norway-123456.iam.gserviceaccount.com",
  ...
}
```

### Також додай всі env vars як GitHub Secrets:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_KEY`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION`
- `ENCRYPTION_KEY`
- `JWT_SECRET`
- `TELEGRAM_BOT_TOKEN`
- `SPACY_API_KEY`
- `SKYVERN_API_URL`

*(Значення візьми з `/home/user/jobbot-norway-public/RENDER_ENV_VARS.txt`)*

---

## 5️⃣ Перший Деплой

Просто запуш код:

```bash
git add .
git commit -m "🚀 Switch to Google Cloud Run"
git push origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
```

GitHub Action автоматично задеплоїть на Cloud Run!

---

## 6️⃣ Отримай URL

Після деплою:
```bash
gcloud run services describe jobbot-backend \
  --region europe-west1 \
  --format 'value(status.url)'
```

Або подивись в консолі: https://console.cloud.google.com/run

---

## 7️⃣ Оновити Netlify

В Netlify env vars зміни `VITE_API_URL` на Cloud Run URL:
```
https://jobbot-backend-xxx-ew.a.run.app
```

---

## 💰 Вартість

**Free Tier (завжди безкоштовно):**
- 2 million requests/місяць
- 360,000 GB-seconds memory
- 180,000 vCPU-seconds

**Min-instances=1** (завжди активний):
- ~$30/місяць для 1 інстансу 1GB RAM + 1 vCPU 24/7
- Але перші 2M requests - безкоштовно

**Можна зменшити до $0:**
- Встанови `--min-instances 0` в workflow
- Буде холодний старт ~10 сек (швидше ніж Render)

---

## 🔍 Моніторинг

- Logs: https://console.cloud.google.com/run/detail/europe-west1/jobbot-backend/logs
- Metrics: https://console.cloud.google.com/run/detail/europe-west1/jobbot-backend/metrics

---

## ❓ Troubleshooting

**Деплой падає?**
```bash
gcloud run services describe jobbot-backend --region europe-west1
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

**Змінити env var вручну:**
```bash
gcloud run services update jobbot-backend \
  --region europe-west1 \
  --set-env-vars "DEBUG=true"
```

**Переглянути всі env vars:**
```bash
gcloud run services describe jobbot-backend \
  --region europe-west1 \
  --format 'value(spec.template.spec.containers[0].env)'
```
