# 🚀 Google Cloud Run - Чек-лист деплою

## ☑️ Кроки налаштування

### Крок 1: Cloud Shell команди
📄 Файл: `CLOUD_SHELL_COMMANDS.md`

- [ ] Відкрити Cloud Shell: https://console.cloud.google.com/?project=jobbot-claude
- [ ] Скопіювати і запустити всі команди з файлу
- [ ] Зберегти JSON ключ (вивід команди `cat ~/key.json`)

### Крок 2: GitHub Secrets
📄 Файл: `GITHUB_SECRETS_SETUP.md`

Відкрити: https://github.com/SmmShaman/jobbot-norway-public/settings/secrets/actions

**Google Cloud (2 secrets):**
- [ ] `GCP_PROJECT_ID` = `jobbot-claude`
- [ ] `GCP_SA_KEY` = JSON ключ з Cloud Shell

**Supabase (3 secrets):**
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_SERVICE_KEY`
- [ ] `SUPABASE_JWT_SECRET`

**Azure OpenAI (4 secrets):**
- [ ] `AZURE_OPENAI_ENDPOINT`
- [ ] `AZURE_OPENAI_KEY`
- [ ] `AZURE_OPENAI_DEPLOYMENT`
- [ ] `AZURE_OPENAI_API_VERSION`

**Security (2 secrets):**
- [ ] `ENCRYPTION_KEY`
- [ ] `JWT_SECRET`

**Integrations (3 secrets):**
- [ ] `TELEGRAM_BOT_TOKEN`
- [ ] `SPACY_API_KEY`
- [ ] `SKYVERN_API_URL`

**Всього: 14 secrets** ✅

### Крок 3: Перший деплой

- [ ] Зробити тестову зміну в `backend/`
- [ ] Закомітити і запушити
- [ ] Перевірити GitHub Actions: https://github.com/SmmShaman/jobbot-norway-public/actions
- [ ] Зачекати ~5-10 хвилин (перший білд довший)
- [ ] Переконатись що деплой успішний ✅

### Крок 4: Отримати Cloud Run URL

Варіант 1 (Cloud Shell):
```bash
gcloud run services describe jobbot-backend \
  --region europe-west1 \
  --format 'value(status.url)'
```

Варіант 2 (консоль):
- [ ] Відкрити: https://console.cloud.google.com/run?project=jobbot-claude
- [ ] Знайти `jobbot-backend`
- [ ] Скопіювати URL (наприклад: `https://jobbot-backend-xxx-ew.a.run.app`)

### Крок 5: Оновити Netlify

- [ ] Відкрити: https://app.netlify.com/sites/jobbotnetlify/configuration/env
- [ ] Знайти `VITE_API_URL`
- [ ] Змінити на Cloud Run URL
- [ ] **Save** → Netlify автоматично редеплоїть

### Крок 6: Протестувати систему

- [ ] Відкрити: https://jobbotnetlify.netlify.app
- [ ] Залогінитись: `test@jobbot.no` / `Test123456`
- [ ] Натиснути "Scan Jobs Now"
- [ ] Переконатись що працює БЕЗ холодного старту ⚡

---

## 🎯 Статус

**Frontend:** ✅ https://jobbotnetlify.netlify.app
**Backend:** ⏳ Очікує деплою на Cloud Run
**Database:** ✅ Supabase
**AI:** ✅ Azure OpenAI GPT-4

---

## 🔍 Моніторинг

**GitHub Actions:**
https://github.com/SmmShaman/jobbot-norway-public/actions

**Cloud Run Logs:**
https://console.cloud.google.com/run/detail/europe-west1/jobbot-backend/logs?project=jobbot-claude

**Cloud Run Metrics:**
https://console.cloud.google.com/run/detail/europe-west1/jobbot-backend/metrics?project=jobbot-claude

---

## 💰 Вартість

**Поточна конфігурація:**
- `--min-instances 1` = Завжди активний
- 1 GB RAM + 1 vCPU
- **~$30/місяць** (але перші 2M requests безкоштовно)

**Як зменшити до $0:**
Змінити в `.github/workflows/cloudrun-deploy.yml`:
```yaml
--min-instances 0  # Замість 1
```

Це додасть ~10 сек холодний старт, але все одно швидше ніж Render.

---

## ❓ Проблеми?

**Деплой падає?**
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 50 --project jobbot-claude
```

**Змінити env var:**
```bash
gcloud run services update jobbot-backend \
  --region europe-west1 \
  --set-env-vars "DEBUG=true" \
  --project jobbot-claude
```

**Редеплой вручну:**
```bash
gcloud run deploy jobbot-backend \
  --image gcr.io/jobbot-claude/jobbot-backend:latest \
  --region europe-west1 \
  --project jobbot-claude
```
