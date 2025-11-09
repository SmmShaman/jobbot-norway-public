# 🚀 VM Auto-Deploy Setup - Покрокова інструкція

## 📊 Поточний стан (з аналізу):

```
✅ Ubuntu 24.04.2 LTS на Azure VM
✅ Python 3.12.3, Git, Docker, Node.js
✅ Playwright + Chromium встановлено
✅ Skyvern працює (порт 8000)
✅ Worker v2 вже ПРАЦЮЄ (process 34242)
✅ Репозиторій: /home/stuard/jobbot-norway-public
✅ Гілка: claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu
```

## ⚠️ Що треба додати (15 хвилин):

```
❌ Встановити supabase Python пакет
❌ Налаштувати systemd service (замість nohup)
❌ Налаштувати GitHub Actions Runner
```

---

## 📋 ТВОЇ ДІЇ (copy-paste в термінал):

### КРОК 1: Встановити відсутні залежності (2 хв)

```bash
cd /home/stuard/jobbot-norway-public
chmod +x vm_setup/fix_dependencies.sh
bash vm_setup/fix_dependencies.sh
```

**Що робить:**
- Встановлює `supabase==2.7.4` Python пакет
- Перевіряє що все працює

---

### КРОК 2: Встановити Worker як systemd service (3 хв)

```bash
cd /home/stuard/jobbot-norway-public
chmod +x vm_setup/install_service.sh
sudo bash vm_setup/install_service.sh
```

**Що робить:**
- Створює systemd service `jobbot-worker`
- Автоматичний старт при перезавантаженні VM
- Автоматичний перезапуск при падінні
- Логи: `journalctl -u jobbot-worker -f`

**Після цього Worker буде працювати як сервіс!**

---

### КРОК 3: Налаштувати GitHub Actions Runner (10 хв)

```bash
cd /home/stuard/jobbot-norway-public
chmod +x vm_setup/setup_github_runner.sh
bash vm_setup/setup_github_runner.sh
```

**Що буде:**
1. Скрипт запитає чи робити автоматично → Відповіси `Y`
2. Скрипт завантажить GitHub Actions Runner
3. Скрипт попросить **TOKEN** з GitHub

**Як отримати TOKEN:**

1. **Відкрий в браузері:**
   ```
   https://github.com/SmmShaman/jobbot-norway-public/settings/actions/runners/new
   ```

2. **Вибери:**
   - Operating System: **Linux**
   - Architecture: **X64**

3. **Скопіюй TOKEN** з команди:
   ```bash
   ./config.sh --url https://github.com/... --token XXXXXXXX
   ```
   (Довгий рядок після `--token`)

4. **Вставляй TOKEN** в термінал коли скрипт попросить

5. **Готово!** Runner буде працювати як systemd service

---

## ✅ Перевірка що все працює:

### 1. Перевірити Worker service:

```bash
# Статус
sudo systemctl status jobbot-worker

# Логи (live)
sudo journalctl -u jobbot-worker -f

# Або файл логів
tail -f /home/stuard/jobbot-norway-public/worker/worker.log
```

**Очікуваний вивід:**
```
● jobbot-worker.service - JobBot Norway Worker v2
     Active: active (running)
     ...
     💤 No pending tasks. Waiting 10s...
```

---

### 2. Перевірити GitHub Runner:

```bash
cd /home/stuard/actions-runner
sudo ./svc.sh status
```

**Очікуваний вивід:**
```
● actions.runner.SmmShaman-jobbot-norway-public.azure-vm-worker.service
     Active: active (running)
```

**АБО перевір в браузері:**
```
https://github.com/SmmShaman/jobbot-norway-public/settings/actions/runners
```

Має показати: **azure-vm-worker** (Idle) 🟢

---

## 🎯 Як це працюватиме ПІСЛЯ налаштування:

### Коли Я (Claude) пушу код:

