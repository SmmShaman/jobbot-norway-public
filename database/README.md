# 🗄️ Database - SQL Functions & Deployment

## 📁 Файли в цій папці

### ⚡ Quick Deploy (РЕКОМЕНДОВАНО)

**`COPY_THIS_SQL.sql`** - Об'єднаний файл з усіма функціями
- Відкрий: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
- Скопіюй весь вміст цього файлу
- Вставай в SQL Editor
- Натисни "Run"
- ✅ Готово!

---

### 📜 Окремі SQL функції

**`function_1_extract_links.sql`**
```sql
extract_finn_job_links(html_content TEXT)
```
Витягує посилання на вакансії з HTML сторінки FINN.no

**Що робить:**
- Парсить HTML з regexp
- Знаходить всі `/job/ad/[finnkode]` посилання
- Підтримує 3 формати URL (absolute, relative, old format)
- Повертає: `url`, `finnkode`, `title`

**Приклад:**
```sql
SELECT * FROM extract_finn_job_links('<a href="/job/ad/123">Job</a>');
-- Результат:
-- url: https://www.finn.no/job/ad/123
-- finnkode: 123
-- title: Job 123
```

---

**`function_2_create_jobs.sql`**
```sql
create_jobs_from_finn_links(
  p_user_id UUID,
  p_scan_task_id UUID,
  p_html_content TEXT
)
```
Створює jobs в таблиці jobs з HTML content

**Що робить:**
- Викликає `extract_finn_job_links()` для парсингу
- Для кожного посилання створює job в базі
- ON CONFLICT (user_id, url) DO UPDATE - не створює дублікатів
- Встановлює `skyvern_status = 'PENDING'`
- Повертає список створених job_id

**Приклад:**
```sql
SELECT * FROM create_jobs_from_finn_links(
  'your-user-uuid',
  'scan-task-uuid',
  '<html>...</html>'
);
-- Результат: список job_id, url, finnkode
```

---

**`function_3_get_pending.sql`**
```sql
get_pending_skyvern_jobs(
  p_user_id UUID,
  p_limit INTEGER DEFAULT 10
)
```
Отримує список jobs готових для Skyvern обробки

**Що робить:**
- Фільтрує jobs з `skyvern_status = 'PENDING'`
- Тільки для вказаного user_id
- Сортує за created_at DESC (найновіші першими)
- Повертає до N jobs (default 10)

**Приклад:**
```sql
SELECT * FROM get_pending_skyvern_jobs('your-user-uuid', 5);
-- Результат: 5 найновіших jobs для обробки
```

---

### 🛠️ Deployment Scripts

**`deploy_on_vm.sh`** ⭐ РЕКОМЕНДОВАНО
```bash
bash database/deploy_on_vm.sh
```

Запускай на Google Cloud VM (де DNS працює правильно)

**Що робить:**
1. Підключається до Supabase PostgreSQL
2. Виконує function_1_extract_links.sql
3. Виконує function_2_create_jobs.sql
4. Виконує function_3_get_pending.sql
5. Перевіряє що функції створено
6. Виводить інструкції для restart worker

**Вимоги:**
- psql встановлений
- DNS резолвить db.ptrmidlhfdbybxmyovtm.supabase.co
- Database password: `QWEpoi123987@`

---

### 📋 Table Schemas

**`jobs_table_schema_fixed.sql`**

Створює таблицю `jobs` з повною структурою:

**Основні поля:**
- `id`, `user_id`, `scan_task_id` - Ідентифікатори
- `title`, `company`, `location`, `url` - Інформація про вакансію
- `finnkode` - Унікальний код FINN.no
- `skyvern_status` - Статус обробки Skyvern
- `status` - Статус вакансії (NEW, APPLIED, etc.)

**Features:**
- ✅ Row Level Security (RLS)
- ✅ Unique constraint (user_id, url) - захист від дублікатів
- ✅ Indexes для швидких запитів
- ✅ Auto-update `updated_at` trigger
- ✅ Safe to run multiple times

**Використання:**
```bash
PGPASSWORD="..." psql "postgresql://..." -f jobs_table_schema_fixed.sql
```

---

**`jobs_table_schema.sql`**

Старіша версія schema (без деяких оптимізацій).
Рекомендовано використовувати `jobs_table_schema_fixed.sql`.

---

## 🚀 Як deploy-ити функції

### Варіант 1: Supabase Dashboard (30 секунд)

```
1. Відкрий: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
2. Відкрий файл: database/COPY_THIS_SQL.sql
3. Ctrl+A, Ctrl+C (скопіюй ВСЕ)
4. Ctrl+V в SQL Editor
5. Натисни "Run" ▶️
6. ✅ Success!
```

