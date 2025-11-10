# 🚀 SQL Functions Deployment Guide

## Проблема
Worker не може знайти вакансії, бо SQL функції не створені в Supabase.

## Рішення: Створити 3 функції

---

## ✅ МЕТОД 1: Автоматичний (через workflow)

### Крок 1: Запусти debug workflow

Іди на GitHub:
```
https://github.com/SmmShaman/jobbot-norway-public/actions/workflows/debug-worker.yml
```

Натисни "Run workflow" і введи команду:
```bash
cd /home/stuard/jobbot-norway-public/database && cat function_1_extract_links.sql function_2_create_jobs.sql function_3_get_pending.sql
```

Це покаже всі 3 функції, які треба створити.

---

## ✅ МЕТОД 2: Ручний (через Supabase Dashboard)

### Крок 1: Відкрий Supabase SQL Editor

```
https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
```

### Крок 2: Створи функції ПО ЧЕРЗІ (ВАЖЛИВО!)

#### 2.1 Функція 1: Extract Links

Відкрий файл:
```
/home/stuard/jobbot-norway-public/database/function_1_extract_links.sql
```

📋 Скопіюй ВЕСЬ вміст → Вставай в SQL Editor → Натисни "Run"

✅ Має показати: `Success. No rows returned`
❌ Якщо помилка - скопіюй повідомлення і надішли мені

#### 2.2 Функція 2: Create Jobs

Відкрий файл:
```
/home/stuard/jobbot-norway-public/database/function_2_create_jobs.sql
```

📋 Скопіюй ВЕСЬ вміст → Вставай в SQL Editor → Натисни "Run"

✅ Має показати: `Success. No rows returned`
❌ Якщо помилка - скопіюй повідомлення і надішли мені

#### 2.3 Функція 3: Get Pending Jobs

Відкрий файл:
```
/home/stuard/jobbot-norway-public/database/function_3_get_pending.sql
```

📋 Скопіюй ВЕСЬ вміст → Вставай в SQL Editor → Натисни "Run"

✅ Має показати: `Success. No rows returned`
❌ Якщо помилка - скопіюй повідомлення і надішли мені

---

## ✅ Крок 3: Перевір що функції створено

Виконай в Supabase SQL Editor:

```sql
SELECT
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
    AND routine_name IN (
        'extract_finn_job_links',
        'create_jobs_from_finn_links',
        'get_pending_skyvern_jobs'
    )
ORDER BY routine_name;
```

✅ Має показати 3 рядки:
```
create_jobs_from_finn_links  | FUNCTION
extract_finn_job_links       | FUNCTION
get_pending_skyvern_jobs     | FUNCTION
```

---

## ✅ Крок 4: Тестуй worker

Після створення функцій, worker автоматично почне знаходити вакансії!

Перезапусти worker:
```bash
sudo systemctl restart worker_v2
```

Подивись логи:
```bash
sudo journalctl -u worker_v2 -f
```

✅ Тепер має з'явитись:
```
📊 Created X jobs from HTML
✅ Jobs saved successfully!
```

Замість:
```
⚠️ No job links extracted from HTML
```

---

## 🐛 Типові помилки

### Помилка: "function extract_finn_job_links does not exist"

**Причина:** Функція 1 не створена

**Рішення:** Виконай функцію 1 ще раз

### Помилка: "syntax error at or near..."

**Причина:** Скопіювалась не вся функція або є зайві символи

**Рішення:**
1. Переконайся що скопіював ВСЮ функцію (від `CREATE` до `plpgsql;`)
2. Видали все з SQL Editor
3. Вставай знову і запусти

### Помилка: "column company does not exist"

**Причина:** Таблиця `jobs` не має потрібних полів

**Рішення:** Виконай:
```bash
cd /home/stuard/jobbot-norway-public
cat database/jobs_table_schema.sql
```

І створи таблицю через Supabase SQL Editor

---

## 📊 Результат

Після створення функцій:

1. ✅ Worker знаходить вакансії з FINN.no
2. ✅ Вакансії зберігаються в БД
3. ✅ Dashboard показує знайдені вакансії
4. ✅ Система працює автоматично 24/7

---

## 🆘 Якщо нічого не працює

Надішли мені:

1. Скріншот помилки з Supabase SQL Editor
2. Вивід команди:
```bash
sudo journalctl -u worker_v2 -n 50 --no-pager
```
3. Результат SQL запиту з "Крок 3: Перевір що функції створено"

І я допоможу!
