"""Enhanced workflow integration with all new AI components."""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class EnhancedWorkflowIntegration:
    def __init__(self, username: str):
        self.username = username
        self.user_config = self._load_user_config()
        self.user_data = self._prepare_user_data()
        
        # Initialize components
        self._init_components()
    
    def _load_user_config(self) -> Dict[str, Any]:
        """Load user configuration."""
        config_path = Path(f"~/jobbot/data/users/{self.username}/config.json").expanduser()
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading user config: {e}")
            return {}
    
    def _prepare_user_data(self) -> Dict[str, Any]:
        """Prepare user data for form filling."""
        user_info = self.user_config.get("user_info", {})
        profile = self.user_config.get("user_profile", {}).get("unified_resume", {}).get("unified_profile", {})
        
        return {
            "username": self.username,
            "full_name": user_info.get("full_name", ""),
            "email": user_info.get("email", ""),
            "phone": user_info.get("phone", ""),
            "location": profile.get("personal_info", {}).get("location", ""),
            "experience_years": profile.get("total_experience_years", 0),
            "linkedin": "",  # Add if available
            "resume_data": profile
        }
    
    def _init_components(self):
        """Initialize all workflow components."""
        try:
            from .multi_site_scraper import MultiSiteScraper
            from .ai_cover_letter_generator import AICoverLetterGenerator
            from .enhanced_sheets_integration import EnhancedSheetsTracker
            from .ai_analyzer import analyze_job_relevance
            from .telegram_bot import TelegramBot
            
            self.scraper = MultiSiteScraper()
            self.cover_letter_generator = AICoverLetterGenerator()
            self.sheets_tracker = EnhancedSheetsTracker()
            self.telegram_bot = TelegramBot()
            
            print(f"✅ Enhanced workflow initialized for {self.username}")
            
        except ImportError as e:
            print(f"❌ Error importing components: {e}")
            raise
    
    async def run_daily_enhanced_workflow(self) -> Dict[str, Any]:
        """Run the complete enhanced daily workflow."""
        print(f"🚀 Starting enhanced daily workflow for {self.username}")
        
        workflow_stats = {
            "total_jobs_found": 0,
            "new_jobs": 0,
            "ai_analyzed": 0,
            "auto_applied": 0,
            "manual_review": 0,
            "cover_letters_generated": 0,
            "applications_success": 0,
            "applications_failed": 0,
            "errors": []
        }
        
        try:
            # Step 1: Multi-site job scraping
            print("📊 Step 1: Scraping jobs from all sites...")
            all_jobs = await self.scraper.scrape_all_sites(self.user_config)
            workflow_stats["total_jobs_found"] = len(all_jobs)
            
            if not all_jobs:
                await self.telegram_bot.send_message(f"ℹ️ No new jobs found for {self.username}")
                return workflow_stats
            
            # Step 2: Filter new jobs
            print("🔍 Step 2: Filtering new jobs...")
            new_jobs = self._filter_new_jobs(all_jobs)
            workflow_stats["new_jobs"] = len(new_jobs)
            
            if not new_jobs:
                await self.telegram_bot.send_message(f"ℹ️ No new jobs found for {self.username}")
                return workflow_stats
            
            # Step 3: AI analysis for each job
            print("🤖 Step 3: AI analysis of job relevance...")
            analyzed_jobs = []
            
            for job in new_jobs:
                try:
                    # AI relevance analysis
                    user_skills = self._get_user_skills_summary()
                    ai_result = analyze_job_relevance(
                        job["title"], 
                        job["description"], 
                        user_skills
                    )
                    
                    job["ai_analysis"] = ai_result
                    job["relevance_score"] = ai_result.get("relevance_score", 0)
                    analyzed_jobs.append(job)
                    workflow_stats["ai_analyzed"] += 1
                    
                    # Log to Google Sheets immediately
                    await self.sheets_tracker.log_job_application(
                        self.username, job, "", "ANALYZED"
                    )
                    
                except Exception as e:
                    workflow_stats["errors"].append(f"AI analysis error for {job['title']}: {e}")
                    continue
            
            # Step 4: Categorize jobs
            print("📋 Step 4: Categorizing jobs...")
            auto_apply_threshold = self.user_config.get("application_settings", {}).get("auto_apply_threshold", 85)
            
            auto_apply_jobs = [j for j in analyzed_jobs if j["relevance_score"] >= auto_apply_threshold]
            manual_review_jobs = [j for j in analyzed_jobs if 30 <= j["relevance_score"] < auto_apply_threshold]
            
            workflow_stats["auto_applied"] = len(auto_apply_jobs)
            workflow_stats["manual_review"] = len(manual_review_jobs)
            
            # Step 5: Process auto-apply jobs
            if auto_apply_jobs:
                print(f"🚀 Step 5: Auto-applying to {len(auto_apply_jobs)} high-relevance jobs...")
                
                for job in auto_apply_jobs:
                    try:
                        # Generate cover letter
                        cover_result = await self.cover_letter_generator.generate_cover_letter(
                            self.username, job, self.user_data["resume_data"]
                        )
                        
                        if cover_result["success"]:
                            workflow_stats["cover_letters_generated"] += 1
                            
                            # Apply to job
                            application_result = await self.scraper.apply_to_job(
                                job, self.user_data, cover_result["file_path"]
                            )
                            
                            if application_result["success"]:
                                workflow_stats["applications_success"] += 1
                                
                                # Update Google Sheets
                                await self.sheets_tracker.log_job_application(
                                    self.username, job, cover_result["cover_letter"], "APPLIED"
                                )
                                
                                print(f"✅ Successfully applied to {job['title']} at {job['company']}")
                            else:
                                workflow_stats["applications_failed"] += 1
                                workflow_stats["errors"].append(f"Application failed: {job['title']}")
                        
                    except Exception as e:
                        workflow_stats["errors"].append(f"Auto-apply error for {job['title']}: {e}")
                        continue
            
            # Step 6: Send manual review jobs to Telegram
            if manual_review_jobs:
                print(f"📱 Step 6: Sending {len(manual_review_jobs)} jobs for manual review...")
                await self._send_manual_review_telegram(manual_review_jobs)
            
            # Step 7: NAV reporting (if applications were made)
            if workflow_stats["applications_success"] > 0:
                print("📋 Step 7: Preparing NAV reporting...")
                nav_result = await self._trigger_nav_reporting(auto_apply_jobs)
                if nav_result:
                    print("✅ NAV reporting initiated")
            
            # Step 8: Send summary to Telegram
            await self._send_workflow_summary(workflow_stats)
            
            print(f"🎉 Enhanced workflow completed for {self.username}")
            return workflow_stats
            
        except Exception as e:
            workflow_stats["errors"].append(f"Workflow error: {e}")
            await self.telegram_bot.send_message(f"❌ Workflow error for {self.username}: {e}")
            return workflow_stats
    
    def _filter_new_jobs(self, all_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter jobs to only include new ones."""
        # Simple implementation - check against saved jobs
        # In production, this would check against database
        saved_jobs_file = Path(f"~/jobbot/data/users/{self.username}/saved_jobs.json").expanduser()
        
        try:
            if saved_jobs_file.exists():
                with open(saved_jobs_file, 'r') as f:
                    saved_jobs = json.load(f)
                saved_urls = {job["url"] for job in saved_jobs}
            else:
                saved_urls = set()
            
            new_jobs = [job for job in all_jobs if job["url"] not in saved_urls]
            
            # Save all jobs (new + old)
            saved_jobs_file.parent.mkdir(parents=True, exist_ok=True)
            with open(saved_jobs_file, 'w') as f:
                json.dump(all_jobs, f, indent=2)
            
            return new_jobs
            
        except Exception as e:
            print(f"⚠️ Error filtering jobs: {e}")
            return all_jobs  # Return all if error
    
    def _get_user_skills_summary(self) -> str:
        """Get user skills summary for AI analysis."""
        try:
            resume = self.user_data["resume_data"]
            summary = resume.get("comprehensive_summary", "")
            
            skills = resume.get("comprehensive_skills", {})
            technical = ", ".join(skills.get("technical", [])[:10])
            soft = ", ".join(skills.get("soft_skills", [])[:5])
            
            return f"{summary}\n\nTechnical skills: {technical}\nSoft skills: {soft}"
            
        except Exception as e:
            print(f"⚠️ Error getting skills summary: {e}")
            return "Experienced professional"
    
    async def _send_manual_review_telegram(self, jobs: List[Dict[str, Any]]):
        """Send manual review jobs to Telegram."""
        message = f"🔍 Manual review needed for {self.username}:\n\n"
        
        for i, job in enumerate(jobs[:5], 1):  # Limit to 5 jobs
            score = job["relevance_score"]
            message += f"{i}. **{job['title']}** at {job['company']}\n"
            message += f"   Score: {score}% | {job['location']}\n"
            message += f"   {job['url'][:50]}...\n\n"
        
        if len(jobs) > 5:
            message += f"... and {len(jobs) - 5} more jobs\n"
        
        message += "Check Google Sheets for full details."
        
        await self.telegram_bot.send_message(message)
    
    async def _trigger_nav_reporting(self, applied_jobs: List[Dict[str, Any]]) -> bool:
        """Trigger NAV reporting workflow."""
        try:
            # This would trigger the BankID workflow
            nav_message = f"📋 NAV Reporting needed for {self.username}:\n"
            nav_message += f"Applied to {len(applied_jobs)} jobs today.\n"
            nav_message += "Please confirm BankID push notification to complete NAV reporting."
            
            await self.telegram_bot.send_message(nav_message)
            
            # In production, this would call working_final_frame.py
            return True
            
        except Exception as e:
            print(f"❌ NAV reporting trigger failed: {e}")
            return False
    
    async def _send_workflow_summary(self, stats: Dict[str, Any]):
        """Send workflow summary to Telegram."""
        message = f"📊 **Daily Workflow Summary - {self.username}**\n\n"
        message += f"🔍 Jobs found: {stats['total_jobs_found']}\n"
        message += f"🆕 New jobs: {stats['new_jobs']}\n"
        message += f"🤖 AI analyzed: {stats['ai_analyzed']}\n"
        message += f"✅ Auto applied: {stats['applications_success']}\n"
        message += f"📝 Cover letters: {stats['cover_letters_generated']}\n"
        message += f"👀 Manual review: {stats['manual_review']}\n"
        
        if stats["errors"]:
            message += f"\n⚠️ Errors: {len(stats['errors'])}"
        
        message += f"\n\n🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        await self.telegram_bot.send_message(message)

# API endpoint for N8N integration
async def run_enhanced_workflow_for_user(username: str) -> Dict[str, Any]:
    """API endpoint for running enhanced workflow."""
    try:
        workflow = EnhancedWorkflowIntegration(username)
        result = await workflow.run_daily_enhanced_workflow()
        return {
            "status": "success",
            "username": username,
            "stats": result
        }
    except Exception as e:
        return {
            "status": "error",
            "username": username,
            "error": str(e)
        }

if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "vitalii"
    result = asyncio.run(run_enhanced_workflow_for_user(username))
    print(json.dumps(result, indent=2))
