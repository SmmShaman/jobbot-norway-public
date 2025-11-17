"""Telegram webhook handler for processing approval callbacks."""
import sys
import asyncio
from pathlib import Path
from .job_manager import JobManager
from .telegram_bot import TelegramBot
from .apply import submit_application

class TelegramApprovalHandler:
    def __init__(self):
        self.job_manager = JobManager()
        self.telegram_bot = TelegramBot()
    
    def process_callback(self, callback_data: str, chat_id: str) -> bool:
        """Process Telegram callback for job approval."""
        try:
            # Parse callback data: "apply_123", "skip_123", "review_123"
            action, job_id_str = callback_data.split('_')
            job_id = int(job_id_str)
            
            job = self.job_manager.get_job(job_id)
            if not job:
                self.telegram_bot.send_message("❌ Job not found in database.")
                return False
            
            if action == 'apply':
                return self.handle_apply_approval(job_id, job)
            elif action == 'skip':
                return self.handle_skip(job_id, job)
            elif action == 'review':
                return self.handle_review_request(job_id, job)
            else:
                self.telegram_bot.send_message("❌ Unknown action.")
                return False
                
        except Exception as e:
            print(f"Error processing callback: {e}")
            self.telegram_bot.send_message(f"❌ Error: {e}")
            return False
    
    def handle_apply_approval(self, job_id: int, job: dict) -> bool:
        """Handle approved application."""
        try:
            # Update status to approved
            self.job_manager.update_job_status(job_id, 'APPROVED')
            
            # Check if letter exists
            letter_file = Path(f"/app/data/letters/{job_id}.txt")
            if not letter_file.exists():
                self.telegram_bot.send_message(f"❌ Letter file missing for job {job_id}")
                return False
            
            # Send confirmation
            self.telegram_bot.send_message(
                f"✅ <b>Application Approved</b>\n\n"
                f"<b>Position:</b> {job['title']}\n"
                f"<b>Company:</b> {job.get('company', 'Unknown')}\n\n"
                f"Starting application process..."
            )
            
            # Queue for application (this would normally trigger the apply script)
            self.job_manager.update_job_status(job_id, 'QUEUED_FOR_APPLICATION')
            
            print(f"✅ Job {job_id} approved and queued for application")
            return True
            
        except Exception as e:
            print(f"Error handling apply approval: {e}")
            return False
    
    def handle_skip(self, job_id: int, job: dict) -> bool:
        """Handle skipped job."""
        try:
            self.job_manager.update_job_status(job_id, 'MANUALLY_SKIPPED')
            
            self.telegram_bot.send_message(
                f"⏭️ <b>Job Skipped</b>\n\n"
                f"<b>Position:</b> {job['title']}\n"
                f"<b>Company:</b> {job.get('company', 'Unknown')}\n\n"
                f"Job marked as skipped."
            )
            
            print(f"✅ Job {job_id} marked as skipped")
            return True
            
        except Exception as e:
            print(f"Error handling skip: {e}")
            return False
    
    def handle_review_request(self, job_id: int, job: dict) -> bool:
        """Handle review request."""
        try:
            self.job_manager.update_job_status(job_id, 'MANUAL_REVIEW')
            
            # Send detailed job information
            letter_file = Path(f"/app/data/letters/{job_id}.txt")
            letter_text = ""
            if letter_file.exists():
                letter_text = letter_file.read_text(encoding='utf-8')[:500] + "..."
            
            review_message = f"""
📝 <b>Job Review Details</b>

<b>Position:</b> {job['title']}
<b>Company:</b> {job.get('company', 'Unknown')}
<b>Source:</b> {job.get('source', 'Unknown')}
<b>Relevance Score:</b> {job.get('relevance_score', 'N/A')}%

<b>Job URL:</b> <a href="{job['url']}">View Job Posting</a>

<b>Generated Cover Letter Preview:</b>
{letter_text}

<b>Status:</b> Marked for manual review
            """
            
            self.telegram_bot.send_message(review_message)
            
            print(f"✅ Job {job_id} marked for manual review")
            return True
            
        except Exception as e:
            print(f"Error handling review: {e}")
            return False

def main():
    """CLI entry point for processing single callback."""
    if len(sys.argv) != 3:
        print("Usage: python -m src.telegram_handler <callback_data> <chat_id>")
        sys.exit(1)
    
    callback_data = sys.argv[1]
    chat_id = sys.argv[2]
    
    handler = TelegramApprovalHandler()
    success = handler.process_callback(callback_data, chat_id)
    
    if success:
        print(f"✅ Successfully processed callback: {callback_data}")
    else:
        print(f"❌ Failed to process callback: {callback_data}")
        sys.exit(1)

if __name__ == "__main__":
    main()
