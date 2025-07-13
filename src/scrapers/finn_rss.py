"""RSS scraper for finn.no job listings."""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sqlite3
from pathlib import Path

def fetch_new_jobs():
    """Fetch new jobs from finn.no RSS feed."""
    rss_url = "https://www.finn.no/job/fulltime/search.rss?location=0.20001"
    
    try:
        response = requests.get(rss_url, timeout=30)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        jobs = []
        
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else "No title"
            link = item.find('link').text if item.find('link') is not None else ""
            description = item.find('description').text if item.find('description') is not None else ""
            
            jobs.append({
                'title': title,
                'url': link,
                'description': description,
                'source': 'finn.no',
                'created_at': datetime.now().isoformat()
            })
        
        return jobs
    except Exception as e:
        print(f"Error fetching RSS: {e}")
        return []

if __name__ == "__main__":
    jobs = fetch_new_jobs()
    print(f"Found {len(jobs)} jobs from finn.no RSS")
    for job in jobs[:3]:  # Show first 3
        print(f"- {job['title']}")
