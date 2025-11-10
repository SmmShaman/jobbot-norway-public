#!/usr/bin/env python3
"""
Deploy SQL Functions directly to Supabase
Uses psycopg2 for direct PostgreSQL connection
"""

import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("⚠️  psycopg2 not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

def deploy_function(cursor, sql_file: Path, function_name: str):
    """Deploy a single SQL function"""
    print(f"\n📤 Deploying: {function_name}")
    print(f"   File: {sql_file.name}")

    # Read SQL content
    sql_content = sql_file.read_text(encoding='utf-8')

    # Execute SQL
    try:
        cursor.execute(sql_content)
        print(f"✅ Success: {function_name}")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main deployment function"""
    print("=" * 70)
    print("🗄️  Deploying SQL Functions to Supabase")
    print("=" * 70)

    # Database credentials
    DB_HOST = "db.ptrmidlhfdbybxmyovtm.supabase.co"
    DB_PORT = 5432
    DB_NAME = "postgres"
    DB_USER = "postgres"
    DB_PASS = "QWEpoi123987@"

    # SQL files to deploy
    base_path = Path(__file__).parent
    sql_files = [
        (base_path / "function_1_extract_links.sql", "extract_finn_job_links()"),
        (base_path / "function_2_create_jobs.sql", "create_jobs_from_finn_links()"),
        (base_path / "function_3_get_pending.sql", "get_pending_skyvern_jobs()"),
    ]

    # Connect to database
    print(f"\n🔗 Connecting to: {DB_HOST}")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=10
        )
        cursor = conn.cursor()
        print("✅ Connected to Supabase PostgreSQL")
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   1. Check if database password is correct")
        print("   2. Check if IP is whitelisted in Supabase settings")
        print("   3. Check network connectivity")
        sys.exit(1)

    # Deploy each function
    success_count = 0
    for sql_file, function_name in sql_files:
        if not sql_file.exists():
            print(f"⚠️  File not found: {sql_file}")
            continue

        if deploy_function(cursor, sql_file, function_name):
            success_count += 1

        # Commit after each function
        conn.commit()

    # Verify deployment
    print("\n" + "=" * 70)
    print("🔍 Verifying deployed functions...")
    print("=" * 70)

    cursor.execute("""
        SELECT routine_name, routine_type
        FROM information_schema.routines
        WHERE routine_schema = 'public'
          AND routine_name IN (
            'extract_finn_job_links',
            'create_jobs_from_finn_links',
            'get_pending_skyvern_jobs'
          )
        ORDER BY routine_name;
    """)

    functions = cursor.fetchall()
    print(f"\n📋 Found {len(functions)} functions:")
    for func_name, func_type in functions:
        print(f"   ✅ {func_name} ({func_type})")

    # Close connection
    cursor.close()
    conn.close()

    # Summary
    print("\n" + "=" * 70)
    if success_count == len(sql_files) and len(functions) == 3:
        print("✅ DEPLOYMENT SUCCESSFUL!")
        print("=" * 70)
        print("\n📋 All functions deployed:")
        print("  1. ✅ extract_finn_job_links(html_content TEXT)")
        print("  2. ✅ create_jobs_from_finn_links(user_id, scan_task_id, html_content)")
        print("  3. ✅ get_pending_skyvern_jobs(user_id, limit)")
        print("\n🔄 Worker can now extract jobs from FINN.no!")
        print("\n📊 Next step: Restart worker")
        print("   sudo systemctl restart worker_v2")
        print("=" * 70)
        return 0
    else:
        print(f"⚠️  PARTIAL SUCCESS: {success_count}/{len(sql_files)} functions deployed")
        print(f"   Found {len(functions)}/3 functions in database")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
