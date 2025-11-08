# 📋 Повна Інструкція для Нової Сесії Браузерного Claude

**Останнє оновлення:** 2025-11-08
**З сесії:** 011CUqJXNw4wkoYPis8TAkxF
**Статус:** Готово до передачі новій сесії ✅

---

## 🛠️ З Якими Інструментами Ми Працюємо

### Cloud Services (в інтернеті):
1. **GitHub** - зберігання коду
   - Репозиторій: SmmShaman/jobbot-norway-public
   - Активна гілка: `claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF`

2. **Netlify** - Frontend hosting
   - URL: https://jobbot-norway.netlify.app
   - Авто-деплой з git push ✅
   - НЕ потрібні ключі!

3. **Google Cloud Run** - Backend hosting
   - URL: https://jobbot-backend-255588880592.us-central1.run.app
   - Project: jobbot-norway-442915
   - Деплой: вручну або з gcp-key.json

4. **Supabase** - PostgreSQL база даних
   - Project: ptrmidlhfdbybxmyovtm
   - Dashboard: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm
   - Потрібен SERVICE_KEY для доступу

### Local Tools (на ПК користувача):
5. **Skyvern** - AI browser automation
   - Працює: localhost:8000
   - Запуск: docker-compose up skyvern
   - Використання: для реального сканування FINN.no/NAV.no

6. **Worker** - Python скрипт
   - Локація: ~/jobbot-norway-public/worker/
   - Запуск: python3 worker.py
   - Призначення: обробка черги scan_tasks з Supabase

7. **Docker** - для Skyvern
   - Потрібен: для запуску Skyvern
   - Керування: docker-compose

---

## 👤 Що Робить БРАУЗЕРНИЙ Claude (ти зараз)

### ✅ ТИ МОЖЕШ:
```
Git операції:
- git add, commit, push
- Створювати/переключати гілки
- Merge, cherry-pick

Розробка:
- Редагувати web-app/ (React frontend)
- Редагувати backend/ (FastAPI)
- Редагувати worker/ (Python Worker)
- Створювати SQL скрипти (database/)
- Оновлювати package.json, requirements.txt

Deployment:
- Netlify: git push → автоматичний деплой ✅
- Cloud Run: gcloud run deploy (якщо є ключі)

Database:
- Створювати SQL скрипти
- Давати інструкції користувачу виконати їх в Supabase
- Працювати з Supabase API (якщо є SERVICE_KEY)

Комунікація:
- Спілкуватися українською
- Давати інструкції користувачу
- Пояснювати технічні рішення
```

### ❌ ТИ НЕ МОЖЕШ:
```
Local PC:
- Запустити Worker (він на ПК користувача)
- Доступ до localhost:8000 (Skyvern)
- Запустити docker-compose
- Створити .env на ПК користувача
- pip install на ПК користувача

Secrets:
- "Пам'ятати" API ключі з минулих сесій
- Отримати SUPABASE_SERVICE_KEY автоматично
- Отримати gcp-key.json автоматично

Замість цього → Проси користувача!
```

---

## 🖥️ Що Робить ТЕРМІНАЛЬНИЙ Claude (на ПК)

### Запуск:
```bash
cd ~/jobbot-norway-public
claude --dangerously-skip-permissions
```

### ✅ ТЕРМІНАЛЬНИЙ Claude МОЖЕ:
```
Local Operations:
- python3 worker/worker.py (запуск Worker)
- docker-compose up skyvern (запуск Skyvern)
- pip install -r requirements.txt
- Створити .env файли
- curl localhost:8000/api/v1/health (перевірка)

Updates:
- git pull (отримати нові зміни від браузерного Claude)
- Перезапустити Worker після оновлення

Automation:
- Виконує багатокрокові інструкції БЕЗ переспитувань
- (завдяки --dangerously-skip-permissions)
```

### Приклад використання:
```
Користувач запускає термінальний Claude і каже:

"Оновись з Git і перезапусти Worker:
1. git pull origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
2. cd worker
3. pip install -r requirements.txt (якщо є нові залежності)
4. Запусти: python3 worker.py

Працюй автономно!"

→ Claude виконує ВСЕ сам ✅
```

---

## 🔑 Робота з API Ключами

