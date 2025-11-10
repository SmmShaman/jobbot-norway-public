# 🚀 SQL Functions Deployment Instructions

## ✅ Що було зроблено

Додано критичні SQL функції та deployment інфраструктуру:

### 📁 Нові файли:

**SQL Functions:**
- `database/function_1_extract_links.sql` - Витягує посилання на вакансії з HTML
- `database/function_2_create_jobs.sql` - Створює jobs в базі даних
- `database/function_3_get_pending.sql` - Отримує список jobs для Skyvern
- `database/COPY_THIS_SQL.sql` - Об'єднаний файл для ручного deployment

**Deployment Scripts:**
- `database/deploy_on_vm.sh` - Скрипт для deployment на VM
- `.github/workflows/deploy-sql-functions.yml` - GitHub Actions workflow
- `.github/workflows/deploy-vm.yml` - Workflow для оновлення worker на VM
- `.github/workflows/debug-worker.yml` - Debug workflow для VM

---

## 🎯 Наступні кроки: Deploy SQL функції

### ⚡ Метод 1: Швидкий (30 секунд) - РЕКОМЕНДОВАНО

**Використовуй Supabase Dashboard:**

1. Відкрий: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new

2. Відкрий файл: `database/COPY_THIS_SQL.sql`

3. Скопіюй **ВСЕ** (Ctrl+A, Ctrl+C)

4. Вставай в SQL Editor (Ctrl+V)

5. Натисни **"Run"** ▶️

6. Має показати: ✅ `Success. No rows returned`

7. Перевір що функції створено:
   ```sql
   SELECT routine_name FROM information_schema.routines
   WHERE routine_schema = 'public' AND routine_name LIKE '%finn%';
   ```

   Має показати **3 функції**:
   - `extract_finn_job_links`
   - `create_jobs_from_finn_links`
   - `get_pending_skyvern_jobs`

---

### 🖥️ Метод 2: Через VM (якщо маєш SSH доступ)

**На Google Cloud VM:**

```bash
# 1. SSH на VM
gcloud compute ssh stuard@<vm-name> --zone=<zone>

# 2. Перейди в repo
cd /home/stuard/jobbot-norway-public

# 3. Fetch і checkout цю гілку
git fetch origin
git checkout claude/autonomous-system-setup-011CUzCXEvwUCyGC22HPW9T2
git pull

# 4. Запусти deployment скрипт
bash database/deploy_on_vm.sh

# 5. Restart worker
sudo systemctl restart worker_v2

# 6. Подивись логи
sudo journalctl -u worker_v2 -f
```

---

### 🤖 Метод 3: GitHub Actions (НЕ РЕКОМЕНДОВАНО - workflow може не відображатися)

**⚠️ УВАГА:** Workflows не відображаються в GitHub UI якщо вони не в main branch.

Якщо хочеш спробувати:

1. Merge цю гілку в main (або створи PR)
2. Йди в Actions → Deploy SQL Functions
3. Run workflow
4. Введи database password: `QWEpoi123987@`

---

## ✅ Перевірка що все працює

### 1. Перевір функції в базі

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

Має показати 3 рядки.

---

### 2. Тестовий виклик функції

```sql
-- Тест витягування посилань
SELECT * FROM extract_finn_job_links('<a href="/job/ad/123456789">Test</a>');

-- Має повернути:
-- url                                  | finnkode   | title
-- https://www.finn.no/job/ad/123456789 | 123456789  | Job 123456789
```

---

### 3. Перевір worker логи

**На VM:**

```bash
sudo journalctl -u worker_v2 -f
```

**Що має бути в логах:**

✅ ПРАВИЛЬНО (функції працюють):
```
📊 Created 50 jobs from HTML
✅ Jobs saved successfully!
✅ Scan task completed
```

❌ НЕПРАВИЛЬНО (функції не існують):
```
⚠️ No job links extracted
❌ Empty result from create_jobs_from_finn_links
```

---

### 4. Перевір jobs в базі

```sql
SELECT COUNT(*) as total_jobs FROM jobs;
SELECT COUNT(*) as pending_jobs FROM jobs WHERE skyvern_status = 'PENDING';
```

Якщо функції працюють - ти побачиш jobs!

---

## 🔄 Після deployment

### Restart Worker

**На VM:**
```bash
sudo systemctl restart worker_v2
sudo journalctl -u worker_v2 -f
```

**Що має статися:**

1. Worker бере `scan_task` з статусом `PENDING`
2. Завантажує HTML з FINN.no
3. Викликає `create_jobs_from_finn_links()`
4. SQL функція парсить HTML і створює jobs
5. Worker отримує список створених jobs
6. Worker оновлює scan_task → `COMPLETED`
7. Jobs з'являються в dashboard!

---

## 🎉 Система стає автономною!

Після deployment функцій:

✅ Worker працює **24/7** без втручання
✅ Dashboard показує jobs **realtime**
✅ Skyvern може заповнювати форми автоматично
✅ Весь процес **повністю автоматизований**

---

## 🆘 Troubleshooting

### Проблема: "function does not exist"

**Рішення:** Функції не задеплоєно, використовуй Метод 1 (швидкий)

---

### Проблема: Worker показує "No job links extracted"

**Причини:**
1. Функції не існують в базі → Deploy функції
2. HTML порожній або неправильний → Перевір що FINN.no доступний
3. Regex не знаходить посилань → Перевір формат HTML

**Перевірка:**
```sql
-- Тест на справжньому HTML
SELECT * FROM create_jobs_from_finn_links(
  'your-user-id-uuid',
  'your-scan-task-id-uuid',
  '<html>тут весь HTML з FINN.no</html>'
);
```

---

### Проблема: GitHub Actions workflow не видно

**Причина:** Workflows не відображаються якщо не в main branch

**Рішення:**
- Використовуй Метод 1 (Dashboard) або Метод 2 (VM)
- АБО merge гілку в main і тоді workflow з'явиться

---

## 📊 Моніторинг системи

### Worker Status
```bash
sudo systemctl status worker_v2
```

### Worker Logs (realtime)
```bash
sudo journalctl -u worker_v2 -f
```

### Database Stats
```sql
SELECT
  COUNT(*) FILTER (WHERE status = 'NEW') as new_jobs,
  COUNT(*) FILTER (WHERE skyvern_status = 'PENDING') as pending_skyvern,
  COUNT(*) FILTER (WHERE status = 'APPLIED') as applied_jobs,
  COUNT(*) as total_jobs
FROM jobs;
```

---

## 🎯 Наступні покращення

Після того як функції запрацюють, можна додати:

1. **AI Analyzer** - Аналізує релевантність вакансій
2. **Auto-apply** - Skyvern автоматично подає заявки
3. **Notification System** - Email/Telegram повідомлення
4. **Analytics Dashboard** - Статистика та графіки
5. **Resume Customization** - Автоматична адаптація резюме

---

## 💡 Важливо!

⚠️ **БЕЗ ЦИХ ФУНКЦІЙ WORKER НЕ МОЖЕ СТВОРЮВАТИ JOBS!**

Функції є **критичними** для автономності системи.

Весь ланцюжок:
```
User → Dashboard → scan_task created
→ Worker бачить task
→ Worker завантажує HTML
→ Worker → SQL function → jobs created ✅
→ Dashboard показує jobs
→ Skyvern заповнює форми
```

Без функцій - ланцюжок рветься на кроці SQL function.

---

**Успіхів! 🚀**
