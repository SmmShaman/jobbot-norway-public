#!/usr/bin/env python3
"""
Deploy SQL Functions to Supabase
Automatically creates the required SQL functions in Supabase database
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client

def load_sql_file(file_path: str) -> str:
    """Load SQL content from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql(supabase: Client, sql_content: str, function_name: str) -> bool:
    """Execute SQL via Supabase RPC"""
    try:
        print(f"📤 Executing: {function_name}")

        # Use Supabase's query method to execute raw SQL
        # Note: This requires a custom RPC function or direct PostgreSQL access
        result = supabase.rpc('exec_sql', {'query': sql_content}).execute()

        print(f"✅ Success: {function_name}")
        return True

    except Exception as e:
        print(f"❌ Error executing {function_name}: {str(e)}")
        print(f"   SQL preview: {sql_content[:200]}...")
        return False

def main():
    """Main deployment script"""
    print("=" * 60)
    print("🚀 Deploying SQL Functions to Supabase")
    print("=" * 60)
    print()

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ ERROR: Missing environment variables!")
        print("   Required: SUPABASE_URL, SUPABASE_SERVICE_KEY")
        print()
        print("   Make sure /home/stuard/jobbot-norway-public/worker/.env is configured")
        sys.exit(1)

    print(f"🔗 Supabase URL: {supabase_url}")
    print()

    # Initialize Supabase client
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)

    # Define SQL files to deploy (in order)
    base_path = Path(__file__).parent
    sql_files = [
        (base_path / "function_1_extract_links.sql", "extract_finn_job_links()"),
        (base_path / "function_2_create_jobs.sql", "create_jobs_from_finn_links()"),
        (base_path / "function_3_get_pending.sql", "get_pending_skyvern_jobs()"),
    ]

    # Execute each SQL file
    success_count = 0
    for sql_file, function_name in sql_files:
        if not sql_file.exists():
            print(f"⚠️ File not found: {sql_file}")
            continue

        print(f"📄 Loading: {sql_file.name}")
        sql_content = load_sql_file(str(sql_file))

        if execute_sql(supabase, sql_content, function_name):
            success_count += 1

        print()

    # Summary
    print("=" * 60)
    if success_count == len(sql_files):
        print(f"✅ SUCCESS! All {success_count} functions deployed")
        print()
        print("📋 Deployed functions:")
        print("  1. extract_finn_job_links(html_content TEXT)")
        print("  2. create_jobs_from_finn_links(user_id, scan_task_id, html_content)")
        print("  3. get_pending_skyvern_jobs(user_id, limit)")
        print()
        print("🔄 Worker can now extract jobs from FINN.no!")
    else:
        print(f"⚠️ Partial success: {success_count}/{len(sql_files)} functions deployed")
        print()
        print("⚠️ ALTERNATIVE DEPLOYMENT METHOD:")
        print()
        print("Since Supabase client may not support direct SQL execution,")
        print("you can deploy manually in Supabase Dashboard:")
        print()
        print("1. Open: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new")
        print()
        print("2. Copy and run each file in order:")
        for sql_file, function_name in sql_files:
            print(f"   - {sql_file.name} → Creates {function_name}")
        print()
        print("3. Each file should show 'Success. No rows returned'")

    print("=" * 60)

if __name__ == "__main__":
    main()