```
1. Я пишу код локально
2. git commit && git push
3. GitHub Actions спрацьовує
4. Відправляє команди на ТВОЮ VM через Runner
5. VM:
   - git pull (оновлює код)
   - pip install -r requirements.txt (якщо треба)
   - systemctl restart jobbot-worker (перезапускає Worker)
6. Я бачу в GitHub Actions що все OK
7. Worker працює з новим кодом!
```

**ТИ НІЧОГО НЕ РОБИШ!** Все автоматично.

---

## 📚 Корисні команди після налаштування:

### Worker управління:

```bash
# Статус
sudo systemctl status jobbot-worker

# Перезапустити
sudo systemctl restart jobbot-worker

# Зупинити
sudo systemctl stop jobbot-worker

# Запустити
sudo systemctl start jobbot-worker

# Логи (live)
sudo journalctl -u jobbot-worker -f

# Логи (файл)
tail -f /home/stuard/jobbot-norway-public/worker/worker.log
```

### GitHub Runner:

```bash
cd /home/stuard/actions-runner

# Статус
sudo ./svc.sh status

# Перезапустити
sudo ./svc.sh restart

# Зупинити
sudo ./svc.sh stop

# Запустити
sudo ./svc.sh start
```

### Git операції:

```bash
cd /home/stuard/jobbot-norway-public

# Подивитись поточний стан
git status

# Переключитись на гілку
git checkout claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu

# Отримати оновлення
git pull

# Подивитись останні коміти
git log --oneline -5
```

---

## 🔥 Тестування auto-deploy:

Після налаштування GitHub Runner, я зможу протестувати:

1. Я створю тестовий коміт
2. git push на GitHub
3. GitHub Actions запуститься **НА ТВОЇЙ VM**
4. Worker автоматично перезапуститься
5. Ти побачиш в логах: "✅ Deployment Complete!"

---

## 🆘 Troubleshooting:

### Worker не запускається:

```bash
# Перевір логи помилок
sudo journalctl -u jobbot-worker -n 50

# Перевір .env файл
cat /home/stuard/jobbot-norway-public/worker/.env

# Перевір що supabase встановлено
python3 -c "import supabase; print('OK')"

# Спробуй запустити вручну
cd /home/stuard/jobbot-norway-public/worker
python3 worker_v2.py
```

### GitHub Runner не підключається:

```bash
# Перевір статус
cd /home/stuard/actions-runner
sudo ./svc.sh status

# Перевір логи
sudo journalctl -u actions.runner.* -n 50

# Перезапусти
sudo ./svc.sh restart

# Перевір в GitHub UI
# https://github.com/SmmShaman/jobbot-norway-public/settings/actions/runners
```

---

## 📊 Структура файлів:

```
/home/stuard/jobbot-norway-public/
├── vm_setup/
│   ├── fix_dependencies.sh          ← КРОК 1
│   ├── install_service.sh           ← КРОК 2
│   ├── setup_github_runner.sh       ← КРОК 3
│   ├── jobbot-worker.service        ← Systemd config
│   └── README_VM_SETUP.md           ← Ця інструкція
│
├── .github/workflows/
│   └── deploy-vm.yml                ← Auto-deploy workflow
│
└── worker/
    ├── worker_v2.py                 ← Worker код
    ├── requirements.txt             ← Python залежності
    ├── .env                         ← Secrets
    └── worker.log                   ← Логи

/home/stuard/actions-runner/          ← GitHub Runner (буде створено)
├── config.sh
├── run.sh
└── svc.sh
```

---

## 🎉 Після виконання всіх кроків:

```
✅ Worker працює як systemd service
✅ GitHub Actions Runner підключений
✅ Автодеплой налаштований
✅ Я (Claude) можу оновлювати код через git push
✅ Ти тільки дивишся результати в дашборді!
```

---

## 🚀 ДАВАЙ ПОЧНЕМО!

**Запускай по черзі:**

```bash
# КРОК 1
bash vm_setup/fix_dependencies.sh

# КРОК 2
sudo bash vm_setup/install_service.sh

# КРОК 3
bash vm_setup/setup_github_runner.sh
```

**Час виконання:** 15 хвилин

**Результат:** Повністю автоматична система! 🎯
