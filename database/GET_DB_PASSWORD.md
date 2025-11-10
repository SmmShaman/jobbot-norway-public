# 🔑 Як отримати Database Password для Supabase

## Крок 1: Відкрий Supabase Dashboard

Іди на:
```
https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/settings/database
```

## Крок 2: Знайди Database Password

На сторінці буде секція **"Connection string"** або **"Database settings"**

Шукай поле:
- **"Database Password"**
- або **"Connection String"**

## Варіант A: Якщо є Database Password

Буде показано:
```
Database Password: ●●●●●●●●●●●●●●●●
[Show] [Reset]
```

Натисни **"Show"** або **"Copy"** щоб побачити пароль.

## Варіант B: Якщо є Connection String

Буде показано:
```
postgresql://postgres:[YOUR-PASSWORD]@db.ptrmidlhfdbybxmyovtm.supabase.co:5432/postgres
```

Пароль - це частина між `postgres:` та `@db.`

Приклад:
```
postgresql://postgres:MySecretPass123@db...
                     ^^^^^^^^^^^^^
                     Це твій пароль
```

## Крок 3: Скопіюй пароль

Збережи його в безпечному місці (наприклад, password manager).

---

## 🚀 Використання для деплою SQL функцій

### Автоматичний деплой через GitHub Actions

1. Іди на GitHub Actions:
```
https://github.com/SmmShaman/jobbot-norway-public/actions/workflows/deploy-sql-functions.yml
```

2. Натисни **"Run workflow"**

3. В полі **"Supabase Database Password"** вставай скопійований пароль

4. Натисни **"Run workflow"**

5. Почекай 1-2 хвилини - функції будуть створені автоматично!

---

## ⚠️ Безпека

- НЕ додавай Database Password в Git
- НЕ публікуй його в Issues або Pull Requests
- ТРИМАЙ його в секреті

Database Password ≠ Service Role Key:
- **Database Password** - для прямого PostgreSQL доступу (psql)
- **Service Role Key** - для Supabase API (JavaScript/Python клієнт)

Обидва дають повний доступ до бази, тому зберігай їх в безпеці!
