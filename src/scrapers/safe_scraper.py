"""Safe scraper with anti-detection measures."""
import json
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import time
import random
from urllib.robotparser import RobotFileParser
import sys

CONFIG_FILE = Path("/app/src/config/search_config.json")

class SafeScraper:
    def __init__(self):
        self.session = requests.Session()
        # Rotate User-Agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def check_robots_txt(self, base_url: str) -> bool:
        """Check if scraping is allowed by robots.txt"""
        try:
            rp = RobotFileParser()
            rp.set_url(f"{base_url}/robots.txt")
            rp.read()
            return rp.can_fetch('*', base_url)
        except:
            return True  # If can't check, assume allowed
    
    def safe_request(self, url: str, delay_range=(1, 3)) -> requests.Response:
        """Make request with random delay and rotating user agent."""
        # Random delay between requests
        time.sleep(random.uniform(*delay_range))
        
        # Random user agent
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = self.session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response
    
    def fetch_finn_rss(self, rss_urls: list, keywords: list, exclude_keywords: list) -> list:
        """Safely fetch from finn.no RSS (low risk)."""
        jobs = []
        
        for rss_url in rss_urls:
            try:
                print(f"Fetching finn RSS: {rss_url}")
                response = self.safe_request(rss_url, delay_range=(0.5, 1.5))  # Shorter delay for RSS
                
                root = ET.fromstring(response.content)
                
                for item in root.findall('.//item'):
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    description = item.find('description').text if item.find('description') is not None else ""
                    
                    full_text = f"{title} {description}".lower()
                    
                    # Keyword filtering
                    has_keyword = any(kw.lower() in full_text for kw in keywords) if keywords else True
                    has_exclude = any(ex.lower() in full_text for ex in exclude_keywords) if exclude_keywords else False
                    
                    if has_keyword and not has_exclude:
                        jobs.append({
                            'title': title,
                            'url': link,
                            'description': description,
                            'source': 'finn.no',
                            'created_at': datetime.now().isoformat()
                        })
                
            except Exception as e:
                print(f"Error fetching finn RSS: {e}")
        
        return jobs
    
    def fetch_nav_carefully(self, search_urls: list, keywords: list, exclude_keywords: list) -> list:
        """Carefully fetch from NAV (higher risk)."""
        jobs = []
        
        # Check robots.txt first
        if not self.check_robots_txt("https://arbeidsplassen.nav.no"):
            print("❌ NAV robots.txt disallows scraping")
            return []
        
        for url in search_urls:
            try:
                print(f"Carefully fetching NAV: {url}")
                response = self.safe_request(url, delay_range=(2, 5))  # Longer delays
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find job listings with various selectors
                job_elements = (
                    soup.find_all('a', href=lambda x: x and '/stilling/' in x) or
                    soup.find_all('article') or
                    soup.find_all('div', class_=lambda x: x and 'job' in x.lower())
                )
                
                for element in job_elements[:20]:  # Limit to first 20 to avoid overload
                    try:
                        title = element.get_text(strip=True)[:100]  # Limit length
                        href = element.get('href') if element.name == 'a' else element.find('a', href=True)
                        
                        if href:
                            job_url = href if href.startswith('http') else f"https://arbeidsplassen.nav.no{href}"
                            
                            # Simple keyword check
                            if keywords:
                                has_keyword = any(kw.lower() in title.lower() for kw in keywords)
                                if not has_keyword:
                                    continue
                            
                            if exclude_keywords:
                                has_exclude = any(ex.lower() in title.lower() for ex in exclude_keywords)
                                if has_exclude:
                                    continue
                            
                            jobs.append({
                                'title': title,
                                'url': job_url,
                                'source': 'arbeidsplassen.nav.no',
                                'created_at': datetime.now().isoformat()
                            })
                    
                    except Exception as e:
                        continue
                
                # Extra delay after each URL
                time.sleep(random.uniform(3, 6))
                
            except Exception as e:
                print(f"Error fetching NAV: {e}")
        
        return jobs

def safe_fetch_all():
    """Main function with safety measures."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        print("❌ Cannot load config")
        return []
    
    scraper = SafeScraper()
    all_jobs = []
    
    # Finn.no (RSS - safe)
    if config.get("search_sources", {}).get("finn.no", {}).get("enabled"):
        finn_config = config["search_sources"]["finn.no"]
        finn_jobs = scraper.fetch_finn_rss(
            finn_config.get("rss_urls", []),
            finn_config.get("keywords", []),
            finn_config.get("exclude_keywords", [])
        )
        all_jobs.extend(finn_jobs)
        print(f"✅ Finn.no: {len(finn_jobs)} jobs")
    
    # NAV.no (HTML - risky, with precautions)
    if config.get("search_sources", {}).get("arbeidsplassen.nav.no", {}).get("enabled"):
        nav_config = config["search_sources"]["arbeidsplassen.nav.no"]
        nav_jobs = scraper.fetch_nav_carefully(
            nav_config.get("search_urls", []),
            nav_config.get("keywords", []),
            nav_config.get("exclude_keywords", [])
        )
        all_jobs.extend(nav_jobs)
        print(f"✅ NAV.no: {len(nav_jobs)} jobs")
    
    # Remove duplicates
    unique_jobs = {job['url']: job for job in all_jobs if job.get('url')}
    
    return list(unique_jobs.values())

if __name__ == "__main__":
    jobs = safe_fetch_all()
    print(f"📊 Total unique jobs: {len(jobs)}")
    
    with open("/app/data/latest_jobs.json", 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
