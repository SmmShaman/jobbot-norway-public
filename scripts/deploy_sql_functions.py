#!/usr/bin/env python3
"""
Deploy SQL functions to Supabase
"""

import os
import sys
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    print("ERROR: supabase package not installed!")
    print("Install it: pip install supabase")
    sys.exit(1)

# Get credentials from environment
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing environment variables!")
    print("Required:")
    print("  - SUPABASE_URL")
    print("  - SUPABASE_SERVICE_KEY")
    print()
    print("Current env:")
    print(f"  SUPABASE_URL: {SUPABASE_URL or 'NOT SET'}")
    print(f"  SUPABASE_SERVICE_KEY: {'SET' if SUPABASE_SERVICE_KEY else 'NOT SET'}")
    sys.exit(1)

# Read SQL file
sql_file = Path(__file__).parent.parent / 'database' / 'finn_link_extractor_function.sql'

if not sql_file.exists():
    print(f"❌ SQL file not found: {sql_file}")
    sys.exit(1)

print(f"📄 Reading SQL from: {sql_file}")
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

print(f"✅ Loaded {len(sql_content)} characters of SQL")

# Connect to Supabase
print(f"🔌 Connecting to Supabase: {SUPABASE_URL}")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Execute SQL using RPC or direct query
# Note: Supabase Python client doesn't have direct SQL execution
# We need to use the REST API directly

import requests

print("🚀 Executing SQL functions...")

# Supabase REST API endpoint for raw SQL
headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

# Split SQL into individual statements
sql_statements = sql_content.split('-- ============================================================')

success_count = 0
error_count = 0

print(f"📊 Found {len(sql_statements)} SQL sections")

# Try to execute via psql if available, otherwise inform user
try:
    # Check if we can use psql
    import subprocess

    # Create temporary SQL file
    temp_sql = Path('/tmp/supabase_functions.sql')
    with open(temp_sql, 'w', encoding='utf-8') as f:
        f.write(sql_content)

    print("⚠️  Note: Supabase Python SDK doesn't support raw SQL execution.")
    print("📝 SQL file is ready at:", sql_file)
    print()
    print("✅ Please execute it manually:")
    print(f"   1. Go to: https://supabase.com/dashboard/project/YOUR_PROJECT_ID/sql/new")
    print(f"   2. Copy and paste the content from: {sql_file}")
    print(f"   3. Click 'Run' to execute")
    print()
    print("Or use psql:")
    print(f"   cat {sql_file} | psql 'YOUR_SUPABASE_CONNECTION_STRING'")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print()
print("💡 Alternative: The SQL functions are ready in the file.")
print("   You can execute them via Supabase Dashboard SQL Editor.")
