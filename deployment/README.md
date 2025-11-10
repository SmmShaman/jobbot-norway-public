# JobBot Worker Deployment

## Автоматичне керування Worker через systemd

Цей каталог містить файли для налаштування JobBot Worker як systemd service, що дозволяє:

✅ Автоматичний запуск worker при старті системи
✅ Автоматичний перезапуск при падінні
✅ Керування через git push (GitHub Actions)
✅ Централізоване логування через journalctl

---

## Швидке налаштування

### Крок 1: Одноразове налаштування systemd

На твоєму VM виконай **ОДИН РАЗ**:

```bash
cd /home/stuard/jobbot-norway-public
sudo chmod +x deployment/setup_systemd.sh
sudo deployment/setup_systemd.sh
```

Це:
- Створить systemd service `worker_v2`
- Налаштує автозапуск
- Запустить worker

### Крок 2: Перевір що працює

```bash
sudo systemctl status worker_v2
```

Маєш побачити: `Active: active (running)`

### Крок 3: Подивись логи

```bash
sudo journalctl -u worker_v2 -f
```

---

## Після налаштування

**Ти більше нічого не робиш вручну!**

Коли я (Claude):
1. Роблю зміни в коді
2. Роблю commit + push

Автоматично:
- GitHub Actions deployment запускається
- Код оновлюється на VM
- Worker перезапускається через systemd
- Все працює 24/7

---

## Корисні команди

### Статус worker
```bash
sudo systemctl status worker_v2
```

### Перезапуск
```bash
sudo systemctl restart worker_v2
```

### Стоп
```bash
sudo systemctl stop worker_v2
```

### Старт
```bash
sudo systemctl start worker_v2
```

### Живі логи (real-time)
```bash
sudo journalctl -u worker_v2 -f
```

### Останні 100 рядків логів
```bash
sudo journalctl -u worker_v2 -n 100 --no-pager
```

### Логи за останню годину
```bash
sudo journalctl -u worker_v2 --since "1 hour ago"
```

### Відключити автозапуск
```bash
sudo systemctl disable worker_v2
```

### Включити автозапуск
```bash
sudo systemctl enable worker_v2
```

---

## Файли

- `worker_v2.service` - systemd service конфігурація
- `setup_systemd.sh` - скрипт для автоматичного налаштування
- `README.md` - ця інструкція

---

## Що далі?

Після виконання `setup_systemd.sh`:

1. Worker працює 24/7
2. Я можу керувати через git push
3. Ти можеш переглядати логи: `sudo journalctl -u worker_v2 -f`
4. Worker автоматично перезапуститься при падінні
5. Worker автоматично запуститься після перезавантаження VM

**Все!** Більше нічого налаштовувати не треба.
