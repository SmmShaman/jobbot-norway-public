#!/usr/bin/env python3
"""
Test FINN.no link extraction locally
This script fetches a FINN.no search page and extracts job links using regex
"""

import requests
import re
from typing import List, Dict

def fetch_finn_search_html(url: str) -> str:
    """Fetch HTML from FINN.no search page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print(f"🌐 Fetching: {url}")
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    print(f"✅ Fetched {len(response.text)} bytes")
    return response.text

def extract_finn_job_links(html_content: str) -> List[Dict[str, str]]:
    """Extract job links with finnkode from HTML"""
    # Pattern to match FINN.no job URLs with finnkode
    pattern = r'href="(https?://[^"]*finnkode=\d+)"'

    matches = re.findall(pattern, html_content, re.IGNORECASE)

    jobs = []
    seen_codes = set()

    for url in matches:
        # Extract finnkode from URL
        code_match = re.search(r'finnkode=(\d+)', url)

        if code_match:
            finnkode = code_match.group(1)

            # Skip duplicates
            if finnkode in seen_codes:
                continue

            seen_codes.add(finnkode)

            # Ensure absolute URL
            if not url.startswith('http'):
                url = 'https://www.finn.no' + (url if url.startswith('/') else '/' + url)

            jobs.append({
                'url': url,
                'finnkode': finnkode,
                'title': f'Job {finnkode}'
            })

    return jobs

def main():
    """Test extraction with provided FINN.no search URL"""

    # User's filtered search URL
    test_url = (
        "https://www.finn.no/job/search?"
        "location=2.20001.22034.20097&"
        "location=2.20001.22034.20098&"
        "location=2.20001.22034.20085&"
        "published=1"
    )

    print("=" * 60)
    print("🧪 Testing FINN.no Link Extraction")
    print("=" * 60)

    try:
        # Fetch HTML
        html = fetch_finn_search_html(test_url)

        # Extract links
        print(f"\n🔍 Extracting job links...")
        jobs = extract_finn_job_links(html)

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

        # Next steps
        print("\n📋 Next Steps:")
        print("1. Install SQL functions in Supabase (see INSTALL_SQL_NOW.md)")
        print("2. These jobs will be created in database with skyvern_status='PENDING'")
        print("3. Worker v2 will then process each job individually with Skyvern")
        print("4. Jobs page will show them appearing in real-time!")

        return jobs

    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        print("\n💡 If you're running this from a restricted environment,")
        print("   you can test with saved HTML instead.")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == '__main__':
    jobs = main()
