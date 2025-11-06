# 🚀 Google Cloud Run - Швидкий старт

**Project:** https://console.cloud.google.com/?project=jobbot-claude

---

## Крок 1: Cloud Shell (5 хв)

1. **Відкрий Cloud Shell:** https://console.cloud.google.com/?project=jobbot-claude
2. **Натисни кнопку `>_`** вгорі справа
3. **Скопіюй і запусти команди** з файлу:
   ```
   CLOUD_SHELL_COMMANDS.md
   ```
4. **Збережи JSON ключ** (вивід команди `cat ~/key.json`)

---

## Крок 2: GitHub Secrets (10 хв)

**Відкрий:** https://github.com/SmmShaman/jobbot-norway-public/settings/secrets/actions

**Додай 14 secrets** (детальна інструкція в файлі `GITHUB_SECRETS_SETUP.md`):

**Швидкий список:**
1. `GCP_PROJECT_ID` = `jobbot-claude`
2. `GCP_SA_KEY` = JSON з Cloud Shell
3-14. Решта значень з файлу `/home/user/jobbot-norway-public/RENDER_ENV_VARS.txt`

**Secrets потрібні:**
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

## Крок 3: Запустити деплой (2 хв)

Після додавання всіх secrets:

```bash
# Зробити тестову зміну
echo "# Ready for Cloud Run" >> backend/README.md

# Закомітити і запушити
git add .
git commit -m "🚀 Deploy to Cloud Run"
git push
```

**Моніторинг:** https://github.com/SmmShaman/jobbot-norway-public/actions

⏱️ Перший білд займе ~8-12 хвилин

---

## Крок 4: Отримати URL (1 хв)

Після успішного деплою, в Cloud Shell:

```bash
gcloud run services describe jobbot-backend \
  --region europe-west1 \
  --format 'value(status.url)'
```

Або консоль: https://console.cloud.google.com/run?project=jobbot-claude

---

## Крок 5: Оновити Netlify (1 хв)

1. **Відкрий:** https://app.netlify.com/sites/jobbotnetlify/configuration/env
2. **Знайди** `VITE_API_URL`
3. **Зміни на** Cloud Run URL (з кроку 4)
4. **Save** → автоматичний редеплой

---

## Крок 6: Тест ✅

**Відкрий:** https://jobbotnetlify.netlify.app

**Логін:**
- Email: `test@jobbot.no`
- Password: `Test123456`

**Натисни:** "Scan Jobs Now"

✅ **Має працювати БЕЗ холодного старту!** ⚡

---

## 📚 Детальні інструкції:

- **Команди Cloud Shell:** `CLOUD_SHELL_COMMANDS.md`
- **GitHub Secrets:** `GITHUB_SECRETS_SETUP.md`
- **Чек-лист:** `DEPLOYMENT_CHECKLIST.md`
- **Повна документація:** `GOOGLE_CLOUD_SETUP.md`

---

## 💰 Вартість

**Поточна конфігурація:**
- 🟢 `--min-instances 1` = Завжди активний, БЕЗ холодного старту
- 💵 ~$30/місяць (але 2M requests безкоштовно)

**Безкоштовний варіант:**
- Зміни `--min-instances 0` в `.github/workflows/cloudrun-deploy.yml`
- Холодний старт ~10 сек (все одно швидше Render)

---

## ❓ Проблеми?

**GitHub Action падає?**
- Перевір чи всі 14 secrets додані
- Подивись логи: https://github.com/SmmShaman/jobbot-norway-public/actions

**Backend не працює?**
```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --project jobbot-claude
```

**Написати мені:** GitHub Issues або створити новий коміт з описом проблеми
