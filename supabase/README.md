# Supabase Setup Instructions

## 🚀 Швидкий старт

### 1. Створення Supabase проекту

1. Перейди на [supabase.com](https://supabase.com)
2. Створи новий проект:
   - **Project Name**: JobBot Norway
   - **Database Password**: (збережи цей пароль!)
   - **Region**: Europe West (найближче до Норвегії)

3. Зачекай 2-3 хвилини поки проект створюється

### 2. Отримання credentials

Після створення проекту:

1. Перейди в **Project Settings** → **API**
2. Скопіюй:
   - ✅ **Project URL** (схоже на: `https://xxxxx.supabase.co`)
   - ✅ **anon public key** (для frontend)
   - ✅ **service_role key** (для backend - **НЕ ПУБЛІКУЙ ЦЕ!**)

### 3. Запуск SQL міграції

1. Перейди в **SQL Editor** в Supabase Dashboard
2. Створи New Query
3. Скопіюй весь вміст файлу `migrations/001_initial_schema.sql`
4. Вставь в SQL Editor
5. Натисни **RUN** ▶️
6. Перевір що всі таблиці створилися в **Table Editor**

### 4. Створення Storage Buckets

Перейди в **Storage** → Create buckets:

#### Bucket 1: `resumes`
- **Name**: `resumes`
- **Public**: ❌ **Приватний**
- **File size limit**: 10 MB
- **Allowed MIME types**: `application/pdf`

**Створи Policy для resumes:**
```sql
-- Users can upload their own resumes
CREATE POLICY "Users upload own resume"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'resumes' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can view their own resumes
CREATE POLICY "Users view own resume"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'resumes' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can update their own resumes
CREATE POLICY "Users update own resume"
ON storage.objects FOR UPDATE
TO authenticated
USING (
  bucket_id = 'resumes' AND
  auth.uid()::text = (storage.foldername(name))[1]
);
```

#### Bucket 2: `cover-letters`
- **Name**: `cover-letters`
- **Public**: ❌ **Приватний**
- **File size limit**: 5 MB
- **Allowed MIME types**: `application/pdf, text/plain`

**Policy для cover-letters:**
```sql
CREATE POLICY "Users manage own cover letters"
ON storage.objects FOR ALL
TO authenticated
USING (
  bucket_id = 'cover-letters' AND
  auth.uid()::text = (storage.foldername(name))[1]
)
WITH CHECK (
  bucket_id = 'cover-letters' AND
  auth.uid()::text = (storage.foldername(name))[1]
);
```

#### Bucket 3: `screenshots`
- **Name**: `screenshots`
- **Public**: ❌ **Приватний**
- **File size limit**: 5 MB
- **Allowed MIME types**: `image/png, image/jpeg`

**Policy для screenshots:**
```sql
CREATE POLICY "Users manage own screenshots"
ON storage.objects FOR ALL
TO authenticated
USING (
  bucket_id = 'screenshots' AND
  auth.uid()::text = (storage.foldername(name))[1]
)
WITH CHECK (
  bucket_id = 'screenshots' AND
  auth.uid()::text = (storage.foldername(name))[1]
);
```

### 5. Налаштування Authentication

1. Перейди в **Authentication** → **Providers**
2. Увімкни **Email** provider:
   - ✅ Enable Email provider
   - ✅ Confirm email (рекомендовано)
   - Email templates можна кастомізувати пізніше

3. (Опціонально) Увімкни **Google OAuth**:
   - Потрібен Google Client ID та Secret
   - Інструкції в Supabase Dashboard

### 6. Налаштування Email Templates (Опціонально)

В **Authentication** → **Email Templates** можна налаштувати:
- Confirmation email
- Reset password email
- Magic link email

Можна додати норвезькі переклади!

---

## 📋 Environment Variables

Після виконання всіх кроків, створи `.env` файли:

### Frontend (`web-app/.env`)
```env
VITE_SUPABASE_URL=твій_project_url
VITE_SUPABASE_ANON_KEY=твій_anon_key
VITE_API_URL=http://localhost:8000
```

### Backend (`backend/.env`)
```env
# Supabase
SUPABASE_URL=твій_project_url
SUPABASE_SERVICE_KEY=твій_service_role_key

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://elvarika.openai.azure.com
AZURE_OPENAI_KEY=твій_azure_key
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Skyvern
SKYVERN_API_URL=http://localhost:8000

# Security
ENCRYPTION_KEY=generate_random_32_char_key_here
JWT_SECRET=generate_random_secret_here

# Optional: Telegram
TELEGRAM_BOT_TOKEN=
```

---

## 🧪 Перевірка setup

### Перевірка таблиць:

```sql
-- Перелік всіх таблиць
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Має показати:
-- applications
-- cover_letters
-- jobs
-- monitoring_logs
-- profiles
-- user_settings
```

### Перевірка RLS Policies:

```sql
-- Перевірка policies на таблиці jobs
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE tablename = 'jobs';
```

### Тестовий користувач:

1. Перейди в **Authentication** → **Users**
2. Натисни **Add user** → **Create new user**
3. Email: `test@example.com`
4. Password: `TestPassword123!`
5. Натисни **Create user**

Після цього в **Table Editor** → **profiles** має з'явитись новий запис!

---

## 🔒 Безпека

### ⚠️ НІКОЛИ НЕ ПУБЛІКУЙ:
- ❌ `service_role` key - це ПОВНИЙ доступ до БД!
- ❌ Database password
- ❌ Azure OpenAI keys
- ❌ Encryption keys

### ✅ Можна публікувати:
- ✅ Project URL
- ✅ `anon` key (це для frontend, має обмеження через RLS)

---

## 📚 Корисні SQL запити

### Статистика по користувачу:
```sql
SELECT * FROM user_dashboard_stats WHERE username = 'твій_username';
```

### Останні вакансії:
```sql
SELECT title, company, relevance_score, status
FROM jobs
WHERE user_id = 'твій_user_id'
ORDER BY created_at DESC
LIMIT 10;
```

### Успішні заявки:
```sql
SELECT
  j.title,
  j.company,
  a.submitted_at,
  a.nav_reported
FROM applications a
JOIN jobs j ON a.job_id = j.id
WHERE a.user_id = 'твій_user_id' AND a.status = 'SUCCESS'
ORDER BY a.submitted_at DESC;
```

---

## 🛠️ Troubleshooting

### Помилка: "permission denied for table X"
➡️ Перевір що RLS policies створені правильно

### Помилка: "bucket not found"
➡️ Створи storage buckets через Dashboard → Storage

### Помилка: "JWT expired"
➡️ Оновіть auth token в frontend (автоматично через Supabase client)

---

## 📞 Контакти

При виникненні проблем:
- 📖 [Supabase Docs](https://supabase.com/docs)
- 💬 [Supabase Discord](https://discord.supabase.com)
- 🐛 GitHub Issues цього репозиторію

---

✅ Готово! Тепер можна переходити до налаштування frontend та backend.
