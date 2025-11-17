"""User-specific workflow using their analyzed profile."""
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

from .playwright_job_analyzer import PlaywrightJobAnalyzer
from .multi_user_system import MultiUserJobSystem

class UserSpecificWorkflow:
    def __init__(self, username: str):
        self.username = username
        self.system = MultiUserJobSystem()
        self.user_dir = Path(f"/app/data/users/{username}")
        
    def get_user_unified_profile(self) -> str:
        """Get user's unified AI-analyzed profile."""
        config = self.system.get_user_config(self.username)
        if not config:
            raise Exception(f"Config not found for {self.username}")
        
        unified_resume = config.get('user_profile', {}).get('unified_resume')
        if not unified_resume:
            raise Exception(f"No AI profile found for {self.username}. Run: analyze {self.username}")
        
        # Extract comprehensive profile for job matching
        profile_data = unified_resume.get('unified_profile', {})
        
        # Build comprehensive profile text
        profile_parts = []
        
        # Personal info
        personal = profile_data.get('personal_info', {})
        if personal.get('name'):
            profile_parts.append(f"Name: {personal['name']}")
        
        # Professional summary
        summary = profile_data.get('comprehensive_summary', '')
        if summary:
            profile_parts.append(f"Professional Summary: {summary}")
        
        # Experience
        experience_years = profile_data.get('total_experience_years', 0)
        profile_parts.append(f"Total Experience: {experience_years} years")
        
        # Work experience
        work_exp = profile_data.get('all_work_experience', [])
        if work_exp:
            profile_parts.append("Work Experience:")
            for exp in work_exp[:3]:  # Top 3 experiences
                company = exp.get('company', 'Unknown')
                position = exp.get('position', 'Unknown')
                duration = exp.get('duration', 'Unknown')
                profile_parts.append(f"- {position} at {company} ({duration})")
        
        # Skills
        skills = profile_data.get('comprehensive_skills', {})
        all_skills = []
        all_skills.extend(skills.get('technical', []))
        all_skills.extend(skills.get('soft_skills', []))
        all_skills.extend(skills.get('industry_knowledge', []))
        all_skills.extend(skills.get('languages', []))
        
        if all_skills:
            profile_parts.append(f"Skills: {', '.join(all_skills[:15])}")  # Top 15 skills
        
        # Career preferences
        career_prefs = profile_data.get('career_preferences', '')
        if career_prefs:
            profile_parts.append(f"Career Goals: {career_prefs}")
        
        # Key strengths
        strengths = profile_data.get('key_strengths', [])
        if strengths:
            profile_parts.append(f"Key Strengths: {', '.join(strengths)}")
        
        return '\n'.join(profile_parts)

    async def run_user_workflow(self):
        """Run workflow for specific user."""
        print(f"🚀 Starting workflow for user: {self.username}")
        print("=" * 50)
        
        try:
            # Get user config
            config = self.system.get_user_config(self.username)
            if not config:
                print(f"❌ No config found for {self.username}")
                return
            
            # Get unified profile
            user_profile = self.get_user_unified_profile()
            print(f"👤 User Profile loaded ({len(user_profile)} chars)")
            
            # Get search configuration
            nav_config = config.get("search_sources", {}).get("arbeidsplassen.nav.no", {})
            search_urls = nav_config.get("search_urls", [])
            min_relevance = config.get("user_profile", {}).get("min_relevance_score", 30)
            
            print(f"🔍 Will search {len(search_urls)} URLs with min relevance {min_relevance}%")
            
            # Run Playwright analysis
            analyzer = PlaywrightJobAnalyzer()
            all_relevant_jobs = []
            
            for i, search_url in enumerate(search_urls[:1], 1):  # Test with first URL
                print(f"\n📊 Processing URL {i}/{len(search_urls[:1])}")
                print(f"🔗 {search_url}")
                
                relevant_jobs = await analyzer.analyze_jobs_with_playwright(
                    search_url, user_profile, min_relevance
                )
                all_relevant_jobs.extend(relevant_jobs)
                
                print(f"✅ Found {len(relevant_jobs)} relevant jobs from this URL")
            
            print(f"\n🎯 TOTAL RELEVANT JOBS: {len(all_relevant_jobs)}")
            
            if all_relevant_jobs:
                print("\n📋 RELEVANT JOBS FOUND:")
                for i, job in enumerate(all_relevant_jobs, 1):
                    score = job.get('relevance_score', 0)
                    title = job.get('title', 'Unknown')
                    company = job.get('company', 'Unknown')
                    recommendation = job.get('ai_analysis', {}).get('recommendation', 'UNKNOWN')
                    
                    print(f"{i}. {title}")
                    print(f"   🏢 {company}")
                    print(f"   📊 {score}% relevance - {recommendation}")
                    print(f"   🔗 {job.get('url', '')}")
                    print()
            else:
                print("📭 No relevant jobs found.")
            
            print("=" * 50)
            print(f"✅ Workflow completed for {self.username}")
            
        except Exception as e:
            print(f"❌ Workflow error for {self.username}: {e}")

async def run_user_workflow(username: str):
    """Run workflow for specific user."""
    workflow = UserSpecificWorkflow(username)
    await workflow.run_user_workflow()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        username = sys.argv[1]
        asyncio.run(run_user_workflow(username))
    else:
        print("Usage: python -m src.user_specific_workflow <username>")
