"""Configuration-based scraper that reads URLs from config file."""
import json
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import re
import sys
import os

# Add parent directory to path for imports
sys.path.append('/app')

CONFIG_FILE = Path("/app/src/config/search_config.json")

def load_config():
    """Load search configuration from JSON file."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found: {CONFIG_FILE}")
        return {}

def filter_by_keywords(text: str, keywords: list, exclude_keywords: list = None) -> bool:
    """Check if text contains desired keywords and doesn't contain excluded ones."""
    if not keywords:  # If no keywords specified, include all
        return True
        
    text_lower = text.lower()
    
    # Check if any keyword is present
    has_keyword = any(keyword.lower() in text_lower for keyword in keywords)
    
    # Check if any exclude keyword is present
    has_exclude = False
    if exclude_keywords:
        has_exclude = any(exclude.lower() in text_lower for exclude in exclude_keywords)
    
    return has_keyword and not has_exclude

def fetch_finn_jobs_config(config: dict) -> list:
    """Fetch finn.no jobs using configuration."""
    if not config.get("search_sources", {}).get("finn.no", {}).get("enabled"):
        return []
    
    finn_config = config["search_sources"]["finn.no"]
    all_jobs = []
    
    for rss_url in finn_config.get("rss_urls", []):
        try:
            print(f"Fetching from finn RSS: {rss_url}")
            response = requests.get(rss_url, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            for item in root.findall('.//item'):
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                description = item.find('description').text if item.find('description') is not None else ""
                
                # Apply keyword filtering
                full_text = f"{title} {description}"
                if filter_by_keywords(
                    full_text, 
                    finn_config.get("keywords", []), 
                    finn_config.get("exclude_keywords", [])
                ):
                    all_jobs.append({
                        'title': title,
                        'url': link,
                        'description': description,
                        'source': 'finn.no',
                        'created_at': datetime.now().isoformat()
                    })
        
        except Exception as e:
            print(f"Error fetching finn RSS {rss_url}: {e}")
    
    return all_jobs

def fetch_nav_jobs_config(config: dict) -> list:
    """Fetch nav.no jobs using configuration."""
    if not config.get("search_sources", {}).get("arbeidsplassen.nav.no", {}).get("enabled"):
        return []
    
    nav_config = config["search_sources"]["arbeidsplassen.nav.no"]
    all_jobs = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for search_url in nav_config.get("search_urls", []):
        try:
            print(f"Fetching from NAV: {search_url}")
            response = requests.get(search_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different selectors for NAV site
            job_cards = (
                soup.find_all('article', class_='job-posting-compact') or
                soup.find_all('div', attrs={'data-testid': 'job-posting'}) or
                soup.find_all('a', href=re.compile(r'/stilling/')) or
                soup.find_all('div', class_='job-item')
            )
            
            for card in job_cards:
                try:
                    # Extract title
                    title_elem = (
                        card.find('h2') or card.find('h3') or 
                        card.find('a') or card.find('span', class_='title')
                    )
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Extract link
                    link_elem = card.find('a', href=True) if card.name != 'a' else card
                    job_url = ""
                    if link_elem and link_elem.get('href'):
                        href = link_elem['href']
                        job_url = href if href.startswith('http') else f"https://arbeidsplassen.nav.no{href}"
                    
                    # Extract company
                    company_elem = (
                        card.find('span', class_='company') or 
                        card.find('div', class_='employer') or
                        card.find('p', class_='company-name')
                    )
                    company = company_elem.get_text(strip=True) if company_elem else ""
                    
                    description = f"{title} {company}"
                    
                    # Apply keyword filtering
                    if title and filter_by_keywords(
                        description, 
                        nav_config.get("keywords", []), 
                        nav_config.get("exclude_keywords", [])
                    ):
                        all_jobs.append({
                            'title': title,
                            'url': job_url,
                            'company': company,
                            'source': 'arbeidsplassen.nav.no',
                            'created_at': datetime.now().isoformat()
                        })
                
                except Exception as e:
                    print(f"Error parsing nav job card: {e}")
                    continue
        
        except Exception as e:
            print(f"Error fetching nav URL {search_url}: {e}")
    
    return all_jobs

def fetch_all_jobs_config():
    """Fetch all jobs using configuration file."""
    config = load_config()
    if not config:
        return []
    
    all_jobs = []
    
    # Fetch from finn.no
    finn_jobs = fetch_finn_jobs_config(config)
    all_jobs.extend(finn_jobs)
    print(f"✓ Found {len(finn_jobs)} relevant jobs from finn.no")
    
    # Fetch from nav.no
    nav_jobs = fetch_nav_jobs_config(config)
    all_jobs.extend(nav_jobs)
    print(f"✓ Found {len(nav_jobs)} relevant jobs from nav.no")
    
    # Remove duplicates based on URL
    unique_jobs = {}
    for job in all_jobs:
        if job.get('url') and job['url'] not in unique_jobs:
            unique_jobs[job['url']] = job
    
    return list(unique_jobs.values())

if __name__ == "__main__":
    jobs = fetch_all_jobs_config()
    print(f"Total filtered jobs: {len(jobs)}")
    
    # Save results
    output_file = "/app/data/latest_jobs.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    print(f"Saved to {output_file}")
