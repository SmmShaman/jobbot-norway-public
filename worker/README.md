# JobBot Worker - Local Scan Task Processor

Worker програма яка працює на твоєму ПК і обробляє завдання сканування вакансій через Skyvern.

## 🎯 Що робить Worker?

1. **Підключається до Supabase** (база даних в інтернеті)
2. **Перевіряє чергу завдань** (`scan_tasks` таблиця) кожні 10 секунд
3. **Викликає Skyvern** (localhost:8000) для сканування сайтів
4. **Зберігає результати** назад в Supabase (`jobs` таблиця)

## 📋 Передумови

1. **Skyvern працює** на localhost:8000
2. **Python 3.8+** встановлений
3. **Supabase service key** (з Dashboard)

## 🚀 Встановлення

### Крок 1: Встанови залежності

```bash
cd worker
pip install -r requirements.txt
```

### Крок 2: Створи .env файл

```bash
cp .env.example .env
```

Відкрий `.env` і додай свої ключі:

```env
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci...  # service_role key з Supabase
SKYVERN_API_URL=http://localhost:8000
```

**Де взяти SUPABASE_SERVICE_KEY?**
1. Відкрий: https://app.supabase.com/project/ptrmidlhfdbybxmyovtm/settings/api
2. Скопіюй `service_role` key (довгий токен)

### Крок 3: Переконайся що Skyvern працює

```bash
curl http://localhost:8000/api/v1/health
```

Якщо не працює:
```bash
cd /path/to/skyvern
docker-compose up -d
```

## ▶️ Запуск Worker

### Просто запустити:

```bash
python worker.py
```

### Запустити у фоні (Linux/Mac):

```bash
nohup python worker.py > worker_output.log 2>&1 &
```

### Запустити як systemd service (Linux):

Створи файл `/etc/systemd/system/jobbot-worker.service`:

```ini
[Unit]
Description=JobBot Worker - Scan Task Processor
After=network.target

[Service]
Type=simple
User=твій_юзер
WorkingDirectory=/home/твій_юзер/jobbot-norway-public/worker
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активуй:
```bash
sudo systemctl daemon-reload
sudo systemctl enable jobbot-worker
sudo systemctl start jobbot-worker
sudo systemctl status jobbot-worker
```

## 📊 Моніторинг

### Переглянути логи:

Worker записує в `worker.log`:

```bash
tail -f worker.log
```

### Перевірити що Worker працює:

```bash
ps aux | grep worker.py
```

## 🔧 Налаштування

### Змінити інтервал опитування:

У файлі `worker.py`, рядок біля кінця:

```python
worker.run(poll_interval=10)  # 10 секунд
```

Зміни на потрібний інтервал (у секундах).

### Кількість одночасних завдань:

У методі `get_pending_tasks()`:

```python
.limit(5)  # обробляти максимум 5 завдань за раз
```

## 🐛 Troubleshooting

### Worker не може підключитися до Supabase:

```
ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY
```

**Рішення:** Переконайся що `.env` файл існує і містить правильні ключі.

### Worker не може підключитися до Skyvern:

```
ERROR: Cannot connect to Skyvern at http://localhost:8000
```

**Рішення:**
```bash
# Переконайся що Skyvern працює
docker ps | grep skyvern

# Якщо не працює - запусти
docker-compose up -d skyvern
```

### No pending tasks:

```
No pending tasks. Waiting 10s...
```

**Це нормально!** Worker чекає на нові завдання. Створи завдання через Dashboard.

### Skyvern task timeout:

```
ERROR: Skyvern task timeout: task-abc123
```

**Рішення:** Збільш timeout у методі `_wait_for_skyvern_task()`:

```python
def _wait_for_skyvern_task(self, task_id: str, max_wait: int = 600):  # 10 хвилин
```

## 📝 Як це працює?

```
Dashboard → додає URL
             ↓
Backend → створює scan_task (status: PENDING)
             ↓
Supabase → зберігає задачу
             ↓
Worker → знаходить PENDING tasks
             ↓
Worker → викликає Skyvern (localhost:8000)
             ↓
Skyvern → сканує FINN.no/NAV.no
             ↓
Skyvern → повертає JSON з вакансіями
             ↓
Worker → зберігає в таблицю jobs
             ↓
Dashboard → показує нові вакансії ✅
```

## ✅ Перевірка роботи

1. **Запусти Worker:**
   ```bash
   python worker.py
   ```

2. **Відкрий Dashboard:**
   https://jobbotnetlify.netlify.app/dashboard

3. **Додай URL для сканування** (в Settings або через кнопку "Scan Jobs")

4. **Дивись логи Worker:**
   ```bash
   tail -f worker.log
   ```

5. **Переглянь результати** в Dashboard → Jobs

## 🛑 Зупинити Worker

### Якщо запущений у терміналі:

```
Ctrl+C
```

### Якщо запущений у фоні:

```bash
ps aux | grep worker.py
kill <PID>
```

### Якщо systemd service:

```bash
sudo systemctl stop jobbot-worker
```

---

**Готово!** Worker тепер обробляє завдання автоматично! 🎉
