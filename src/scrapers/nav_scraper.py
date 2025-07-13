"""Scraper for arbeidsplassen.nav.no job listings."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json

def fetch_nav_jobs(base_url: str = "https://arbeidsplassen.nav.no/stillinger?county=INNLANDET&v=5&municipal=INNLANDET.%C3%98STRE+TOTEN&municipal=INNLANDET.VESTRE+TOTEN"):
    """Scrape jobs from arbeidsplassen.nav.no with geographic filter."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        jobs = []
        
        # NAV uses different selectors - need to inspect their HTML structure
        job_cards = soup.find_all('article', class_='job-posting-compact')
        if not job_cards:
            # Fallback selectors if structure changed
            job_cards = soup.find_all('div', attrs={'data-testid': 'job-posting'})
        
        for card in job_cards:
            try:
                title_elem = card.find('h2') or card.find('h3') or card.find('a')
                title = title_elem.get_text(strip=True) if title_elem else "No title"
                
                link_elem = card.find('a', href=True)
                job_url = ""
                if link_elem:
                    href = link_elem['href']
                    job_url = href if href.startswith('http') else f"https://arbeidsplassen.nav.no{href}"
                
                company_elem = card.find('span', class_='company') or card.find('div', class_='employer')
                company = company_elem.get_text(strip=True) if company_elem else "Unknown company"
                
                location_elem = card.find('span', class_='location')
                location = location_elem.get_text(strip=True) if location_elem else "Unknown location"
                
                jobs.append({
                    'title': title,
                    'url': job_url,
                    'company': company,
                    'location': location,
                    'source': 'arbeidsplassen.nav.no',
                    'created_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"Error parsing job card: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"Error fetching NAV jobs: {e}")
        return []

if __name__ == "__main__":
    jobs = fetch_nav_jobs()
    print(f"Found {len(jobs)} jobs from arbeidsplassen.nav.no")
    for job in jobs[:3]:
        print(f"- {job['title']} at {job['company']}")


class NavScraper:
    """NAV scraper class for arbeidsplassen.nav.no"""
    
    def __init__(self):
        self.base_url = 'https://arbeidsplassen.nav.no'
    
    async def scrape_jobs(self, search_urls):
        """Scrape jobs from NAV search URLs"""
        from playwright.async_api import async_playwright
        
        jobs = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            for url in search_urls:
                try:
                    await page.goto(url, timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Правильні селектори на базі тесту
                    job_elements = await page.query_selector_all('article, .job-item, .stilling')
                    
                    for element in job_elements:
                        try:
                            title = await element.query_selector('h2, h3, .title')
                            company = await element.query_selector('.company, .employer')
                            link = await element.query_selector('a')
                            
                            if title and link:
                                title_text = await title.inner_text()
                                company_text = await company.inner_text() if company else 'Unknown'
                                href = await link.get_attribute('href')
                                
                                if href:
                                    full_url = href if href.startswith('http') else f'{self.base_url}{href}'
                                    jobs.append({
                                        'title': title_text.strip(),
                                        'company': company_text.strip(),
                                        'url': full_url,
                                        'source': 'arbeidsplassen.nav.no'
                                    })
                        except:
                            continue
                            
                except Exception as e:
                    print(f'Error scraping {url}: {e}')
                    
            await browser.close()
        
        return jobs
