"""Enhanced main workflow using deep job analyzer."""
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

from .deep_job_analyzer import DeepJobAnalyzer
from .job_manager import JobManager
from .telegram_bot import TelegramBot
from .sheets_integration import SheetsTracker
from .letter_generator import generate_cover_letter, save_letter

class EnhancedJobBotWorkflow:
    def __init__(self):
        self.job_manager = JobManager()
        self.telegram_bot = TelegramBot()
        self.sheets_tracker = SheetsTracker()
        self.deep_analyzer = DeepJobAnalyzer()
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        config_file = Path("/app/src/config/search_config.json")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return {}

    def run_enhanced_workflow(self):
        """Run enhanced workflow with deep analysis."""
        print("🚀 Starting Enhanced JobBot Workflow")
        print("=" * 50)

        try:
            # Get configuration
            nav_config = self.config.get("search_sources", {}).get("arbeidsplassen.nav.no", {})
            if not nav_config.get("enabled", False):
                print("❌ NAV source is disabled")
                return

            search_urls = nav_config.get("search_urls", [])
            if not search_urls:
                print("❌ No search URLs configured")
                return

            user_skills = self.config.get("user_profile", {}).get("skills", "")
            min_relevance = self.config.get("user_profile", {}).get("min_relevance_score", 70)

            all_relevant_jobs = []

            # Process each search URL
            for search_url in search_urls:
                print(f"\n🔍 Processing: {search_url}")
                
                relevant_jobs = self.deep_analyzer.analyze_jobs_from_search_url(
                    search_url, user_skills, min_relevance
                )
                
                all_relevant_jobs.extend(relevant_jobs)

            print(f"\n📊 Total relevant jobs found: {len(all_relevant_jobs)}")

            if not all_relevant_jobs:
                print("ℹ️ No relevant jobs found. Workflow complete.")
                return

            # Store and process jobs
            stored_jobs = []
            for job_data in all_relevant_jobs:
                job_id = self.job_manager.add_job(job_data)
                if job_id:
                    job_data['id'] = job_id
                    stored_jobs.append(job_data)
                    print(f"💾 Stored job: {job_data['title']}")

            # Generate cover letters for highly relevant jobs
            auto_apply_threshold = self.config.get("application_settings", {}).get("auto_apply_threshold", 85)
            
            for job in stored_jobs:
                relevance_score = job.get('relevance_score', 0)
                
                try:
                    # Generate cover letter
                    letter_text = generate_cover_letter(
                        job['title'],
                        job.get('company', ''),
                        job.get('description', ''),
                        user_skills
                    )
                    
                    letter_file = save_letter(job['id'], letter_text)
                    job['letter_file'] = str(letter_file)
                    
                    # Update status
                    if relevance_score >= auto_apply_threshold:
                        self.job_manager.update_job_status(job['id'], 'AUTO_APPROVED')
                        status = "🤖 AUTO-APPROVED"
                    else:
                        self.job_manager.update_job_status(job['id'], 'NEEDS_APPROVAL')
                        # Send Telegram approval request
                        self.telegram_bot.send_approval_request(job, relevance_score)
                        status = "📱 APPROVAL_REQUESTED"
                    
                    print(f"✍️ {job['title']}: {relevance_score}% - {status}")
                    
                    # Log to sheets
                    self.sheets_tracker.log_application(job, status)
                    
                except Exception as e:
                    print(f"❌ Error processing job {job['id']}: {e}")

            # Summary
            print("=" * 50)
            print("📋 Enhanced Workflow Summary:")
            print(f"  • Relevant jobs found: {len(all_relevant_jobs)}")
            print(f"  • Jobs stored: {len(stored_jobs)}")
            print(f"  • Auto-approved: {len([j for j in stored_jobs if j.get('relevance_score', 0) >= auto_apply_threshold])}")
            print("🎉 Enhanced workflow completed successfully!")

        except Exception as e:
            print(f"💥 Enhanced workflow failed: {e}")
            self.telegram_bot.send_message(f"❌ Enhanced JobBot workflow failed: {e}")

if __name__ == "__main__":
    workflow = EnhancedJobBotWorkflow()
    workflow.run_enhanced_workflow()