---

### Варіант 2: VM Script

**SSH на VM:**
```bash
gcloud compute ssh stuard@<vm-name>
```

**Deploy:**
```bash
cd /home/stuard/jobbot-norway-public
git pull
bash database/deploy_on_vm.sh
```

**Restart worker:**
```bash
sudo systemctl restart worker_v2
sudo journalctl -u worker_v2 -f
```

---

### Варіант 3: GitHub Actions

⚠️ **Увага:** Workflow може не відображатися якщо не в main branch

```
1. GitHub → Actions → Deploy SQL Functions
2. Run workflow
3. Input: db_password = "QWEpoi123987@"
4. ✅ Дочекайся завершення
```

---

## ✅ Перевірка deployment

### 1. Перевір що функції існують

```sql
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name IN (
    'extract_finn_job_links',
    'create_jobs_from_finn_links',
    'get_pending_skyvern_jobs'
  )
ORDER BY routine_name;
```

Має показати **3 функції**.

---

### 2. Тестовий виклик

```sql
-- Тест парсингу
SELECT * FROM extract_finn_job_links(
  '<a href="/job/ad/123456789">Test Job</a>'
);

-- Має повернути:
-- url: https://www.finn.no/job/ad/123456789
-- finnkode: 123456789
-- title: Job 123456789
```

---

### 3. Worker логи

**На VM:**
```bash
sudo journalctl -u worker_v2 -f
```

**✅ Правильно (функції працюють):**
```
📊 Created 50 jobs from HTML
✅ Jobs saved successfully!
```

**❌ Неправильно (функції не існують):**
```
⚠️ No job links extracted
❌ RPC call failed
```

---

## 🔗 Зв'язок з Worker

### Worker викликає функції так:

```python
# worker_v2.py
result = supabase.rpc(
    "create_jobs_from_finn_links",
    {
        "p_user_id": user_id,
        "p_scan_task_id": scan_task_id,
        "p_html_content": html_content  # 500KB HTML
    }
).execute()

print(f"Created {len(result.data)} jobs")
```

**Що відбувається в базі:**

1. `create_jobs_from_finn_links()` приймає HTML
2. Викликає `extract_finn_job_links()` для парсингу
3. Для кожного посилання:
   - INSERT INTO jobs (або UPDATE якщо існує)
   - Встановлює skyvern_status = 'PENDING'
4. Повертає список створених job_id

**Результат:**
- Worker отримує масив job records
- Dashboard показує нові jobs (realtime!)
- Skyvern може починати заповнювати форми

---

## 🆘 Troubleshooting

### ❌ Error: "function does not exist"

**Причина:** Функції не задеплоєно в базу

**Рішення:**
```bash
# Використовуй COPY_THIS_SQL.sql в Dashboard
# АБО
bash database/deploy_on_vm.sh
```

---

### ❌ Error: "relation 'jobs' does not exist"

**Причина:** Таблиця jobs не створена

**Рішення:**
```bash
PGPASSWORD="..." psql "postgresql://..." -f database/jobs_table_schema_fixed.sql
```

---

### ❌ Worker показує "No job links extracted"

**Можливі причини:**

1. **Функції не існують** → Deploy функції
2. **HTML порожній** → Перевір що FINN.no доступний
3. **Regex не знаходить посилань** → Перевір формат HTML

**Debug:**
```sql
-- Тест на реальному HTML
SELECT COUNT(*) FROM extract_finn_job_links('
  <a href="/job/ad/123">Job 1</a>
  <a href="/job/ad/456">Job 2</a>
');
-- Має повернути 2
```

---

### ⚠️ DNS не резолвить db.*.supabase.co

**Причина:** Claude Code Environment має проблеми з Supabase DNS

**Рішення:**
- Використовуй VM (де DNS працює)
- АБО Supabase Dashboard (web interface)

---

## 📚 Додаткова інформація

**Supabase Project:**
- Project ID: `ptrmidlhfdbybxmyovtm`
- Dashboard: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm
- Database: `db.ptrmidlhfdbybxmyovtm.supabase.co:5432`

**Credentials:**
- DB User: `postgres`
- DB Password: `QWEpoi123987@`
- DB Name: `postgres`

**Connection String:**
```
postgresql://postgres:QWEpoi123987@@db.ptrmidlhfdbybxmyovtm.supabase.co:5432/postgres
```

⚠️ **Service Role Key** (для Python worker):
```python
SUPABASE_SERVICE_KEY=<в worker/.env на VM>
```

---

**Успіхів з deployment! 🚀**
