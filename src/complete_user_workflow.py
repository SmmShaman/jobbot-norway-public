"""Complete user workflow with automatic applications."""
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

from .user_specific_workflow import UserSpecificWorkflow
from .nav_auto_apply import NAVAutoApplicator
from .multi_user_system import MultiUserJobSystem

class CompleteUserWorkflow(UserSpecificWorkflow):
    def __init__(self, username: str):
        super().__init__(username)
        
    async def run_complete_workflow_with_applications(self):
        """Run complete workflow including automatic applications."""
        print(f"🚀 Starting COMPLETE workflow for: {self.username}")
        print("=" * 60)
        
        try:
            # Step 1: Find relevant jobs (existing functionality)
            config = self.system.get_user_config(self.username)
            user_profile = self.get_user_unified_profile()
            
            nav_config = config.get("search_sources", {}).get("arbeidsplassen.nav.no", {})
            search_urls = nav_config.get("search_urls", [])
            min_relevance = config.get("user_profile", {}).get("min_relevance_score", 30)
            auto_apply_threshold = config.get("application_settings", {}).get("auto_apply_threshold", 85)
            
            print(f"👤 User: {self.username}")
            print(f"🎯 Auto-apply threshold: {auto_apply_threshold}%")
            print(f"📊 Min relevance: {min_relevance}%")
            
            # Find jobs using existing workflow
            from .playwright_job_analyzer import PlaywrightJobAnalyzer
            analyzer = PlaywrightJobAnalyzer()
            all_relevant_jobs = []
            
            for search_url in search_urls[:1]:  # Test with first URL
                relevant_jobs = await analyzer.analyze_jobs_with_playwright(
                    search_url, user_profile, min_relevance
                )
                all_relevant_jobs.extend(relevant_jobs)
            
            print(f"\n🎯 Found {len(all_relevant_jobs)} relevant jobs")
            
            if not all_relevant_jobs:
                print("📭 No relevant jobs found.")
                return
            
            # Step 2: Categorize jobs for application
            auto_apply_jobs = []
            manual_approval_jobs = []
            
            for job in all_relevant_jobs:
                relevance_score = job.get('relevance_score', 0)
                if relevance_score >= auto_apply_threshold:
                    auto_apply_jobs.append(job)
                else:
                    manual_approval_jobs.append(job)
            
            print(f"🤖 Auto-apply jobs: {len(auto_apply_jobs)}")
            print(f"📱 Manual approval jobs: {len(manual_approval_jobs)}")
            
            # Step 3: Auto-apply to high-relevance jobs
            if auto_apply_jobs:
                print(f"\n🚀 Starting automatic applications...")
                
                applicator = NAVAutoApplicator(config)
                await applicator.initialize_browser()
                
                try:
                    # Login to NAV
                    login_success = await applicator.login_to_nav()
                    
                    if login_success:
                        for i, job in enumerate(auto_apply_jobs, 1):
                            print(f"\n📝 Auto-applying {i}/{len(auto_apply_jobs)}")
                            
                            result = await applicator.apply_to_job(job)
                            
                            print(f"📊 Result: {result['status']} - {result['message']}")
                            
                            # Add result to job data
                            job['application_result'] = result
                            
                            # Wait between applications
                            if i < len(auto_apply_jobs):
                                await asyncio.sleep(10)  # 10 second delay
                    else:
                        print("❌ Could not login to NAV. Manual applications required.")
                        
                finally:
                    await applicator.close_browser()
            
            # Step 4: Send Telegram notifications for manual approval
            if manual_approval_jobs:
                print(f"\n📱 Sending Telegram requests for {len(manual_approval_jobs)} jobs...")
                # Add Telegram integration here
            
            # Step 5: Summary
            print("\n" + "=" * 60)
            print("📋 COMPLETE WORKFLOW SUMMARY:")
            print(f"  • Total relevant jobs: {len(all_relevant_jobs)}")
            print(f"  • Auto-applied: {len(auto_apply_jobs)}")
            print(f"  • Manual approval: {len(manual_approval_jobs)}")
            
            if auto_apply_jobs:
                print(f"\n🤖 AUTO-APPLICATIONS:")
                for job in auto_apply_jobs:
                    result = job.get('application_result', {})
                    status = result.get('status', 'UNKNOWN')
                    title = job.get('title', 'Unknown')[:50]
                    print(f"  • {title}: {status}")
            
            print(f"\n✅ Complete workflow finished for {self.username}")
            
        except Exception as e:
            print(f"❌ Complete workflow error: {e}")

async def run_complete_user_workflow(username: str):
    """Run complete workflow for user."""
    workflow = CompleteUserWorkflow(username)
    await workflow.run_complete_workflow_with_applications()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        username = sys.argv[1]
        asyncio.run(run_complete_user_workflow(username))
    else:
        print("Usage: python -m src.complete_user_workflow <username>")
