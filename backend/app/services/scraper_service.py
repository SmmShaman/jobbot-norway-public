"""Job scraper service for NAV and FINN websites"""
import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Any
from uuid import uuid4
from app.services.database import DatabaseService
from app.services.ai_service import AIService


class ScraperService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.db = DatabaseService()
        self.ai = AIService()

    def get_job_links_from_nav_search(self, search_url: str) -> List[str]:
        """Extract all job links from NAV search results page."""
        try:
            print(f"🔍 Fetching NAV job links from: {search_url}")
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

            unique_urls = list(set(full_urls))  # Remove duplicates
            print(f"✅ Found {len(unique_urls)} unique job links from NAV")
            return unique_urls

        except Exception as e:
            print(f"❌ Error fetching NAV job links: {e}")
            return []

    def get_job_links_from_finn_search(self, search_url: str) -> List[str]:
        """Extract all job links from FINN search results page."""
        try:
            print(f"🔍 Fetching FINN job links from: {search_url}")
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all job links - FINN specific
            job_links = soup.find_all('a', href=lambda x: x and '/job/fulltime/ad.html' in x)

            # Convert to full URLs
            full_urls = []
            for link in job_links:
                href = link.get('href')
                if href.startswith('http'):
                    full_urls.append(href)
                else:
                    full_urls.append(f"https://www.finn.no{href}")

            unique_urls = list(set(full_urls))
            print(f"✅ Found {len(unique_urls)} unique job links from FINN")
            return unique_urls

        except Exception as e:
            print(f"❌ Error fetching FINN job links: {e}")
            return []

    def fetch_nav_job_details(self, job_url: str) -> Dict[str, Any]:
        """Fetch full job description from NAV job page."""
        try:
            print(f"📖 Fetching NAV job details: {job_url}")

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
            title_elem = soup.find('h1') or soup.find('h2') or soup.find('title')
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
            location_elem = soup.find(string=lambda x: x and any(
                word in x.lower() for word in ['oslo', 'bergen', 'trondheim', 'stavanger', 'drammen', 'toten', 'innlandet']
            ))
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

            print(f"✅ Extracted NAV job: {title[:50]}...")
            return job_data

        except Exception as e:
            print(f"❌ Error fetching NAV job {job_url}: {e}")
            return {
                'url': job_url,
                'title': 'Error fetching',
                'company': '',
                'description': '',
                'location': '',
                'source': 'arbeidsplassen.nav.no',
                'error': str(e)
            }

    def fetch_finn_job_details(self, job_url: str) -> Dict[str, Any]:
        """Fetch full job description from FINN job page."""
        try:
            print(f"📖 Fetching FINN job details: {job_url}")

            # Random delay to avoid being blocked
            time.sleep(random.uniform(2, 4))

            response = self.session.get(job_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract job details - FINN specific selectors
            title = ""
            company = ""
            description = ""
            location = ""

            # Title
            title_elem = soup.find('h1', class_='u-t3') or soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Company
            company_elem = soup.find('div', class_='panel') or soup.find('p', class_='u-caption')
            if company_elem:
                company = company_elem.get_text(strip=True)

            # Description
            desc_elem = soup.find('div', class_='import-decoration') or soup.find('div', id='job-description')
            if desc_elem:
                description = desc_elem.get_text(strip=True)[:3000]

            # Location
            location_elem = soup.find('span', class_='u-capitalize')
            if location_elem:
                location = location_elem.get_text(strip=True)

            job_data = {
                'url': job_url,
                'title': title,
                'company': company,
                'description': description,
                'location': location,
                'source': 'finn.no'
            }

            print(f"✅ Extracted FINN job: {title[:50]}...")
            return job_data

        except Exception as e:
            print(f"❌ Error fetching FINN job {job_url}: {e}")
            return {
                'url': job_url,
                'title': 'Error fetching',
                'company': '',
                'description': '',
                'location': '',
                'source': 'finn.no',
                'error': str(e)
            }

    async def scan_and_analyze_jobs(
        self,
        user_id: str,
        nav_urls: List[str],
        finn_urls: List[str],
        user_profile: Dict[str, Any],
        min_relevance: int = 70
    ) -> Dict[str, Any]:
        """
        Complete job scanning and analysis pipeline.

        Args:
            user_id: User ID
            nav_urls: List of NAV search URLs
            finn_urls: List of FINN search URLs
            user_profile: User profile with skills and preferences
            min_relevance: Minimum relevance score threshold

        Returns:
            Dictionary with statistics about discovered and analyzed jobs
        """
        print(f"🚀 Starting job scan for user {user_id}")

        all_job_urls = []

        # Step 1: Collect all job URLs from search pages
        for nav_url in nav_urls:
            urls = self.get_job_links_from_nav_search(nav_url)
            all_job_urls.extend([(url, 'nav') for url in urls])

        for finn_url in finn_urls:
            urls = self.get_job_links_from_finn_search(finn_url)
            all_job_urls.extend([(url, 'finn') for url in urls])

        print(f"📊 Total unique jobs found: {len(all_job_urls)}")

        # Step 2: Check which jobs are already in database
        existing_jobs = await self.db.get_jobs(user_id)
        existing_urls = {job['url'] for job in existing_jobs}

        new_jobs = [job for job in all_job_urls if job[0] not in existing_urls]
        print(f"🆕 New jobs to analyze: {len(new_jobs)}")

        # Step 3: Fetch and analyze each new job
        analyzed_count = 0
        relevant_count = 0

        for job_url, source in new_jobs[:20]:  # Limit to 20 jobs per scan
            print(f"\n--- Analyzing job {analyzed_count + 1}/{min(len(new_jobs), 20)} ---")

            # Fetch job details based on source
            if source == 'nav':
                job_data = self.fetch_nav_job_details(job_url)
            else:
                job_data = self.fetch_finn_job_details(job_url)

            if not job_data.get('description') or job_data.get('error'):
                print("⚠️ No valid job data, skipping...")
                continue

            # AI analysis
            try:
                analysis = await self.ai.analyze_job_relevance(
                    job_data['title'],
                    job_data['description'],
                    job_data['company'],
                    job_data['location'],
                    user_profile
                )

                relevance_score = analysis.get('relevance_score', 0)
                print(f"🤖 AI Score: {relevance_score}% - {analysis.get('recommendation', 'UNKNOWN')}")

                # Save job to database
                job_entry = {
                    'id': str(uuid4()),
                    'user_id': user_id,
                    'url': job_data['url'],
                    'title': job_data['title'],
                    'company': job_data['company'],
                    'location': job_data['location'],
                    'description': job_data['description'],
                    'source': job_data['source'],
                    'relevance_score': relevance_score,
                    'ai_analysis': analysis,
                    'status': 'ANALYZED' if relevance_score >= min_relevance else 'NEW'
                }

                await self.db.create_job(job_entry)
                analyzed_count += 1

                if relevance_score >= min_relevance:
                    relevant_count += 1
                    print(f"✅ Relevant job saved!")
                else:
                    print(f"⏭️ Job below threshold ({min_relevance}%), marked as NEW")

            except Exception as e:
                print(f"❌ AI analysis failed: {e}")
                await self.db.log_monitoring_event(user_id, 'ANALYSIS_ERROR', {'error': str(e), 'url': job_url})

        # Log scan completion
        await self.db.log_monitoring_event(
            user_id,
            'SCAN_COMPLETED',
            {
                'total_found': len(all_job_urls),
                'new_jobs': len(new_jobs),
                'analyzed': analyzed_count,
                'relevant': relevant_count
            }
        )

        print(f"\n🎯 Scan complete: {analyzed_count} analyzed, {relevant_count} relevant jobs")

        return {
            'total_found': len(all_job_urls),
            'new_jobs': len(new_jobs),
            'analyzed': analyzed_count,
            'relevant': relevant_count
        }
