import os
import sys
sys.path.append('/app/src')

from workflow_integration import WorkflowIntegration
from local_storage_manager import LocalStorageManager
from resume_loader import create_ai_prompt
from ai_analyzer import analyze_job_relevance
from telegram_bot import TelegramBot
from datetime import datetime

class WorkflowWithScreenshots(WorkflowIntegration):
    def __init__(self, username):
        self.username = username
        self.telegram = TelegramBot()
        self.storage = LocalStorageManager(self.username)
        
    def take_step_screenshot(self, page, step_name, job_data):
        """Робить скріншот та зберігає крок"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{self.username}_{step_name.replace(" ", "_")}_{timestamp}.png'
            screenshot_path = f'/app/data/screenshots/{self.username}/{filename}'
            
            # Створюємо папку
            os.makedirs(f'/app/data/screenshots/{self.username}', exist_ok=True)
            
            # Робимо скріншот
            page.screenshot(path=screenshot_path, full_page=True)
            
            # Зберігаємо в storage
            self.storage.add_job_step(job_data, step_name, screenshot_path)
            
            print(f'📸 Скріншот збережено: {filename}')
            return screenshot_path
            
        except Exception as e:
            print(f'❌ Помилка скріншоту: {e}')
            # Зберігаємо крок без скріншоту
            self.storage.add_job_step(job_data, step_name)
            return None
    
    def analyze_jobs_with_logging(self, jobs):
        """Аналізує вакансії з логуванням кожного кроку"""
        user_ai_text = create_ai_prompt(self.username)
        
        analyzed_jobs = []
        for job in jobs:
            try:
                # Підготовка даних про вакансію
                job_data = {
                    'title': job['title'],
                    'company': job.get('company', 'Невідомо'),
                    'url': job['url']
                }
                
                # Крок 1: Початок аналізу
                self.storage.add_job_step(job_data, 'Початок AI аналізу')
                
                # Крок 2: AI аналіз
                analysis = analyze_job_relevance(job, user_ai_text[:500], user_ai_text)
                job['analysis'] = analysis
                analyzed_jobs.append(job)
                
                # Крок 3: Результат аналізу
                job_data.update({
                    'ai_score': f'{analysis["relevance_score"]}%',
                    'recommendation': analysis['recommendation']
                })
                self.storage.add_job_step(job_data, 'AI аналіз завершено')
                
                print(f'✅ {job["title"]}: {analysis["relevance_score"]}% - {analysis["recommendation"]}')
                
            except Exception as e:
                print(f'❌ Помилка аналізу {job["title"]}: {e}')
                job['analysis'] = {'relevance_score': 0, 'is_relevant': False, 'recommendation': 'SKIP'}
                analyzed_jobs.append(job)
        
        return analyzed_jobs

