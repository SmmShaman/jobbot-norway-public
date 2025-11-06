#!/bin/bash
# Render Backend Deployment Script
# This script guides through Render deployment

set -e  # Exit on error

echo "🎨 JobBot Norway - Render Backend Deployment"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}ℹ️  Render Deployment Methods:${NC}"
echo ""
echo "  1) 🖱️  GUI Dashboard (Recommended) - через веб-інтерфейс"
echo "  2) 🔗 GitHub Auto-Deploy - автоматично з GitHub"
echo ""
echo "Render не має CLI як Railway, тому deployment через Dashboard."
echo ""

read -p "Продовжити з інструкціями? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Скасовано."
    exit 1
fi

echo ""
echo -e "${GREEN}📋 Крок 1: Підготовка Environment Variables${NC}"
echo "=============================================="
echo ""

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env файл не знайдено!${NC}"
    echo "Створіть backend/.env з усіма потрібними змінними"
    exit 1
fi

echo -e "${GREEN}✅ .env знайдено${NC}"
echo ""
echo "Скопіюй ці змінні (вони будуть потрібні в Render Dashboard):"
echo ""
echo -e "${YELLOW}=========== ENVIRONMENT VARIABLES ===========${NC}"
cat .env | grep -v '^#' | grep -v '^$'
echo -e "${YELLOW}=============================================${NC}"
echo ""
echo -e "${BLUE}💾 Збережено у clipboard? (Mac: pbcopy, Linux: xclip)${NC}"
echo ""

# Try to copy to clipboard if possible
if command -v pbcopy &> /dev/null; then
    cat .env | grep -v '^#' | grep -v '^$' | pbcopy
    echo -e "${GREEN}✅ Скопійовано в clipboard (Mac)${NC}"
elif command -v xclip &> /dev/null; then
    cat .env | grep -v '^#' | grep -v '^$' | xclip -selection clipboard
    echo -e "${GREEN}✅ Скопійовано в clipboard (Linux)${NC}"
else
    echo -e "${YELLOW}⚠️  Скопіюй змінні вручну з виводу вище${NC}"
fi

echo ""
echo -e "${GREEN}📋 Крок 2: Створення Render Web Service${NC}"
echo "=========================================="
echo ""
echo "1. Відкрий: ${BLUE}https://dashboard.render.com${NC}"
echo ""
echo "2. Натисни: ${YELLOW}New + → Web Service${NC}"
echo ""
echo "3. Підключи GitHub:"
echo "   - Configure account → Select repositories"
echo "   - Вибери: ${BLUE}SmmShaman/jobbot-norway-public${NC}"
echo ""
echo "4. Налаштування сервісу:"
echo "   ${YELLOW}Name:${NC}                jobbot-backend"
echo "   ${YELLOW}Region:${NC}              Frankfurt (EU Central)"
echo "   ${YELLOW}Branch:${NC}              claude/netlify-ui-011CUqJXNw4wkoYPis8TAkxF"
echo "   ${YELLOW}Root Directory:${NC}      backend"
echo "   ${YELLOW}Runtime:${NC}             Python 3"
echo "   ${YELLOW}Build Command:${NC}       pip install -r requirements.txt"
echo "   ${YELLOW}Start Command:${NC}       uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
echo ""
echo "5. Instance Type:"
echo "   Вибери: ${GREEN}Free${NC} ($0/month, 750 hours)"
echo ""
echo "6. Advanced → Health Check Path:"
echo "   ${YELLOW}/health${NC}"
echo ""

read -p "Натисни Enter коли дійдеш до Environment Variables..."

echo ""
echo -e "${GREEN}📋 Крок 3: Додавання Environment Variables${NC}"
echo "==========================================="
echo ""
echo "У Render Dashboard → Environment:"
echo ""
echo "Додай ці змінні (скопіюй з виводу вище або з .env):"
echo ""

# Parse .env and show in Render format
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue

    # Remove quotes
    value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

    echo -e "${YELLOW}$key${NC} = $value"
