"""Multi-site scraper supporting arbeidsplassen.nav.no, finn.no, and future LinkedIn."""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from playwright.async_api import async_playwright, Page

class MultiSiteScraper:
    def __init__(self):
        self.site_configs = {
            "arbeidsplassen": {
                "base_url": "https://arbeidsplassen.nav.no",
                "job_selector": "article[data-testid='job-posting-card']",
                "title_selector": "h2 a",
                "company_selector": ".navds-body-short",
                "location_selector": "[data-testid='location']",
                "link_selector": "h2 a",
                "apply_button_text": "Gå til søknad",
                "enabled": True
            },
            "finn": {
                "base_url": "https://www.finn.no",
                "job_selector": ".ads__unit",
                "title_selector": ".ads__unit__link",
                "company_selector": ".ads__unit__content__subtitle",
                "location_selector": ".ads__unit__content__location",
                "link_selector": ".ads__unit__link",
                "apply_button_text": "Søk stilling",
                "enabled": False  # Enable when ready
            },
            "linkedin": {
                "base_url": "https://www.linkedin.com",
                "job_selector": ".job-card-container",
                "title_selector": ".job-card-list__title",
                "company_selector": ".job-card-container__company-name",
                "location_selector": ".job-card-container__metadata-item",
                "link_selector": ".job-card-list__title",
                "apply_button_text": "Easy Apply",
                "enabled": False  # Future implementation
            }
        }
    
    async def scrape_all_sites(self, user_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape all enabled sites for a user."""
        all_jobs = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Scrape arbeidsplassen.nav.no
            if user_config.get("search_sources", {}).get("arbeidsplassen.nav.no", {}).get("enabled"):
                arbeidsplassen_jobs = await self._scrape_arbeidsplassen(
                    page, user_config["search_sources"]["arbeidsplassen.nav.no"]
                )
                all_jobs.extend(arbeidsplassen_jobs)
            
            # Scrape finn.no
            if user_config.get("search_sources", {}).get("finn.no", {}).get("enabled"):
                finn_jobs = await self._scrape_finn(
                    page, user_config["search_sources"]["finn.no"]
                )
                all_jobs.extend(finn_jobs)
            
            # Future: LinkedIn scraping
            # if user_config.get("search_sources", {}).get("linkedin", {}).get("enabled"):
            #     linkedin_jobs = await self._scrape_linkedin(page, user_config["search_sources"]["linkedin"])
            #     all_jobs.extend(linkedin_jobs)
            
            await browser.close()
        
        print(f"🕷️ Scraped {len(all_jobs)} total jobs from all sites")
        return all_jobs
    
    async def _scrape_arbeidsplassen(self, page: Page, site_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape arbeidsplassen.nav.no."""
        jobs = []
        
        try:
            for search_url in site_config.get("search_urls", []):
                print(f"🔍 Scraping arbeidsplassen: {search_url}")
                
                await page.goto(search_url, wait_until="networkidle")
                await asyncio.sleep(2)
                
                # Get job cards
                job_cards = await page.query_selector_all(self.site_configs["arbeidsplassen"]["job_selector"])
                
                for card in job_cards[:20]:  # Limit to first 20 jobs
                    try:
                        job_data = await self._extract_arbeidsplassen_job(page, card)
                        if job_data:
                            job_data["source"] = "arbeidsplassen"
                            job_data["scraped_date"] = datetime.now().isoformat()
                            jobs.append(job_data)
                    except Exception as e:
                        print(f"⚠️ Error extracting arbeidsplassen job: {e}")
                        continue
                
                await asyncio.sleep(1)  # Be respectful
            
        except Exception as e:
            print(f"❌ Error scraping arbeidsplassen: {e}")
        
        return jobs
    
    async def _extract_arbeidsplassen_job(self, page: Page, card) -> Optional[Dict[str, Any]]:
        """Extract job data from arbeidsplassen job card."""
        try:
            # Get title and link
            title_element = await card.query_selector(self.site_configs["arbeidsplassen"]["title_selector"])
            if not title_element:
                return None
            
            title = await title_element.inner_text()
            link = await title_element.get_attribute("href")
            if link and not link.startswith("http"):
                link = f"https://arbeidsplassen.nav.no{link}"
            
            # Get company
            company_element = await card.query_selector(self.site_configs["arbeidsplassen"]["company_selector"])
            company = await company_element.inner_text() if company_element else ""
            
            # Get location
            location_element = await card.query_selector(self.site_configs["arbeidsplassen"]["location_selector"])
            location = await location_element.inner_text() if location_element else ""
            
            # Get job description by visiting the job page
            description = await self._get_job_description(page, link)
            
            return {
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "url": link,
                "description": description,
                "site": "arbeidsplassen.nav.no"
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting arbeidsplassen job data: {e}")
            return None
    
    async def _scrape_finn(self, page: Page, site_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape finn.no (future implementation)."""
        jobs = []
        
        try:
            for search_url in site_config.get("search_urls", []):
                print(f"🔍 Scraping finn.no: {search_url}")
                
                await page.goto(search_url, wait_until="networkidle")
                await asyncio.sleep(2)
                
                # Finn.no implementation will be added here
                # Similar structure to arbeidsplassen but with finn-specific selectors
                
        except Exception as e:
            print(f"❌ Error scraping finn.no: {e}")
        
        return jobs
    
    async def _get_job_description(self, page: Page, job_url: str) -> str:
        """Get full job description from job page."""
        try:
            # Create new page for job details
            job_page = await page.context.new_page()
            await job_page.goto(job_url, wait_until="networkidle")
            await asyncio.sleep(1)
            
            # Try different selectors for job description
            description_selectors = [
                "[data-testid='job-posting-text']",
                ".job-description",
                ".job-posting-text",
                "main article",
                ".content"
            ]
            
            description = ""
            for selector in description_selectors:
                try:
                    element = await job_page.query_selector(selector)
                    if element:
                        description = await element.inner_text()
                        break
                except:
                    continue
            
            await job_page.close()
            return description[:2000]  # Limit description length
            
        except Exception as e:
            print(f"⚠️ Could not get job description for {job_url}: {e}")
            return ""
    
    async def apply_to_job(self, job_data: Dict[str, Any], user_data: Dict[str, Any], 
                          cover_letter_path: str) -> Dict[str, Any]:
        """Apply to a job using the universal form filler."""
        try:
            from .ai_form_analyzer import AIFormAnalyzer
            from .universal_form_filler import UniversalFormFiller
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)  # Visible for debugging
                page = await browser.new_page()
                
                # Navigate to job page
                await page.goto(job_data["url"], wait_until="networkidle")
                
                # Look for apply button
                apply_button_text = self._get_apply_button_text(job_data["source"])
                apply_button = await page.query_selector(f"text={apply_button_text}")
                
                if not apply_button:
                    # Try alternative selectors
                    apply_selectors = [
                        "a:has-text('Søk')", "a:has-text('Apply')", 
                        "button:has-text('Søk')", "[href*='apply']"
                    ]
                    for selector in apply_selectors:
                        apply_button = await page.query_selector(selector)
                        if apply_button:
                            break
                
                if not apply_button:
                    return {"success": False, "error": "Apply button not found"}
                
                # Click apply button
                await apply_button.click()
                await page.wait_for_load_state("networkidle")
                
                # Take screenshot for AI analysis
                screenshot_path = f"/tmp/form_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                
                # Get page HTML
                html_content = await page.content()
                
                # Analyze form with AI
                analyzer = AIFormAnalyzer()
                form_analysis = await analyzer.analyze_application_form(
                    screenshot_path, html_content, 
                    job_data["title"], job_data["company"]
                )
                
                # Fill form
                filler = UniversalFormFiller(user_data)
                fill_success = await filler.fill_application_form(
                    page, form_analysis, cover_letter_path
                )
                
                if fill_success:
                    # Submit form
                    submit_success = await filler.submit_form(page, form_analysis)
                    
                    if submit_success:
                        print(f"✅ Successfully applied to {job_data['title']} at {job_data['company']}")
                        return {"success": True, "message": "Application submitted"}
                    else:
                        return {"success": False, "error": "Form submission failed"}
                else:
                    return {"success": False, "error": "Form filling failed"}
                
                await browser.close()
                
        except Exception as e:
            print(f"❌ Application process failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_apply_button_text(self, source: str) -> str:
        """Get apply button text for specific site."""
        return self.site_configs.get(source, {}).get("apply_button_text", "Apply")
    
    def add_site_config(self, site_name: str, config: Dict[str, Any]):
        """Add configuration for new site."""
        self.site_configs[site_name] = config
        print(f"✅ Added site configuration for {site_name}")
    
    def enable_site(self, site_name: str, enabled: bool = True):
        """Enable or disable site scraping."""
        if site_name in self.site_configs:
            self.site_configs[site_name]["enabled"] = enabled
            print(f"✅ {'Enabled' if enabled else 'Disabled'} {site_name} scraping")

if __name__ == "__main__":
    scraper = MultiSiteScraper()
    print("✅ Multi-Site Scraper created")
    print(f"📊 Configured sites: {list(scraper.site_configs.keys())}")
    print(f"🔛 Enabled sites: {[name for name, config in scraper.site_configs.items() if config.get('enabled')]}")
