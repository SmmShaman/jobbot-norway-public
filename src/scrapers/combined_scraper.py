"""Combined scraper for both finn.no and arbeidsplassen.nav.no."""
import sys
import os
sys.path.append('/app')

from .finn_rss import fetch_new_jobs as fetch_finn_jobs
from .nav_scraper import fetch_nav_jobs
from datetime import datetime
import json

def fetch_all_jobs():
    """Fetch jobs from all configured sources."""
    all_jobs = []
    
    print("Fetching jobs from finn.no...")
    finn_jobs = fetch_finn_jobs()
    all_jobs.extend(finn_jobs)
    print(f"✓ Found {len(finn_jobs)} jobs from finn.no")
    
    print("Fetching jobs from arbeidsplassen.nav.no...")
    nav_jobs = fetch_nav_jobs()
    all_jobs.extend(nav_jobs)
    print(f"✓ Found {len(nav_jobs)} jobs from nav.no")
    
    # Remove duplicates based on URL
    unique_jobs = {}
    for job in all_jobs:
        if job['url'] and job['url'] not in unique_jobs:
            unique_jobs[job['url']] = job
    
    final_jobs = list(unique_jobs.values())
    print(f"Total unique jobs: {len(final_jobs)}")
    
    return final_jobs

if __name__ == "__main__":
    jobs = fetch_all_jobs()
    
    # Save to file for n8n to process
    output_file = "/app/data/latest_jobs.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(jobs)} jobs to {output_file}")
