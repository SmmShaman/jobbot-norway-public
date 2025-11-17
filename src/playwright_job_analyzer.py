"""Working Playwright job analyzer with proper timeouts."""
import asyncio
from playwright.async_api import async_playwright
from typing import List, Dict, Any
from .ai_analyzer import analyze_job_relevance

class PlaywrightJobAnalyzer:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def initialize_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def get_job_links_from_search_page(self, search_url: str) -> List[str]:
        try:
            print(f"🔍 Opening search page: {search_url}")
            await self.page.goto(search_url, wait_until='domcontentloaded', timeout=45000)
            await self.page.wait_for_timeout(5000)
            await self.page.wait_for_selector('a[href*="/stilling/"]', timeout=15000)
            
            job_links = await self.page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="/stilling/"]'));
                    return links.map(link => link.href);
                }
            """)
            
            unique_links = list(set(job_links))
            print(f"✅ Found {len(unique_links)} unique job links")
            return unique_links
            
        except Exception as e:
            print(f"❌ Error getting job links: {e}")
            return []

    async def fetch_full_job_description_with_click(self, job_url: str) -> Dict[str, Any]:
        try:
            print(f"🖱️ Navigating to: {job_url}")
            
            # Use the working approach from simple_test
            await self.page.goto(job_url, wait_until='domcontentloaded', timeout=45000)
            await self.page.wait_for_timeout(15000)  # Wait 15 seconds like in test
            
            # Extract data using simple approach that worked
            job_data = await self.page.evaluate("""
                () => {
                    const title = document.title.replace(' - arbeidsplassen.no', '');
                    const mainElement = document.querySelector('main');
                    const main_text = mainElement ? mainElement.textContent : '';
                    
                    // Try to find company in the main content
                    let company = 'Unknown Company';
                    if (main_text.includes('Arbeidsgiver')) {
                        const lines = main_text.split('\\n');
                        for (let i = 0; i < lines.length; i++) {
                            if (lines[i].includes('Arbeidsgiver') && i + 1 < lines.length) {
                                company = lines[i + 1].trim();
                                break;
                            }
                        }
                    }
                    
                    return {
                        title: title,
                        company: company,
                        description: main_text.substring(0, 4000),
                        url: window.location.href
                    };
                }
            """)
            
            job_data['source'] = 'arbeidsplassen.nav.no'
            job_data['location'] = 'Norway'
            
            print(f"✅ Extracted: {job_data['title'][:50]}... ({len(job_data['description'])} chars)")
            return job_data
            
        except Exception as e:
            print(f"❌ Error fetching job {job_url}: {e}")
            return {'url': job_url, 'title': 'Error', 'company': '', 'description': '', 'location': '', 'source': 'nav'}

    async def analyze_jobs_with_playwright(self, search_url: str, full_resume: str, min_relevance: int = 10) -> List[Dict[str, Any]]:
        await self.initialize_browser()
        
        try:
            print(f"🚀 Starting Working Playwright analysis for: {search_url}")
            
            job_links = await self.get_job_links_from_search_page(search_url)
            if not job_links:
                return []
            
            relevant_jobs = []
            
            # Test with first 3 jobs
            for i, job_url in enumerate(job_links[:3]):
                print(f"\n--- Working Playwright Analysis {i+1}/{len(job_links[:3])} ---")
                
                job_data = await self.fetch_full_job_description_with_click(job_url)
                
                if len(job_data['description']) < 100:
                    print(f"⚠️ Insufficient description: {len(job_data['description'])} chars")
                    continue
                
                # AI analysis with full resume
                try:
                    analysis = analyze_job_relevance(
                        job_data['title'],
                        job_data['description'],
                        full_resume
                    )
                    
                    relevance_score = analysis.get('relevance_score', 0)
                    job_data['relevance_score'] = relevance_score
                    job_data['ai_analysis'] = analysis
                    
                    print(f"🤖 AI Score: {relevance_score}% - {analysis.get('recommendation', 'UNKNOWN')}")
                    
                    if relevance_score >= min_relevance:
                        relevant_jobs.append(job_data)
                        print(f"✅ Relevant job found!")
                    else:
                        print(f"⏭️ Below threshold ({min_relevance}%)")
                        
                except Exception as e:
                    print(f"❌ AI analysis error: {e}")
            
            return relevant_jobs
            
        finally:
            await self.close_browser()

async def run_playwright_analysis():
    analyzer = PlaywrightJobAnalyzer()
    search_url = "https://arbeidsplassen.nav.no/stillinger?county=INNLANDET&v=5&municipal=INNLANDET.%C3%98STRE+TOTEN&municipal=INNLANDET.VESTRE+TOTEN"
    
    full_resume = "Experienced professional seeking new opportunities. Background in customer service, administration, logistics, and basic technical skills. Open to various positions including warehouse work, retail, office administration, and entry-level technical roles. Hardworking, reliable, and eager to learn new skills. Fluent in Norwegian and English."
    
    results = await analyzer.analyze_jobs_with_playwright(search_url, full_resume, min_relevance=10)
    print(f"📊 Final Working Results: {len(results)} relevant jobs")
    
    for job in results:
        print(f"🎯 {job['title']}: {job['relevance_score']}% - {job.get('ai_analysis', {}).get('recommendation', 'UNKNOWN')}")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_playwright_analysis())
