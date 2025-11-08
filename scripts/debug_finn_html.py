#!/usr/bin/env python3
"""
Debug FINN.no HTML structure to understand how job links are formatted
"""

import requests
import re

def fetch_and_analyze():
    url = (
        "https://www.finn.no/job/search?"
        "location=2.20001.22034.20097&"
        "location=2.20001.22034.20098&"
        "location=2.20001.22034.20085&"
        "published=1"
    )

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print("🌐 Fetching FINN.no search page...")
    response = requests.get(url, headers=headers, timeout=30)
    html = response.text

    print(f"✅ Fetched {len(html)} characters\n")

    # Look for different patterns
    patterns = {
        'finnkode in href': r'href="[^"]*finnkode=\d+[^"]*"',
        'finnkode anywhere': r'finnkode=\d+',
        'job/fulltime links': r'href="[^"]*job/fulltime[^"]*"',
        'job/parttime links': r'href="[^"]*job/parttime[^"]*"',
        'data-finnkode': r'data-finnkode="?\d+"?',
        '/job/ links': r'href="(/job/[^"]*)"',
    }

    print("🔍 Searching for patterns:\n")

    for name, pattern in patterns.items():
        matches = re.findall(pattern, html, re.IGNORECASE)
        unique_matches = list(set(matches))[:5]  # Show first 5 unique matches

        print(f"📌 {name}:")
        print(f"   Found: {len(matches)} matches ({len(set(matches))} unique)")

        if unique_matches:
            print("   Sample matches:")
            for match in unique_matches:
                print(f"     - {match[:100]}...")
        print()

    # Check if it's a SPA (React/Vue)
    print("🔍 Checking for JavaScript frameworks:")
    if 'react' in html.lower() or '__NEXT_DATA__' in html:
        print("   ⚠️ Detected React/Next.js - page likely loads content via JavaScript")
    elif 'vue' in html.lower():
        print("   ⚠️ Detected Vue.js - page likely loads content via JavaScript")
    else:
        print("   ✅ No obvious SPA framework detected")
    print()

    # Save sample HTML for inspection
    sample_file = '/home/user/jobbot-norway-public/scripts/finn_sample.html'
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write(html[:50000])  # Save first 50KB

    print(f"💾 Saved first 50KB of HTML to: {sample_file}")
    print("   You can inspect it to understand the structure\n")

if __name__ == '__main__':
    fetch_and_analyze()
