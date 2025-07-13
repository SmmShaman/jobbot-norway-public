import os
import json
import gspread
from datetime import datetime

class SheetsScreenshotManager:
    def __init__(self, username):
        self.username = username
        self.setup_google_sheets()
        
    def setup_google_sheets(self):
        try:
            # Читаємо credentials з .env
            with open('/app/.env', 'r') as f:
                content = f.read()
                
            # Знаходимо GOOGLE_CREDENTIALS_JSON
            for line in content.split('\n'):
                if line.startswith('GOOGLE_CREDENTIALS_JSON='):
                    creds_json = line.split('=', 1)[1].strip()
                    break
            
            credentials = json.loads(creds_json)
            self.gc = gspread.service_account_from_dict(credentials)
            
            # Створюємо таблицю
            sheet_name = f'JobBot_{self.username}'
            try:
                self.spreadsheet = self.gc.open(sheet_name)
                self.sheet = self.spreadsheet.sheet1
                print(f'✅ Відкрито таблицю: {sheet_name}')
            except:
                self.spreadsheet = self.gc.create(sheet_name)
                self.sheet = self.spreadsheet.sheet1
                self.setup_headers()
                print(f'✅ Створено таблицю: {sheet_name}')
                
        except Exception as e:
            print(f'❌ Google Sheets помилка: {e}')
            self.sheet = None
    
    def setup_headers(self):
        headers = [
            'Дата', 'Час', 'Вакансія', 'Компанія', 'Лінк вакансії', 
            'AI Score', 'Рекомендація', 'Поточний крок', 'Скріншот', 
            'Cover Letter', 'Сайт роботодавця', 'Статус заявки', 
            'NAV звітовано', 'Відповідь роботодавця', 'Примітки'
        ]
        self.sheet.insert_row(headers, 1)
        print('✅ Заголовки створено')
    
    def add_step(self, job_data, step_name, screenshot_path=None):
        if not self.sheet:
            return
            
        now = datetime.now()
        row_data = [
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M:%S'),
            job_data.get('title', ''),
            job_data.get('company', ''),
            job_data.get('url', ''),
            job_data.get('ai_score', ''),
            job_data.get('recommendation', ''),
            step_name,
            screenshot_path or '',
            job_data.get('cover_letter_url', ''),
            job_data.get('employer_site', ''),
            job_data.get('application_status', 'В процесі'),
            job_data.get('nav_reported', 'НІ'),
            job_data.get('employer_response', ''),
            job_data.get('notes', '')
        ]
        
        try:
            self.sheet.insert_row(row_data, 2)
            print(f'✅ Додано крок: {step_name} для {job_data.get("title", "")}')
        except Exception as e:
            print(f'❌ Помилка запису: {e}')