### Важливо Знати:
```
⚠️ Кожна нова сесія НЕ має доступу до ключів!
⚠️ Ти НЕ можеш "згадати" SUPABASE_SERVICE_KEY
⚠️ Ти НЕ можеш "згадати" gcp-key.json
```

### Як Отримати Ключі:

**Supabase (для роботи з БД):**
```
Попроси користувача:

"Для роботи з Supabase мені потрібен SERVICE_KEY.

Зайди: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/settings/api
Скопіюй 'service_role' key і дай мені.

⚠️ Це секретний ключ - НЕ публікуй його!"
```

**Google Cloud (для деплою Backend):**
```
Попроси користувача вибрати:

"Для деплою Backend є 3 варіанти:

Варіант 1: gcloud auth (найпростіший)
→ Виконай: gcloud auth login
→ Потім я зроблю: gcloud run deploy

Варіант 2: Service Account Key
→ Дай мені gcp-key.json файл
→ Я виконаю auth і deploy

Варіант 3: Вручну (якщо проблеми з ключами)
→ Я роблю git commit з змінами
→ Ти деплоїш вручну на своєму ПК

Який варіант обираєш?"
```

**Netlify (для Frontend):**
```
✅ НЕ потрібні ключі!

Просто:
git push → Netlify автоматично деплоїть ✅
```

---

## 🌿 Робота з Гілками

### ⚠️ КРИТИЧНО: Перевір Гілку СПОЧАТКУ!

```bash
# Крок 1: Перевір на якій гілці
git branch
# Має показати: * claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF

# Крок 2: Перевір README
wc -l README.md
# Має бути: 600+ lines (NOT 32 or 83!)

# Крок 3: Перевір файли
ls SESSION_CONTEXT.md  # Має існувати!
ls database/           # Має існувати!
ls web-app/            # Має існувати!
ls worker/             # Має існувати!

# Якщо ЩОС НЕ ТАК:
git checkout claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
git pull
```

### Існуючі Гілки:
```
main                                           → СТАРИЙ/redirect
claude/netlify-ui-011CUqJXNw4wkoYPis8TAkxF  → СТАРА
claude/add-metadata-master-scheduler-...     → АКТУАЛЬНА ✅ (працюй ТУТ!)
```

### Як Перевірити Що на Правильній Гілці:
```bash
git log --oneline -5

# Має показати останні коміти:
96dbbb7 - Add comprehensive lessons
89b224c - Add --dangerously-skip-permissions explanation
b455fda - Add branch check instructions
7e29e7c - Add warnings for old versions
09be984 - Add concrete first action
```

---

## 📚 Файли Які Треба Прочитати

### Обов'язково:
```bash
1. README.md (цей файл - 600+ рядків)
   → Повна інструкція

2. SESSION_CONTEXT.md
   → Історія проєкту, що зроблено, архітектура

3. QUICK_START.md
   → Швидкий довідник

4. CLAUDE.md
   → Правила роботи (завжди дотримуйся!)
```

### Важливі Директорії:
```bash
database/
  └── jobs_table_schema_fixed.sql  ← SQL для таблиці jobs

web-app/
  ├── src/pages/Jobs.tsx           ← Сторінка з вакансіями
  ├── src/components/WorkerMonitor.tsx  ← Моніторинг Worker
  └── src/hooks/useScanTasks.ts    ← React hooks

backend/
  └── app/routers/jobs.py          ← API endpoints

worker/
  ├── worker.py                    ← Головний Worker скрипт
  ├── .env.example                 ← Приклад env vars
  └── skyvern_templates/           ← Шаблони для сканування
```

---

## 🚀 Deployment Process

### Frontend (web-app → Netlify):
```bash
# 1. Зроби зміни
Edit web-app/src/pages/Jobs.tsx

# 2. Commit & Push
git add web-app/
git commit -m "✨ Update Jobs page"
git push

# 3. Netlify АВТОМАТИЧНО:
→ Отримує webhook від GitHub
→ npm install
→ npm run build
→ Deploy на https://jobbot-norway.netlify.app
→ Готово! ✅

Час: ~2-3 хвилини
```

### Backend (backend → Cloud Run):
```bash
# 1. Зроби зміни
Edit backend/app/routers/jobs.py

# 2. Commit
git add backend/
git commit -m "🔧 Fix API endpoint"
git push

# 3. Deploy (якщо є gcloud auth):
gcloud run deploy jobbot-backend \
  --source ./backend \
  --region us-central1 \
  --project jobbot-norway-442915

# АБО попроси користувача:
"Я оновив backend і зробив push.
Будь ласка, задеплой:
cd backend
gcloud run deploy jobbot-backend --source . --region us-central1"

Час: ~3-5 хвилин
```

