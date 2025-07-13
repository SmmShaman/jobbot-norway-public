"""Deep job analysis - fetch full job descriptions and analyze relevance."""
import requests
from bs4 import BeautifulSoup
import time
import random
from pathlib import Path
import json
from typing import List, Dict, Any
from .ai_analyzer import analyze_job_relevance

class DeepJobAnalyzer:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_job_links_from_search_page(self, search_url: str) -> List[str]:
        """Extract all job links from search results page."""
        try:
            print(f"🔍 Fetching job links from: {search_url}")
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all job links - NAV specific
            job_links = soup.find_all('a', href=lambda x: x and '/stilling/' in x)
            
            # Convert to full URLs
            full_urls = []
            for link in job_links:
                href = link.get('href')
                if href.startswith('http'):
                    full_urls.append(href)
                else:
                    full_urls.append(f"https://arbeidsplassen.nav.no{href}")
            
            print(f"✅ Found {len(full_urls)} job links")
            return list(set(full_urls))  # Remove duplicates
            
        except Exception as e:
            print(f"❌ Error fetching job links: {e}")
            return []
    
    def fetch_full_job_description(self, job_url: str) -> Dict[str, Any]:
        """Fetch full job description from individual job page."""
        try:
            print(f"📖 Fetching job details: {job_url}")
            
            # Random delay to avoid being blocked
            time.sleep(random.uniform(2, 4))
            
            response = self.session.get(job_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job details - NAV specific selectors
            title = ""
            company = ""
            description = ""
            location = ""
            
            # Title
            title_elem = (
                soup.find('h1') or 
                soup.find('h2') or
                soup.find('title')
            )
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Company
            company_elem = (
                soup.find('span', class_='company') or
                soup.find('div', class_='employer') or
                soup.find(string=lambda x: x and 'arbeidsgiver' in x.lower())
            )
            if company_elem:
                if hasattr(company_elem, 'get_text'):
                    company = company_elem.get_text(strip=True)
                else:
                    company = str(company_elem).strip()
            
            # Description - look for main content
            desc_elements = (
                soup.find_all('div', class_=lambda x: x and ('description' in x.lower() or 'content' in x.lower())) or
                soup.find_all('section') or
                soup.find_all('div', class_=lambda x: x and 'job' in x.lower()) or
                soup.find_all('p')
            )
            
            description_parts = []
            for elem in desc_elements:
                text = elem.get_text(strip=True)
                if len(text) > 50:  # Only meaningful text blocks
                    description_parts.append(text)
            
            description = " ".join(description_parts)[:3000]  # Limit length
            
            # Location
            location_elem = soup.find(string=lambda x: x and any(word in x.lower() for word in ['oslo', 'bergen', 'toten', 'innlandet']))
            if location_elem:
                location = str(location_elem).strip()
            
            job_data = {
                'url': job_url,
                'title': title,
                'company': company,
                'description': description,
                'location': location,
                'source': 'arbeidsplassen.nav.no'
            }
            
            print(f"✅ Extracted: {title[:50]}...")
            return job_data
            
        except Exception as e:
            print(f"❌ Error fetching job {job_url}: {e}")
            return {
                'url': job_url,
                'title': 'Error fetching',
                'company': '',
                'description': '',
                'location': '',
                'source': 'arbeidsplassen.nav.no'
            }
    
    def analyze_jobs_from_search_url(self, search_url: str, user_skills: str, min_relevance: int = 70) -> List[Dict[str, Any]]:
        """Complete analysis pipeline for jobs from search URL."""
        print(f"🚀 Starting deep analysis for: {search_url}")
        
        # Step 1: Get all job links
        job_links = self.get_job_links_from_search_page(search_url)
        if not job_links:
            print("❌ No job links found")
            return []
        
        # Step 2: Analyze each job
        relevant_jobs = []
        
        for i, job_url in enumerate(job_links[:10]):  # Limit to first 10 for testing
            print(f"\n--- Analyzing job {i+1}/{len(job_links[:10])} ---")
            
            # Fetch full job description
            job_data = self.fetch_full_job_description(job_url)
            
            if not job_data['description']:
                print("⚠️ No description found, skipping...")
                continue
            
            # AI analysis
            try:
                analysis = analyze_job_relevance(
                    job_data['title'],
                    job_data['description'],
                    user_skills
                )
                
                relevance_score = analysis.get('relevance_score', 0)
                job_data['relevance_score'] = relevance_score
                job_data['ai_analysis'] = analysis
                
                print(f"🤖 AI Score: {relevance_score}% - {analysis.get('recommendation', 'UNKNOWN')}")
                
                # Add to relevant jobs if meets threshold
                if relevance_score >= min_relevance:
                    relevant_jobs.append(job_data)
                    print(f"✅ Job added to relevant list!")
                else:
                    print(f"⏭️ Job below threshold ({min_relevance}%), skipping")
                
            except Exception as e:
                print(f"❌ AI analysis failed: {e}")
                job_data['relevance_score'] = 0
                job_data['ai_analysis'] = {'error': str(e)}
        
        print(f"\n🎯 Analysis complete: {len(relevant_jobs)} relevant jobs found")
        return relevant_jobs

if __name__ == "__main__":
    # Test the analyzer
    analyzer = DeepJobAnalyzer()
    
    search_url = "https://arbeidsplassen.nav.no/stillinger?county=INNLANDET&v=5&municipal=INNLANDET.%C3%98STRE+TOTEN&municipal=INNLANDET.VESTRE+TOTEN"
    user_skills = "Python, FastAPI, SQL, Docker, JavaScript, React"
    
    relevant_jobs = analyzer.analyze_jobs_from_search_url(search_url, user_skills, min_relevance=30)
    
    print(f"\n📊 Results: {len(relevant_jobs)} relevant jobs")
    for job in relevant_jobs:
        print(f"- {job['title']} ({job['relevance_score']}%)")
