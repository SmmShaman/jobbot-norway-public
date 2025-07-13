import os
import json
import gspread
from datetime import datetime
from playwright.sync_api import sync_playwright
import base64

class SheetsWithScreenshots:
    def __init__(self, username):
        self.username = username
        self.setup_google_sheets()
        
    def setup_google_sheets(self):
        """Налаштування Google Sheets"""
        try:
            # Читаємо credentials з .env
            with open('/app/.env', 'r') as f:
                for line in f:
                    if line.startswith('GOOGLE_CREDENTIALS_JSON='):
                        creds_json = line.split('=', 1)[1].strip()
                        break
            
            credentials = json.loads(creds_json)
            self.gc = gspread.service_account_from_dict(credentials)
            
            # Створюємо або відкриваємо таблицю
            sheet_name = f'JobBot_{self.username}'
            try:
                self.sheet = self.gc.open(sheet_name).sheet1
                print(f'✅ Відкрито існуючу таблицю: {sheet_name}')
            except:
                self.spreadsheet = self.gc.create(sheet_name)
                self.sheet = self.spreadsheet.sheet1
                self.setup_headers()
                print(f'✅ Створено нову таблицю: {sheet_name}')
                
        except Exception as e:
            print(f'❌ Помилка Google Sheets: {e}')
            self.sheet = None
    
    def setup_headers(self):
        """Створюємо заголовки таблиці"""
        headers = [
            'Дата', 'Час', 'Вакансія', 'Компанія', 'Лінк', 
            'AI Score', 'Status', 'Крок', 'Скріншот URL', 
            'Cover Letter', 'Сайт роботодавця', 'Застосовано', 
            'NAV звітовано', 'Відповідь роботодавця', 'Примітки'
        ]
        self.sheet.insert_row(headers, 1)
    
    def take_screenshot(self, page, step_name):
        """Робить скріншот поточної сторінки"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{self.username}_{step_name}_{timestamp}.png'
            screenshot_path = f'/app/data/screenshots/{filename}'
            
            # Створюємо папку якщо немає
            os.makedirs('/app/data/screenshots', exist_ok=True)
            
            # Робимо скріншот
            page.screenshot(path=screenshot_path, full_page=True)
            
            return screenshot_path, filename
            
        except Exception as e:
            print(f'❌ Помилка скріншоту: {e}')
            return None, None
    
    def add_job_row(self, job_data, step_name, screenshot_path=None):
        """Додає рядок в таблицю з даними про вакансію"""
        if not self.sheet:
            print('❌ Google Sheets недоступний')
            return
            
        try:
            now = datetime.now()
            row_data = [
                now.strftime('%Y-%m-%d'),      # Дата
                now.strftime('%H:%M:%S'),      # Час  
                job_data.get('title', ''),      # Вакансія
                job_data.get('company', ''),    # Компанія
                job_data.get('url', ''),        # Лінк
                job_data.get('ai_score', ''),   # AI Score
                job_data.get('status', ''),     # Status
                step_name,                      # Крок
                screenshot_path or '',          # Скріншот URL
                job_data.get('cover_letter', ''), # Cover Letter
                job_data.get('employer_site', ''), # Сайт роботодавця
                job_data.get('applied', 'НІ'),     # Застосовано
                job_data.get('nav_reported', 'НІ'), # NAV звітовано
                job_data.get('employer_response', ''), # Відповідь
                job_data.get('notes', '')           # Примітки
            ]
            
            self.sheet.insert_row(row_data, 2)  # Вставляємо на 2-й рядок
            print(f'✅ Додано рядок: {job_data.get("title", "")} - {step_name}')
            
        except Exception as e:
            print(f'❌ Помилка додавання рядка: {e}')

