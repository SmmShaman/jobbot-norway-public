"""Telegram integration for manual approval of job applications."""
import os
import json
import requests
from typing import Dict, Any

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, text: str) -> bool:
        """Send message to configured chat."""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram error: {e}")
            return False
    
    def send_approval_request(self, job_data: Dict[str, Any], relevance_score: int) -> bool:
        """Send job approval request with inline keyboard."""
        try:
            title = job_data.get('title', 'Unknown Job')
            company = job_data.get('company', 'Unknown Company')
            url = job_data.get('url', '')
            
            message = f"""
🔔 <b>New Job Application Request</b>

<b>Position:</b> {title}
<b>Company:</b> {company}
<b>AI Relevance Score:</b> {relevance_score}%
<b>Source:</b> {job_data.get('source', 'Unknown')}

<b>URL:</b> <a href="{url}">View Job</a>

Should I apply for this position?
            """
            
            # Inline keyboard for approval
            keyboard = {
                "inline_keyboard": [[
                    {"text": "✅ Apply", "callback_data": f"apply_{job_data.get('id')}"},
                    {"text": "❌ Skip", "callback_data": f"skip_{job_data.get('id')}"},
                    {"text": "📝 Review", "callback_data": f"review_{job_data.get('id')}"}
                ]]
            }
            
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": keyboard
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending approval request: {e}")
            return False
    
    def send_application_result(self, job_title: str, status: str) -> bool:
        """Send application result notification."""
        status_emoji = {
            "SUCCESS": "✅",
            "ERROR": "❌", 
            "PENDING": "⏳"
        }
        
        message = f"""
{status_emoji.get(status, '❓')} <b>Application Update</b>

<b>Position:</b> {job_title}
<b>Status:</b> {status}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        return self.send_message(message)

if __name__ == "__main__":
    # Test telegram integration
    bot = TelegramBot()
    test_job = {
        'id': 123,
        'title': 'Python Developer',
        'company': 'Test AS',
        'url': 'https://example.com/job/123',
        'source': 'finn.no'
    }
    bot.send_approval_request(test_job, 85)
