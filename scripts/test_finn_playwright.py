#!/usr/bin/env python3
"""
Test FINN.no link extraction using Playwright
FINN.no is a React/Next.js SPA, so we need browser automation to render JavaScript
"""

from playwright.sync_api import sync_playwright
import re
from typing import List, Dict
import time

def extract_finn_jobs_with_playwright(url: str) -> List[Dict[str, str]]:
    """Extract job links using Playwright to render JavaScript"""

    print(f"🌐 Launching browser for: {url}")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()

        try:
            # Navigate to search page
            print("📄 Loading page...")
            page.goto(url, wait_until='networkidle', timeout=30000)

            # Wait for job listings to load
            print("⏳ Waiting for job listings to appear...")
            try:
                # Wait for job cards or links to appear
                page.wait_for_selector('a[href*="finnkode"]', timeout=10000)
                print("✅ Job listings loaded!")
            except:
                print("⚠️ No job listings found with finnkode links")

            # Get page HTML after JavaScript execution
            html = page.content()

            # Extract all links with finnkode
            pattern = r'href="([^"]*finnkode=\d+[^"]*)"'
            matches = re.findall(pattern, html, re.IGNORECASE)

            jobs = []
            seen_codes = set()

            for url_match in matches:
                # Decode HTML entities
                url_match = url_match.replace('&amp;', '&')

                # Extract finnkode
                code_match = re.search(r'finnkode=(\d+)', url_match)

                if code_match:
                    finnkode = code_match.group(1)

                    # Skip duplicates
                    if finnkode in seen_codes:
                        continue

                    seen_codes.add(finnkode)

                    # Ensure absolute URL
                    if not url_match.startswith('http'):
                        if url_match.startswith('/'):
                            url_match = 'https://www.finn.no' + url_match
                        else:
                            url_match = 'https://www.finn.no/' + url_match

                    jobs.append({
                        'url': url_match,
                        'finnkode': finnkode,
                        'title': f'Job {finnkode}'
                    })

            # Also try to extract job titles if available
            print("\n📝 Attempting to extract job titles...")
            job_cards = page.query_selector_all('[data-testid*="result"], article, .job-item')

            if job_cards:
                print(f"Found {len(job_cards)} job card elements")
                for card in job_cards[:5]:  # Sample first 5
                    try:
                        title_elem = card.query_selector('h2, h3, .title, [class*="title"]')
                        link_elem = card.query_selector('a[href*="finnkode"]')

                        if title_elem and link_elem:
                            title = title_elem.inner_text().strip()
                            href = link_elem.get_attribute('href')
                            print(f"  - {title[:60]}...")
                            print(f"    {href}")
                    except:
                        continue

            browser.close()
            return jobs

        except Exception as e:
            print(f"❌ Error: {e}")
            browser.close()
            return []

def main():
    """Test Playwright extraction with provided FINN.no search URL"""

    # User's filtered search URL
    test_url = (
        "https://www.finn.no/job/search?"
        "location=2.20001.22034.20097&"
        "location=2.20001.22034.20098&"
        "location=2.20001.22034.20085&"
        "published=1"
    )

    print("=" * 60)
    print("🧪 Testing FINN.no Link Extraction with Playwright")
    print("=" * 60)

    try:
        # Extract links
        jobs = extract_finn_jobs_with_playwright(test_url)

        # Display results
        print(f"\n✅ Found {len(jobs)} unique job links:\n")

        for i, job in enumerate(jobs, 1):
            print(f"{i}. finnkode={job['finnkode']}")
            print(f"   URL: {job['url']}")
            print()

        # Summary
        print("=" * 60)
        print(f"📊 Summary:")
        print(f"   - Total jobs found: {len(jobs)}")
        print(f"   - Search URL: {test_url}")
        print("=" * 60)

        if jobs:
            print("\n✅ SUCCESS! Playwright successfully extracted job links!")
            print("\n📋 Next Steps:")
            print("1. Install SQL functions in Supabase (see INSTALL_SQL_NOW.md)")
            print("2. Update Worker v2 to use Playwright instead of requests")
            print("3. These jobs will be created with skyvern_status='PENDING'")
            print("4. Jobs page will show them appearing in real-time!")
        else:
            print("\n⚠️ No jobs found. Possible reasons:")
            print("   - No jobs matching these location filters")
            print("   - FINN.no structure changed")
            print("   - Need to adjust selectors")

        return jobs

    except ImportError:
        print("❌ Playwright not installed!")
        print("\n💡 Install with:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == '__main__':
    jobs = main()
