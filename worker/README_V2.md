# Worker v2 - Link Extraction Architecture

## Швидкий старт

### 1. Встановіть SQL функції в Supabase

Відкрийте Supabase SQL Editor:
```
https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
```

Виконайте файл:
```sql
-- Скопіюйте і виконайте весь код з файлу:
../database/finn_link_extractor_function.sql
```

### 2. Запустіть Worker v2

```bash
cd ~/jobbot-norway-public/worker
python3 worker_v2.py
```

## Що нового?

### Старий підхід (worker.py):
```
FINN.no search URL → Skyvern (повільно) → List of jobs → For each job → Skyvern (знову)
```
⏱️ Час до перших результатів: **30+ секунд**

### Новий підхід (worker_v2.py):
```
FINN.no search URL → Fetch HTML (швидко) → Extract links (regex) → Create jobs in DB
                                                                         ↓
                                              For each job URL → Skyvern (детальна інформація)
```
⏱️ Час до перших результатів: **< 5 секунд**

## Переваги

### 🚀 Швидкість
- Витягування лінків через regex замість Skyvern
- Результати з'являються одразу після скачування HTML
- ~100x швидше для фази екстракції лінків

### 👁️ Видимість
- Користувач бачить всі знайдені вакансії одразу
- Можна відслідковувати статус обробки кожної вакансії
- Поле `skyvern_status` показує прогрес

### 🔧 Надійність
- Якщо одна вакансія не обробилася - інші не страждають
- Легко перезапустити обробку окремої вакансії
- Автоматичне дедуплікування (як і раніше)

### ⚡ Масштабованість
- Готово до паралельної обробки (можна запустити 5-10 Skyvern задач одночасно)
- Можна додати пріоритетну чергу
- Можна розподілити обробку між кількома воркерами

## Як це працює

### Крок 1: Витягування лінків

```python
# Worker завантажує HTML зі сторінки пошуку FINN.no
html_content = requests.get(finn_search_url).text

# Викликає Supabase функцію для екстракції
result = supabase.rpc('create_jobs_from_finn_links', {
    'p_user_id': user_id,
    'p_scan_task_id': scan_task_id,
    'p_html_content': html_content
})

# Функція:
# 1. Витягує всі URL з pattern: finnkode=\d+
# 2. Створює записи в таблиці jobs
# 3. Встановлює skyvern_status='PENDING'
# 4. Повертає список створених job_id
```

### Крок 2: Обробка кожної вакансії

```python
# Для кожної створеної вакансії
for job in created_jobs:
    # Викликаємо Skyvern для витягування деталей
    skyvern_result = call_skyvern('DETAIL', job['job_url'])

    # Оновлюємо запис у БД
    update_job_with_details(job['job_id'], skyvern_result)

    # Встановлюємо skyvern_status='COMPLETED'
```

## SQL Функції

### extract_finn_job_links(html_content)

Витягує лінки з HTML використовуючи regex:

```sql
SELECT * FROM extract_finn_job_links('<html>
  <a href="https://www.finn.no/job/fulltime/ad.html?finnkode=123456">Job 1</a>
  <a href="/job/fulltime/ad.html?finnkode=789012">Job 2</a>
</html>');

-- Результат:
-- url                                              | finnkode | title
-- ------------------------------------------------|----------|--------
-- https://www.finn.no/...?finnkode=123456         | 123456   | Job 123456
-- https://www.finn.no/job/fulltime/...?finnkode=789012 | 789012   | Job 789012
```

### create_jobs_from_finn_links(user_id, scan_task_id, html_content)

Створює записи вакансій в БД:

```sql
SELECT * FROM create_jobs_from_finn_links(
    'user-uuid-here',
    'task-uuid-here',
    '<html>...</html>'
);

-- Результат:
-- job_id                               | job_url                    | finnkode
-- ------------------------------------|----------------------------|----------
-- job-uuid-1                          | https://www.finn.no/...    | 123456
-- job-uuid-2                          | https://www.finn.no/...    | 789012
```

### get_pending_skyvern_jobs(user_id, limit)

Отримує вакансії для обробки:

```sql
SELECT * FROM get_pending_skyvern_jobs('user-uuid-here', 10);

-- Повертає до 10 вакансій зі статусом skyvern_status='PENDING'
```

## Поле skyvern_status

Нове поле в таблиці `jobs`:

- **PENDING** - Очікує обробки Skyvern
- **PROCESSING** - Обробляється Skyvern (в майбутньому)
- **COMPLETED** - Успішно оброблено
- **FAILED** - Помилка при обробці

## Логування

Worker v2 логує кожен крок:

