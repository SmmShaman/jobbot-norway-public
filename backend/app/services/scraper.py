"""Job scraper service for extracting job postings from various sources."""
import asyncio
import random
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup


class JobScraper:
    """Service for scraping job postings from Norwegian job boards."""

    def __init__(self, timeout: int = 30):
        """Initialize job scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/120.0.0.0 Safari/537.36'
        }

    async def _random_delay(self, min_sec: float = 2, max_sec: float = 4):
        """Add random delay to avoid rate limiting.

        Args:
            min_sec: Minimum delay in seconds
            max_sec: Maximum delay in seconds
        """
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def get_job_links_from_nav(self, search_url: str) -> List[str]:
        """Extract job links from NAV search results page.

        Args:
            search_url: NAV search results URL

        Returns:
            List of job posting URLs
        """
        try:
            print(f"🔍 Fetching job links from: {search_url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(search_url, headers=self.headers)
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

            # Remove duplicates
            unique_urls = list(set(full_urls))
            print(f"✅ Found {len(unique_urls)} unique job links")
            return unique_urls

        except Exception as e:
            print(f"❌ Error fetching job links: {e}")
            return []

    async def fetch_job_details_nav(self, job_url: str) -> Dict[str, Any]:
        """Fetch full job description from NAV job page.

        Args:
            job_url: URL of the job posting

        Returns:
            Dictionary with job details
        """
        try:
            print(f"📖 Fetching job details: {job_url}")

            # Random delay to avoid being blocked
            await self._random_delay()

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(job_url, headers=self.headers)
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
                soup.find_all('div', class_=lambda x: x and (
                    'description' in x.lower() or 'content' in x.lower()
                )) or
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
            location_elem = soup.find(
                string=lambda x: x and any(
                    word in x.lower()
                    for word in ['oslo', 'bergen', 'toten', 'innlandet', 'trondheim']
                )
            )
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
                'source': 'arbeidsplassen.nav.no',
                'error': str(e)
            }

    async def scrape_finn_no(self, search_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Scrape job postings from finn.no.

        Args:
            search_url: FINN.no search URL
            limit: Maximum number of jobs to scrape

        Returns:
            List of job postings
        """
        # TODO: Implement FINN.no scraping
        print("⚠️ FINN.no scraping not yet implemented")
        return []

    async def scrape_nav_no(
        self,
        search_url: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Scrape job postings from NAV.no.

        Args:
            search_url: NAV search URL
            limit: Maximum number of jobs to scrape

        Returns:
            List of job postings
        """
        print(f"🚀 Starting NAV.no scraping: {search_url}")

        # Get all job links
        job_links = await self.get_job_links_from_nav(search_url)

        if not job_links:
            print("❌ No job links found")
            return []

        # Limit the number of jobs to scrape
        job_links = job_links[:limit]

        # Fetch details for each job concurrently
        jobs = []
        for i, job_url in enumerate(job_links):
            print(f"\n--- Scraping job {i+1}/{len(job_links)} ---")
            job_data = await self.fetch_job_details_nav(job_url)

            if job_data.get('description'):
                jobs.append(job_data)
            else:
                print("⚠️ No description found, skipping...")

        print(f"\n🎯 Scraping complete: {len(jobs)} jobs extracted")
        return jobs

    async def scrape_multiple_sources(
        self,
        sources: List[Dict[str, str]],
        limit_per_source: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape jobs from multiple sources concurrently.

        Args:
            sources: List of source dicts with 'name' and 'url' keys
            limit_per_source: Max jobs per source

        Returns:
            Dictionary mapping source names to job lists
        """
        tasks = []
        source_names = []

        for source in sources:
            source_name = source['name']
            source_url = source['url']

            if 'arbeidsplassen.nav.no' in source_url:
                task = self.scrape_nav_no(source_url, limit=limit_per_source)
                tasks.append(task)
                source_names.append(source_name)
            elif 'finn.no' in source_url:
                task = self.scrape_finn_no(source_url, limit=limit_per_source)
                tasks.append(task)
                source_names.append(source_name)

        # Run all scraping tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Organize results by source
        organized_results = {}
        for source_name, result in zip(source_names, results):
            if isinstance(result, Exception):
                print(f"❌ Error scraping {source_name}: {result}")
                organized_results[source_name] = []
            else:
                organized_results[source_name] = result

        return organized_results
