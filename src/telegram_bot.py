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

import threading
import time
import requests as req

def listen_for_commands(self):
    """Listen for Telegram commands using polling."""
    offset = 0
    while True:
        try:
            url = f"{self.base_url}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            response = req.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        
                        # Check for /start command
                        if "message" in update and "text" in update["message"]:
                            text = update["message"]["text"]
                            if text == "/start":
                                # Call N8N webhook
                                webhook_url = "http://localhost:5678/webhook/start-jobbot"
                                req.post(webhook_url, json={"triggered_by": "telegram"})
                                self.send_message("🚀 JobBot workflow запущено!")
                                
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

def start_bot_listener(self):
    """Start bot in background thread."""
    thread = threading.Thread(target=self.listen_for_commands, daemon=True)
    thread.start()
    return thread

# Add methods to TelegramBot class
TelegramBot.listen_for_commands = listen_for_commands  
TelegramBot.start_bot_listener = start_bot_listener

if __name__ == "__main__":
    bot = TelegramBot()
    print("🤖 Telegram bot started. Listening for /start command...")
    bot.start_bot_listener()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Bot stopped.")
