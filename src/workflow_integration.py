"""
Інтеграція всіх компонентів JobBot workflow
"""
import asyncio
import json
import sys
sys.path.append('/app/src')

from ai_analyzer import analyze_job_relevance
from local_storage_manager import LocalStorageManager
from telegram_bot import TelegramBot

class WorkflowIntegration:
    def __init__(self, username):
        self.username = username
        self.telegram = TelegramBot()
        self.storage = LocalStorageManager(self.username)
    
    async def run_daily_workflow(self):
        """Запуск щоденного workflow"""
        print(f"🚀 Starting daily workflow for {self.username}")
        
        # 1. Знайти джоби (симуляція)
        jobs = self.find_jobs()
        
        # 2. Аналіз джобів через AI
        analyzed_jobs = self.analyze_jobs(jobs)
        
        # 3. Розподіл за категоріями
        auto_apply, manual_review = self.categorize_jobs(analyzed_jobs)
        
        # 4. Автоподача заявок
        if auto_apply:
            await self.auto_apply_jobs(auto_apply)
        
        # 5. Відправка на ручну перевірку
        if manual_review:
            await self.send_manual_review(manual_review)
        
        return {"auto_applied": len(auto_apply), "manual_review": len(manual_review)}
    
    def find_jobs(self):
        # Симуляція знаходження джобів
        return [
            {"title": "Python Developer", "description": "FastAPI, Docker experience", "url": "test1.com"},
            {"title": "Project Manager", "description": "Agile, Scrum experience", "url": "test2.com"}
        ]
    
    def analyze_jobs(self, jobs):
        analyzed = []
        for job in jobs:
            try:
                result = analyze_job_relevance(
                    job["title"], 
                    job["description"], 
                    "Python, Project Management, AI integration"
                )
                job["analysis"] = result
                analyzed.append(job)
            except Exception as e:
                print(f"AI Analysis error: {e}")
                job["analysis"] = {"relevance_score": 0, "recommendation": "SKIP"}
                analyzed.append(job)
        return analyzed
    
    def categorize_jobs(self, jobs):
        auto_apply = [j for j in jobs if j["analysis"]["relevance_score"] >= 85]
        manual_review = [j for j in jobs if 30 <= j["analysis"]["relevance_score"] < 85]
        return auto_apply, manual_review
    
    async def auto_apply_jobs(self, jobs):
        for job in jobs:
            print(f"📝 Auto applying to: {job['title']}")
            # Тут буде виклик BankID workflow
        
        self.telegram.send_message(f"✅ Auto applied to {len(jobs)} jobs")
    
    async def send_manual_review(self, jobs):
        message = f"🔍 Manual review needed for {len(jobs)} jobs:\n"
        for job in jobs:
            message += f"• {job['title']} ({job['analysis']['relevance_score']}%)\n"
        
        self.telegram.send_message(message)

if __name__ == "__main__":
    workflow = WorkflowIntegration("vitalii")
    result = asyncio.run(workflow.run_daily_workflow())
    print(f"Workflow completed: {result}")
