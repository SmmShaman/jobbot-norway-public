# 🖥️ Установка Worker на ЛОКАЛЬНОМУ ПК

**ВАЖЛИВО:** Ці команди треба виконати на **ТВОЄМУ ПК** (де працює Skyvern), НЕ в GitHub репозиторії!

---

## 📋 Метод 1: Автоматична установка (РЕКОМЕНДОВАНО)

### Крок 1: Відкрий термінал на своєму ПК

**Windows:** Git Bash / PowerShell / WSL
**Mac/Linux:** Terminal

### Крок 2: Перейди в директорію Worker

```bash
cd ~/jobbot-norway-public/worker
```

**Якщо репозиторій не склонований:**
```bash
git clone https://github.com/SmmShaman/jobbot-norway-public.git
cd jobbot-norway-public/worker
```

### Крок 3: Запусти скрипт установки

```bash
bash setup_worker.sh
```

Скрипт автоматично:
- ✅ Перевірить Python
- ✅ Встановить залежності
- ✅ Створить .env файл (попросить SUPABASE_SERVICE_KEY)
- ✅ Перевірить чи працює Skyvern
- ✅ Протестує Worker

### Крок 4: Отримай SUPABASE_SERVICE_KEY

Коли скрипт попросить, відкрий в браузері:

```
https://app.supabase.com/project/ptrmidlhfdbybxmyovtm/settings/api
```

Скопіюй **service_role** key (довгий токен, починається з `eyJ...`) і вставь в термінал.

### Крок 5: Запусти Worker

```bash
python worker.py
```

Або Python 3:
```bash
python3 worker.py
```

Ти побачиш:
```
🤖 JobBot Worker Started
🆔 Worker ID: worker-abc12345
⏱️ Poll Interval: 10s
===================================

💤 No pending tasks. Waiting 10s...
```

**✅ Працює!** Залиш Worker працювати.

---

## 📋 Метод 2: Ручна установка

### 1. Встанови залежності:

```bash
cd ~/jobbot-norway-public/worker
pip install -r requirements.txt
```

### 2. Створи .env файл:

```bash
cp .env.example .env
nano .env  # або vim/code .env
```

Відредагуй:
```env
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=твій_service_role_key_тут
SKYVERN_API_URL=http://localhost:8000
```

### 3. Перевір Skyvern:

```bash
curl http://localhost:8000/api/v1/health
```

### 4. Запусти Worker:

```bash
python worker.py
```

---

## 🔧 Команди для локального Claude Code Terminal

Якщо використовуєш **Claude Code в терміналі на своєму ПК**, скопіюй ці команди:

```bash
# ВАЖЛИВО: Виконуй з правами
claude --dangerously-skip-permissions

# Перейди в worker директорію
cd ~/jobbot-norway-public/worker

# Запусти setup
bash setup_worker.sh

# Після setup - запусти Worker
python3 worker.py
```

---

## ✅ Перевірка роботи

### 1. Worker запущений та чекає завдань:
```
💤 No pending tasks. Waiting 10s...
```

### 2. Відкрий Dashboard:
```
https://jobbotnetlify.netlify.app/dashboard
```

### 3. Натисни "Scan Jobs Now"

### 4. Worker почне обробку:
```
📋 Processing task: 5694561a...
🌐 Source: FINN
🔗 URL: https://www.finn.no/...
🤖 Calling Skyvern API...
✅ Skyvern task created
```

### 5. Переглянь логи:
```bash
tail -f worker.log
```

---

## 🛑 Зупинити Worker

В терміналі де працює Worker:
```
Ctrl+C
```

Або знайти процес і вбити:
```bash
ps aux | grep worker.py
kill <PID>
```

---

## 🐛 Troubleshooting

### Python не знайдено:
```bash
# Mac/Linux
brew install python3
# або
sudo apt install python3 python3-pip

# Windows
# Завантаж з https://python.org
```

### pip не знайдено:
```bash
python3 -m ensurepip --upgrade
```

### Skyvern не працює:
```bash
docker ps | grep skyvern
# Якщо пусто:
docker-compose up -d skyvern
```

### Permission denied:
```bash
chmod +x setup_worker.sh
```

---

## 🚀 Запуск як фоновий сервіс

### Linux (systemd):

Створи `/etc/systemd/system/jobbot-worker.service`:
```ini
[Unit]
Description=JobBot Worker
After=network.target

[Service]
Type=simple
User=твій_username
WorkingDirectory=/home/твій_username/jobbot-norway-public/worker
ExecStart=/usr/bin/python3 worker.py
Restart=always

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

### Mac (launchd):

Створи `~/Library/LaunchAgents/com.jobbot.worker.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jobbot.worker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/твій_username/jobbot-norway-public/worker/worker.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Запусти:
```bash
launchctl load ~/Library/LaunchAgents/com.jobbot.worker.plist
```

### Windows (Task Scheduler):

1. Відкрий Task Scheduler
2. Create Basic Task → "JobBot Worker"
3. Trigger: At startup
4. Action: Start a program
   - Program: `python.exe`
   - Arguments: `C:\path\to\jobbot-norway-public\worker\worker.py`
   - Start in: `C:\path\to\jobbot-norway-public\worker`

---

**Готово! Worker встановлений на локальному ПК!** 🎉
