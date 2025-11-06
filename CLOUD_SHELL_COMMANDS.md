# Google Cloud Shell - Команди для налаштування

Скопіюй і запусти ці команди в Cloud Shell (кнопка `>_` вгорі справа):

---

## 1️⃣ Встановити Project ID

```bash
gcloud config set project jobbot-claude
```

---

## 2️⃣ Увімкнути необхідні API

```bash
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

*(Зачекай ~1 хвилину)*

---

## 3️⃣ Створити Service Account для GitHub

```bash
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deploy"
```

---

## 4️⃣ Дати права Service Account

```bash
# Cloud Run Admin
gcloud projects add-iam-policy-binding jobbot-claude \
  --member="serviceAccount:github-actions@jobbot-claude.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Storage Admin (для Container Registry)
gcloud projects add-iam-policy-binding jobbot-claude \
  --member="serviceAccount:github-actions@jobbot-claude.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Service Account User
gcloud projects add-iam-policy-binding jobbot-claude \
  --member="serviceAccount:github-actions@jobbot-claude.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Cloud Build Editor
gcloud projects add-iam-policy-binding jobbot-claude \
  --member="serviceAccount:github-actions@jobbot-claude.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"
```

---

## 5️⃣ Створити JSON ключ

```bash
gcloud iam service-accounts keys create ~/key.json \
  --iam-account=github-actions@jobbot-claude.iam.gserviceaccount.com
```

---

## 6️⃣ Показати JSON ключ

```bash
cat ~/key.json
```

**ВАЖЛИВО:** Скопіюй ВЕСЬ JSON (від `{` до `}`), включаючи всі лапки та переноси рядків!

---

## 7️⃣ (Опціонально) Завантажити ключ локально

Якщо Cloud Shell закриється, можеш завантажити файл:

```bash
cloudshell download ~/key.json
```

---

## ✅ Готово!

Тепер у тебе є:
- ✅ Project ID: `jobbot-claude`
- ✅ Service Account JSON ключ

**Наступний крок:** Додай GitHub Secrets

