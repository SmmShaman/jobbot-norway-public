# JobBot Norway - Job Application Automation

## Структура проекту
- `workflows/` - N8N workflow JSON файли
- `src/` - Python модулі (API, AI аналіз, Skyvern integration)
- `data/` - Резюме, шаблони, логи

## Docker контейнери
- **n8n_jobhunter** (5679) - N8N workflow automation
- **skyvern-skyvern-1** (8000) - Skyvern для заповнення форм
- **pw_browser** - Playwright для BankID/NAV

## API Endpoints
- N8N: http://localhost:5679
- Skyvern: http://localhost:8000

## Робочі workflows
1. FINN.no scraper
2. AI relevance analyzer (Azure OpenAI)
3. Application sender (Skyvern)
4. Daily report generator

## Правила редагування
- Не змінювати credential IDs
- Тестувати локально перед commit
- Коментувати складну логіку
