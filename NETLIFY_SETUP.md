# 🌐 Netlify Setup - Покрокова інструкція

## 🚀 Крок-за-кроком для підключення GitHub → Netlify

### Крок 1: Відкрий Netlify

1. Перейди на: https://app.netlify.com
2. Залогінься через GitHub (якщо ще не)

---

### Крок 2: Створи новий сайт

1. Натисни велику кнопку **"Add new site"**
2. Вибери **"Import an existing project"**

![Netlify New Site](https://docs.netlify.com/images/start-import.png)

---

### Крок 3: Підключи GitHub

1. Натисни **"Deploy with GitHub"**
2. Якщо попросить дозвіл - натисни **"Authorize Netlify"**
3. Netlify попросить доступ до репозиторіїв - дозволь

---

### Крок 4: Вибери репозиторій

1. В пошуку знайди: **`jobbot-norway-public`**
2. Клікни на нього

![Select Repo](https://docs.netlify.com/images/pick-repo.png)

---

### Крок 5: Налаштуй Build Settings

Заповни такі поля:

```
Branch to deploy:
claude/netlify-ui-011CUqJXNw4wkoYPis8TAkxF

Base directory:
web-app

Build command:
npm install && npm run build

Publish directory:
web-app/dist
```

![Build Settings](https://docs.netlify.com/images/configure-builds.png)

---

### Крок 6: Додай Environment Variables

**Перед тим як натиснути "Deploy"**, розгорни **"Advanced build settings"**

Додай 2 змінні:

**Variable 1:**
```
Key: VITE_SUPABASE_URL
Value: https://ptrmidlhfdbybxmyovtm.supabase.co
```

**Variable 2:**
```
Key: VITE_SUPABASE_ANON_KEY
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0cm1pZGxoZmRieWJ4bXlvdnRtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0MzQ3NDksImV4cCI6MjA3ODAxMDc0OX0.rdOIJ9iMnbz5uxmGrtxJxb0n1cwf6ee3ppz414IaDWM
```

**Variable 3** (поки залишимо порожнім, оновимо після backend deploy):
```
Key: VITE_API_URL
Value: http://localhost:8000
```

---

### Крок 7: Deploy!

1. Натисни велику зелену кнопку **"Deploy [site name]"**
2. Зачекай 2-3 хвилини
3. Netlify покаже процес build в реальному часі

---

### Крок 8: Перевір результат

Після успішного deploy:

1. Netlify покаже URL твого сайту (щось на кшталт):
   ```
   https://sparkly-trifle-abc123.netlify.app
   ```

2. Клікни на URL - має відкритись сторінка Login!

---

## ✅ Перевірка що все працює:

1. Відкрий твій Netlify URL
2. Натисни **"Sign Up"**
3. Введи email та password (мінімум 6 символів)
4. Натисни **"Sign Up"**
5. Має відкритись Dashboard!

**Якщо з'явився Dashboard - ВСЕ ПРАЦЮЄ!** 🎉

---

## 🔄 Автоматичний deploy при push

Тепер при кожному `git push` в гілку `claude/netlify-ui-011CUqJXNw4wkoYPis8TAkxF`:
- Netlify автоматично запустить build
- Через 2-3 хвилини зміни будуть на сайті

**Тестуємо:**
```bash
# Зроби будь-яку зміну
echo "test" >> web-app/README.md

# Commit і push
git add .
git commit -m "Test auto-deploy"
git push

# Відкрий Netlify Dashboard - побачиш новий deploy!
```

---

## 🎨 Налаштування Custom Domain (опціонально)

Якщо хочеш свій домен (наприклад `jobbot.no`):

1. В Netlify Dashboard → **"Domain settings"**
2. Натисни **"Add custom domain"**
3. Введи свій домен
4. Netlify покаже які DNS записи додати
5. Додай ці записи у свого domain provider
6. Зачекай 10-30 хвилин на DNS propagation
7. Netlify автоматично налаштує HTTPS (Let's Encrypt)

---

## 🔐 Security Headers

Netlify автоматично додасть security headers (вже налаштовано в `netlify.toml`):
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: no-referrer

---

## 📊 Моніторинг

В Netlify Dashboard ти можеш бачити:
- 📈 **Analytics** - скільки відвідувачів
- 🚀 **Deploys** - історія всіх deploy
- 📋 **Functions** - якщо додаси Netlify Functions
- 🔒 **Logs** - всі build logs

---

## ⚠️ Troubleshooting

### Build fails з помилкою "Module not found"
```bash
# Перевір що в web-app/ є файл package.json
# Перевір що Base directory = web-app
```

### "Environment variable not found"
```bash
# Перевір що додав всі 3 variables
# Перевір що немає зайвих пробілів в Keys
```

### Сайт відкривається, але "Loading..." нескінченно
```bash
# Перевір в browser console (F12)
# Скоріш за все помилка з Supabase credentials
# Перевір що VITE_SUPABASE_URL та VITE_SUPABASE_ANON_KEY правильні
```

---

## 📞 Потрібна допомога?

- 📖 [Netlify Docs](https://docs.netlify.com)
- 💬 [Netlify Community](https://answers.netlify.com)
- 🐛 GitHub Issues цього проекту

---

✅ **Netlify налаштований! Frontend готовий!** 🎉

**Наступний крок:** Налаштувати backend на Railway (див. DEPLOYMENT.md)
