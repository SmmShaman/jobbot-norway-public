"""Main workflow using Playwright for real job analysis."""
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

from .playwright_job_analyzer import PlaywrightJobAnalyzer
from .job_manager import JobManager
from .telegram_bot import TelegramBot
from .sheets_integration import SheetsTracker
from .letter_generator import generate_cover_letter, save_letter

class PlaywrightJobBotWorkflow:
    def __init__(self):
        self.job_manager = JobManager()
        self.telegram_bot = TelegramBot()
        self.sheets_tracker = SheetsTracker()
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        config_file = Path("/app/src/config/search_config.json")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return {}

    async def run_playwright_workflow(self):
        """Run workflow with Playwright real browser interaction."""
        print("🚀 Starting Playwright JobBot Workflow")
        print("=" * 60)

        try:
            nav_config = self.config.get("search_sources", {}).get("arbeidsplassen.nav.no", {})
            if not nav_config.get("enabled", False):
                print("❌ NAV source disabled")
                return

            search_urls = nav_config.get("search_urls", [])
            full_resume = self.config.get("user_profile", {}).get("full_resume", "")
            min_relevance = self.config.get("user_profile", {}).get("min_relevance_score", 70)

            if not full_resume:
                print("❌ No resume configured! Please add your full resume to config.")
                return

            analyzer = PlaywrightJobAnalyzer()
            all_relevant_jobs = []

            # Process each search URL with Playwright
            for search_url in search_urls[:1]:  # Test with first URL
                print(f"\n🎭 Playwright analysis: {search_url}")
                
                relevant_jobs = await analyzer.analyze_jobs_with_playwright(
                    search_url, full_resume, min_relevance
                )
                all_relevant_jobs.extend(relevant_jobs)

            print(f"\n📊 Total relevant jobs: {len(all_relevant_jobs)}")

            if not all_relevant_jobs:
                print("ℹ️ No relevant jobs found.")
                return

            # Store and process jobs
            auto_apply_threshold = self.config.get("application_settings", {}).get("auto_apply_threshold", 85)
            
            for job_data in all_relevant_jobs:
                # Store in database
                job_id = self.job_manager.add_job(job_data)
                job_data['id'] = job_id
                
                relevance_score = job_data.get('relevance_score', 0)
                
                # Generate cover letter
                letter_text = generate_cover_letter(
                    job_data['title'],
                    job_data.get('company', ''),
                    job_data.get('description', ''),
                    full_resume
                )
                
                letter_file = save_letter(job_id, letter_text)
                
                # Determine action
                if relevance_score >= auto_apply_threshold:
                    status = 'AUTO_APPROVED'
                    action = "🤖 AUTO-APPLY"
                else:
                    status = 'NEEDS_APPROVAL'
                    self.telegram_bot.send_approval_request(job_data, relevance_score)
                    action = "📱 APPROVAL_REQUESTED"
                
                self.job_manager.update_job_status(job_id, status)
                self.sheets_tracker.log_application(job_data, action)
                
                print(f"✅ {job_data['title']}: {relevance_score}% - {action}")

            print("=" * 60)
            print("🎉 Playwright workflow completed!")

        except Exception as e:
            print(f"💥 Playwright workflow error: {e}")
            self.telegram_bot.send_message(f"❌ Playwright workflow failed: {e}")

# Async runner
async def run_async_workflow():
    workflow = PlaywrightJobBotWorkflow()
    await workflow.run_playwright_workflow()

if __name__ == "__main__":
    asyncio.run(run_async_workflow())