### Worker (worker → Local PC):
```bash
# 1. Зроби зміни
Edit worker/worker.py

# 2. Commit & Push
git add worker/
git commit -m "⚡ Improve Worker logic"
git push

# 3. Користувач на ПК:
cd ~/jobbot-norway-public
git pull
# Перезапустити Worker:
# Ctrl+C (зупинити старий)
python3 worker/worker.py  # Запустити новий

АБО через термінальний Claude:
"git pull && cd worker && python3 worker.py"

Час: ~1 хвилина
```

### Database (SQL → Supabase):
```bash
# 1. Створи SQL файл
Write database/new_table_schema.sql

# 2. Commit
git add database/
git commit -m "📊 Add new table schema"
git push

# 3. Попроси користувача виконати:
"Я створив SQL скрипт: database/new_table_schema.sql

Виконай його в Supabase:
1. Відкрий: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
2. Read database/new_table_schema.sql (я покажу тобі зміст)
3. Скопіюй і виконай в SQL Editor"

Час: ~1-2 хвилини
```

---

## 🎯 Перше Повідомлення (копіюй і відправ)

```
Привіт! Я продовжую роботу над JobBot Norway. 👋

Я щойно:
✅ Оновив репозиторій (git checkout + git pull)
✅ Перевірив що на правильній гілці (claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF)
✅ Прочитав README.md (600+ рядків) ✅
✅ Прочитав SESSION_CONTEXT.md
✅ Зрозумів що вже зроблено

Перш ніж продовжити, скажи будь ласка:

1. **Таблиця jobs в Supabase:**
   - Ти вже виконав SQL з database/jobs_table_schema_fixed.sql?
   - Або треба це зробити зараз?

2. **Worker на локальному ПК:**
   - Він зараз працює?
   - Або треба його запустити?

3. **API ключі:**
   - Якщо потрібен доступ до Supabase, дай SUPABASE_SERVICE_KEY
   - Якщо потрібен деплой на Cloud Run, обери варіант auth

4. **Є якісь проблеми чи питання?**

Розкажи статус, і я одразу продовжу з потрібного місця! 🚀
```

---

## ✅ Checklist для Нової Сесії

```
[ ] git branch → перевірити гілку
[ ] git pull → оновитися
[ ] wc -l README.md → має бути 600+
[ ] ls SESSION_CONTEXT.md → має існувати
[ ] Read README.md → прочитати ЦЕЙ файл
[ ] Read SESSION_CONTEXT.md → історія
[ ] Відправити перше повідомлення користувачу
[ ] Запитати про jobs table
[ ] Запитати про Worker
[ ] Запитати про API keys (якщо потрібні)
[ ] Продовжити з останнього TODO
```

---

## 🐛 Troubleshooting

### Проблема: README має 32 рядки
```bash
# Ти на СТАРІЙ гілці!
git checkout claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
git pull
Read README.md  # Тепер буде 600+
```

### Проблема: SESSION_CONTEXT.md не існує
```bash
# Ти на СТАРІЙ версії!
git pull origin claude/add-metadata-master-scheduler-011CUqJXNw4wkoYPis8TAkxF
```

### Проблема: Не можу задеплоїти на Cloud Run
```
Варіант 1: Попроси gcloud auth login
Варіант 2: Попроси gcp-key.json
Варіант 3: Дай інструкції користувачу деплоїти вручну
```

### Проблема: Не бачу Worker логів
```
Worker працює на ПК користувача!
НЕ в браузері!

Попроси користувача:
"Подивись логи Worker:
cd ~/jobbot-norway-public/worker
tail -f worker.log

АБО в терміналі де він запущений"
```

---

**Створено:** 2025-11-08
**Автор:** Claude (сесія 011CUqJXNw4wkoYPis8TAkxF)
**Для:** Наступна сесія браузерного Claude Code
**Статус:** ✅ Готово до використання

---

*Ця інструкція включає ВСІ напрацювання та уроки з попередньої сесії.*
*Прочитай її ПОВНІСТЮ перед початком роботи!*