```
🚀 Worker v2 initialized: worker-v2-abc123
📡 Supabase: https://ptrmidlhfdbybxmyovtm.supabase.co
🤖 Skyvern: http://localhost:8000
✅ Loaded template: DETAIL

📋 Processing task: 12345678...
🌐 Source: FINN
🔗 URL: https://www.finn.no/job/search?...

🌐 Fetching HTML from: https://www.finn.no/job/search?...
✅ HTML fetched: 145232 characters

🔍 Extracting job links from HTML...
✅ Created/updated 15 job entries

🔍 Processing job 1/15: finnkode=123456
🤖 Calling Skyvern for: https://www.finn.no/job/fulltime/...
✅ Skyvern task created: task_abc123
⏳ Skyvern task processing: task_abc123
✅ Skyvern task completed: task_abc123
✅ Updated job 12345678... with Skyvern details
✅ Job 1/15 processed successfully

...

✅ Task completed: 15/15 jobs processed
```

## Тестування

### Локальне тестування

1. **Встановіть залежності:**
```bash
cd worker
pip install -r requirements.txt
```

2. **Налаштуйте .env:**
```bash
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=your_service_key_here
SKYVERN_API_URL=http://localhost:8000
```

3. **Запустіть Skyvern:**
```bash
cd ~/jobbot-norway-public
docker-compose up skyvern
```

4. **Запустіть Worker v2:**
```bash
cd ~/jobbot-norway-public/worker
python3 worker_v2.py
```

5. **Створіть тестову задачу через Dashboard:**
   - Відкрийте https://jobbot-norway.netlify.app
   - Settings → Додайте FINN.no URL
   - Dashboard → "Scan Jobs Now"

6. **Перевірте логи:**
```bash
tail -f worker.log
```

### SQL тестування

```sql
-- Тест витягування лінків
SELECT * FROM extract_finn_job_links('
    <a href="https://www.finn.no/job/fulltime/ad.html?finnkode=123456">Developer</a>
    <a href="/job/parttime/ad.html?finnkode=789012">Designer</a>
');

-- Тест створення вакансій
SELECT * FROM create_jobs_from_finn_links(
    'your-user-id',
    'your-task-id',
    '<html><a href="https://www.finn.no/job/fulltime/ad.html?finnkode=111111">Test Job</a></html>'
);

-- Перевірка створених вакансій
SELECT id, url, finnkode, skyvern_status FROM jobs WHERE finnkode='111111';

-- Отримання pending вакансій
SELECT * FROM get_pending_skyvern_jobs('your-user-id', 5);
```

## Сумісність

Worker v2 повністю сумісний з існуючою інфраструктурою:

✅ Використовує ту саму таблицю `jobs`
✅ Ті самі Skyvern шаблони
✅ Той самий Frontend (без змін)
✅ Можна переключитися назад на worker.py

## Порівняння v1 vs v2

| Аспект | Worker v1 | Worker v2 |
|--------|-----------|-----------|
| **Екстракція списку** | Skyvern (30+ сек) | Regex (< 1 сек) |
| **Час до перших результатів** | 30+ сек | < 5 сек |
| **Видимість прогресу** | Тільки загальна | По кожній вакансії |
| **Обробка помилок** | Всі або нічого | Індивідуально |
| **Паралелізація** | Складно | Легко |
| **Налагодження** | Складно | Легко (логи по вакансіях) |

## Майбутні покращення

### Паралельна обробка
```python
# Можна обробляти 5 вакансій одночасно
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_job, job) for job in pending_jobs]
```

### Пріоритетна черга
```python
# Спочатку обробляти вакансії з дедлайном
SELECT * FROM get_pending_skyvern_jobs(user_id, 10)
ORDER BY deadline ASC NULLS LAST;
```

### Retry логіка
```python
# Автоматично перезапускати failed jobs
UPDATE jobs SET skyvern_status='PENDING', retry_count=retry_count+1
WHERE skyvern_status='FAILED' AND retry_count < 3;
```

## Питання та відповіді

**Q: Чи можна використовувати worker.py та worker_v2.py одночасно?**
A: Технічно так, але не рекомендується. Краще використовувати один воркер.

**Q: Що робити, якщо SQL функції вже існують?**
A: Скрипт використовує `CREATE OR REPLACE`, тому просто виконайте його знову.

**Q: Чи можна обробляти NAV.no таким же способом?**
A: Так, логіку можна адаптувати для NAV.no, додавши відповідну regex функцію.

**Q: Чи зберігаються старі вакансії при переході на v2?**
A: Так, всі існуючі вакансії залишаються в базі.

**Q: Скільки вакансій може обробити Worker v2?**
A: Немає обмежень, але рекомендується обробляти по 10-20 одночасно для стабільності Skyvern.

## Підтримка

Логи:
```bash
# Реалтайм логи
tail -f worker.log

# Останні 50 рядків
tail -50 worker.log

# Фільтрувати помилки
grep "ERROR" worker.log
```

Перевірка статусу:
```sql
-- Скільки вакансій в кожному статусі
SELECT skyvern_status, COUNT(*)
FROM jobs
WHERE source='FINN'
GROUP BY skyvern_status;

-- Failed вакансії
SELECT id, url, finnkode, error_message
FROM jobs
WHERE skyvern_status='FAILED';
```

## Ліцензія

Частина JobBot Norway project.
