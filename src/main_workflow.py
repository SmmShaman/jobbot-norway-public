"""Main workflow script that orchestrates the entire job application process."""
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Import our modules
from .scrapers.config_based_scraper import fetch_all_jobs_config
from .ai_analyzer import analyze_job_relevance
from .letter_generator import generate_cover_letter, save_letter
from .job_manager import JobManager
from .telegram_bot import TelegramBot
from .sheets_integration import SheetsTracker

class JobBotWorkflow:
    def __init__(self):
        self.job_manager = JobManager()
        self.telegram_bot = TelegramBot()
        self.sheets_tracker = SheetsTracker()
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
    
    def step_1_fetch_jobs(self) -> List[Dict[str, Any]]:
        """Step 1: Fetch new jobs from all sources."""
        print("🔍 Step 1: Fetching jobs from all sources...")
        
        try:
            jobs = fetch_all_jobs_config()
            print(f"✅ Found {len(jobs)} jobs total")
            return jobs
        except Exception as e:
            print(f"❌ Error fetching jobs: {e}")
            return []
    
    def step_2_store_jobs(self, jobs: List[Dict[str, Any]]) -> List[int]:
        """Step 2: Store jobs in database and return new job IDs."""
        print("💾 Step 2: Storing jobs in database...")
        
        new_job_ids = []
        for job in jobs:
            job_id = self.job_manager.add_job(job)
            if job_id:
                new_job_ids.append(job_id)
        
        print(f"✅ Stored {len(new_job_ids)} new jobs")
        return new_job_ids
    
    def step_3_analyze_jobs(self, job_ids: List[int]) -> List[Dict[str, Any]]:
        """Step 3: Analyze job relevance with AI."""
        print("🤖 Step 3: Analyzing job relevance...")
        
        user_skills = self.config.get("user_profile", {}).get("skills", "")
        analyzed_jobs = []
        
        for job_id in job_ids:
            try:
                job = self.job_manager.get_job(job_id)
                if not job:
                    continue
                
                # AI analysis
                analysis = analyze_job_relevance(
                    job['title'],
                    job.get('description', ''),
                    user_skills
                )
                
                # Update job with relevance score
                relevance_score = analysis.get('relevance_score', 0)
                
                # Update status based on score
                min_score = self.config.get("user_profile", {}).get("min_relevance_score", 70)
                if relevance_score >= min_score:
                    status = 'ANALYZED_RELEVANT'
                else:
                    status = 'ANALYZED_IRRELEVANT'
                
                self.job_manager.update_job_status(job_id, status)
                
                if status == 'ANALYZED_RELEVANT':
                    job['relevance_score'] = relevance_score
                    job['analysis'] = analysis
                    analyzed_jobs.append(job)
                
                print(f"  📊 {job['title']}: {relevance_score}% relevance")
                
            except Exception as e:
                print(f"❌ Error analyzing job {job_id}: {e}")
                self.job_manager.update_job_status(job_id, 'ERROR_ANALYSIS')
        
        print(f"✅ {len(analyzed_jobs)} jobs are relevant")
        return analyzed_jobs
    
    def step_4_generate_letters(self, relevant_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Step 4: Generate cover letters for relevant jobs."""
        print("✍️ Step 4: Generating cover letters...")
        
        jobs_with_letters = []
        user_skills = self.config.get("user_profile", {}).get("skills", "")
        
        for job in relevant_jobs:
            try:
                letter_text = generate_cover_letter(
                    job['title'],
                    job.get('company', ''),
                    job.get('description', ''),
                    user_skills
                )
                
                # Save letter to file
                letter_file = save_letter(job['id'], letter_text)
                
                # Update job status
                self.job_manager.update_job_status(job['id'], 'LETTER_GENERATED')
                
                job['letter_file'] = str(letter_file)
                job['letter_text'] = letter_text
                jobs_with_letters.append(job)
                
                print(f"  ✍️ Generated letter for: {job['title']}")
                
            except Exception as e:
                print(f"❌ Error generating letter for job {job['id']}: {e}")
                self.job_manager.update_job_status(job['id'], 'ERROR_LETTER')
        
        print(f"✅ Generated {len(jobs_with_letters)} cover letters")
        return jobs_with_letters
    
    def step_5_request_approval(self, jobs_with_letters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Step 5: Request manual approval via Telegram."""
        print("📱 Step 5: Requesting approval via Telegram...")
        
        auto_apply_threshold = self.config.get("application_settings", {}).get("auto_apply_threshold", 90)
        require_approval = self.config.get("application_settings", {}).get("require_manual_approval", True)
        
        approved_jobs = []
        
        for job in jobs_with_letters:
            try:
                relevance_score = job.get('relevance_score', 0)
                
                # Check if auto-apply
                if not require_approval and relevance_score >= auto_apply_threshold:
                    self.job_manager.update_job_status(job['id'], 'AUTO_APPROVED')
                    approved_jobs.append(job)
                    print(f"  🤖 Auto-approved: {job['title']} ({relevance_score}%)")
                else:
                    # Send Telegram approval request
                    success = self.telegram_bot.send_approval_request(job, relevance_score)
                    
                    if success:
                        self.job_manager.update_job_status(job['id'], 'APPROVAL_REQUESTED')
                        print(f"  📱 Approval requested: {job['title']}")
                    else:
                        print(f"  ❌ Failed to send approval for: {job['title']}")
                
            except Exception as e:
                print(f"❌ Error requesting approval for job {job['id']}: {e}")
        
        print(f"✅ Processed approval for {len(jobs_with_letters)} jobs")
        return approved_jobs
    
    def step_6_log_to_sheets(self, processed_jobs: List[Dict[str, Any]]):
        """Step 6: Log results to Google Sheets."""
        print("📊 Step 6: Logging to Google Sheets...")
        
        for job in processed_jobs:
            try:
                self.sheets_tracker.log_application(job, job.get('status', 'PROCESSED'))
            except Exception as e:
                print(f"❌ Error logging job {job['id']} to sheets: {e}")
        
        # Update daily stats
        try:
            stats = self.job_manager.get_stats()
            self.sheets_tracker.update_daily_stats(stats)
        except Exception as e:
            print(f"❌ Error updating daily stats: {e}")
        
        print("✅ Logged to Google Sheets")
    
    def run_daily_workflow(self):
        """Run the complete daily workflow."""
        print("🚀 Starting JobBot Daily Workflow")
        print("=" * 50)
        
        try:
            # Step 1: Fetch jobs
            jobs = self.step_1_fetch_jobs()
            if not jobs:
                print("ℹ️ No new jobs found. Workflow complete.")
                return
            
            # Step 2: Store jobs
            new_job_ids = self.step_2_store_jobs(jobs)
            if not new_job_ids:
                print("ℹ️ No new jobs to process. Workflow complete.")
                return
            
            # Step 3: Analyze relevance
            relevant_jobs = self.step_3_analyze_jobs(new_job_ids)
            if not relevant_jobs:
                print("ℹ️ No relevant jobs found. Workflow complete.")
                return
            
            # Step 4: Generate letters
            jobs_with_letters = self.step_4_generate_letters(relevant_jobs)
            
            # Step 5: Request approval
            approved_jobs = self.step_5_request_approval(jobs_with_letters)
            
            # Step 6: Log to sheets
            self.step_6_log_to_sheets(jobs_with_letters)
            
            # Summary
            print("=" * 50)
            print("📋 Workflow Summary:")
            print(f"  • Total jobs found: {len(jobs)}")
            print(f"  • New jobs stored: {len(new_job_ids)}")
            print(f"  • Relevant jobs: {len(relevant_jobs)}")
            print(f"  • Letters generated: {len(jobs_with_letters)}")
            print(f"  • Auto-approved: {len(approved_jobs)}")
            print("🎉 Daily workflow completed successfully!")
            
        except Exception as e:
            print(f"💥 Workflow failed: {e}")
            # Send error notification
            self.telegram_bot.send_message(f"❌ JobBot workflow failed: {e}")

if __name__ == "__main__":
    workflow = JobBotWorkflow()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 Running test mode...")
        # Run individual steps for testing
    else:
        # Run full workflow
        workflow.run_daily_workflow()
