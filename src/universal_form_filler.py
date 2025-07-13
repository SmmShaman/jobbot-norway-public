"""Universal form filler orchestrator using AI analysis."""
import asyncio
import os
from pathlib import Path
from typing import Dict, Any
from form_navigator import FormNavigator
from form_analyzer import FormAnalyzer  
from form_filler import FormFiller

class UniversalFormFiller:
    def __init__(self, username):
        self.username = username
        self.navigator = FormNavigator()
        self.analyzer = FormAnalyzer()
        self.filler = FormFiller()
        
    async def process_job_application(self, job_data):
        """Complete end-to-end job application process."""
        try:
            job_url = job_data['url']
            job_title = job_data['title'] 
            company = job_data.get('company', 'Unknown')
            
            print(f'Processing application for: {job_title} at {company}')
            
            # Step 1: Navigate to employer application form
            print('Step 1: Navigating to employer site...')
            nav_result = await self.navigator.navigate_to_application(job_url, self.username)
            
            if not nav_result.get('success'):
                return {'error': f'Navigation failed: {nav_result.get("error")}', 'step': 'navigation'}
            
            employer_url = nav_result['employer_url']
            form_screenshot = nav_result['form_screenshot']
            html_content = nav_result['html_content']
            
            print(f'Employer site: {employer_url}')
            
            # Step 2: AI analysis of form
            print('Step 2: Analyzing form with AI...')
            analysis_result = await self.analyzer.analyze_form(
                form_screenshot, html_content, job_title, company
            )
            
            if not analysis_result.get('success'):
                return {'error': f'Form analysis failed: {analysis_result.get("error")}', 'step': 'analysis'}
            
            instructions = analysis_result['instructions']
            print(f'Found {len(instructions.get("form_fields", []))} form fields')
            
            # Step 3: Prepare user data
            print('Step 3: Preparing user data...')
            user_data = self.filler.prepare_user_data(self.username, job_data)
            
            if 'error' in user_data:
                return {'error': f'User data preparation failed: {user_data["error"]}', 'step': 'data_preparation'}
            
            # Step 4: Fill form
            print('Step 4: Filling form...')
            fill_result = await self.filler.fill_form_universally(
                employer_url, instructions, user_data, self.username
            )
            
            if not fill_result.get('success'):
                return {'error': f'Form filling failed: {fill_result.get("error")}', 'step': 'form_filling'}
            
            return {
                'success': True,
                'job_title': job_title,
                'company': company,
                'employer_url': employer_url,
                'fields_filled': fill_result['filled_fields'],
                'screenshot': fill_result['screenshot'],
                'ai_instructions': instructions
            }
            
        except Exception as e:
            return {'error': str(e), 'step': 'general'}

    async def test_with_real_job(self):
        """Test Universal Form Filler with a real job from NAV."""
        try:
            # Get a real job
            from scrapers.nav_scraper import NavScraper
            scraper = NavScraper()
            search_urls = ['https://arbeidsplassen.nav.no/stillinger?county=OSLO&v=5']
            jobs = await scraper.scrape_jobs(search_urls)
            
            if not jobs:
                return {'error': 'No jobs found for testing'}
            
            # Use first job for testing
            test_job = jobs[0]
            print(f'Testing with job: {test_job["title"]}')
            
            result = await self.process_job_application(test_job)
            return result
            
        except Exception as e:
            return {'error': str(e)}