done < .env

echo ""
echo -e "${BLUE}⚠️  ВАЖЛИВО: Додай також CORS для Netlify:${NC}"
echo ""
echo -e "${YELLOW}CORS_ORIGINS${NC} = http://localhost:3000,http://localhost:5173,https://твій-netlify-сайт.netlify.app"
echo ""

read -p "Натисни Enter коли додав всі змінні..."

echo ""
echo -e "${GREEN}📋 Крок 4: Deploy!${NC}"
echo "==================="
echo ""
echo "1. Натисни ${YELLOW}Create Web Service${NC}"
echo ""
echo "2. Render почне build (займе 2-3 хвилини)"
echo ""
echo "3. Коли deploy завершиться, скопіюй твій URL:"
echo "   Виглядає як: ${BLUE}https://jobbot-backend.onrender.com${NC}"
echo ""

read -p "Натисни Enter коли deploy завершився..."

echo ""
echo -e "${GREEN}📋 Крок 5: Отримати URL${NC}"
echo "======================="
echo ""
echo "Твій Render URL:"
echo ""
read -p "Вставити URL сюди: " RENDER_URL

if [ -z "$RENDER_URL" ]; then
    echo -e "${YELLOW}⚠️  URL не вказано. Знайди його в Render Dashboard.${NC}"
    RENDER_URL="https://твій-сервіс.onrender.com"
fi

echo ""
echo -e "${GREEN}✅ Backend URL: $RENDER_URL${NC}"
echo ""

echo ""
echo -e "${GREEN}📋 Крок 6: Перевірка Health Check${NC}"
echo "=================================="
echo ""
echo "Тестую backend..."

sleep 3  # Wait for service to be fully ready

if curl -s "$RENDER_URL/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend працює!${NC}"
else
    echo -e "${YELLOW}⚠️  Backend ще запускається або є помилка${NC}"
    echo "   Перевір логи в Render Dashboard"
fi

echo ""
echo -e "${GREEN}📋 Крок 7: Оновлення Netlify${NC}"
echo "=============================="
echo ""
echo "Тепер потрібно оновити Netlify:"
echo ""
echo "Варіант A - Dashboard:"
echo "  1. https://app.netlify.com"
echo "  2. Твій сайт → Site settings → Environment variables"
echo "  3. Edit VITE_API_URL = ${BLUE}$RENDER_URL${NC}"
echo "  4. Save + Trigger deploy"
echo ""
echo "Варіант B - CLI:"
echo "  ${YELLOW}netlify env:set VITE_API_URL $RENDER_URL${NC}"
echo "  ${YELLOW}netlify deploy --prod${NC}"
echo ""

read -p "Натисни Enter коли оновив Netlify..."

echo ""
echo -e "${GREEN}🎉 Deployment завершено!${NC}"
echo "======================="
echo ""
echo "📊 Твої URLs:"
echo "   Frontend: https://твій-сайт.netlify.app"
echo "   Backend:  $RENDER_URL"
echo "   API Docs: $RENDER_URL/docs"
echo ""
echo "🧪 Тести:"
echo "   Health:   curl $RENDER_URL/health"
echo "   Frontend: Відкрий Netlify сайт → Login → Scan Jobs Now"
echo ""
echo -e "${GREEN}✅ Все готово! Система працює на Render (безкоштовно)!${NC}"
echo ""
echo "💡 Корисні посилання:"
echo "   Render Dashboard: https://dashboard.render.com"
echo "   Logs: Dashboard → твій service → Logs"
echo "   Metrics: Dashboard → твій service → Metrics"
echo ""
echo "⚠️  FREE TIER обмеження:"
echo "   - Service засипає після 15 хв неактивності"
echo "   - Перший запит після сну займе 30-60 секунд"
echo "   - 750 годин/місяць (достатньо для 1 сервісу)"
echo ""
echo "🚀 Щоб уникнути сну (upgrade до $7/month):"
echo "   Dashboard → твій service → Settings → Instance Type → Starter"
echo ""
