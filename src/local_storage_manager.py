import os
import json
from datetime import datetime

class LocalStorageManager:
    def __init__(self, username):
        self.username = username
        self.data_dir = f'/app/data/users/{username}'
        self.jobs_file = f'{self.data_dir}/jobs_log.json'
        self.screenshots_dir = f'/app/data/screenshots/{username}'
        
        # Створюємо папки
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Ініціалізуємо файл якщо немає
        if not os.path.exists(self.jobs_file):
            self.save_data([])
    
    def load_data(self):
        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def save_data(self, data):
        with open(self.jobs_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_job_step(self, job_data, step_name, screenshot_path=None):
        data = self.load_data()
        
        now = datetime.now()
        job_entry = {
            'timestamp': now.isoformat(),
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'job_title': job_data.get('title', ''),
            'company': job_data.get('company', ''),
            'job_url': job_data.get('url', ''),
            'ai_score': job_data.get('ai_score', ''),
            'recommendation': job_data.get('recommendation', ''),
            'current_step': step_name,
            'screenshot': screenshot_path,
            'cover_letter': job_data.get('cover_letter_url', ''),
            'employer_site': job_data.get('employer_site', ''),
            'application_status': job_data.get('application_status', 'В процесі'),
            'nav_reported': job_data.get('nav_reported', 'НІ'),
            'employer_response': job_data.get('employer_response', ''),
            'notes': job_data.get('notes', '')
        }
        
        data.append(job_entry)
        self.save_data(data)
        print(f'✅ Збережено локально: {step_name} для {job_data.get("title", "")}')
        
        return len(data)

