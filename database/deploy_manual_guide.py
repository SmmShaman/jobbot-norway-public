#!/usr/bin/env python3
"""
Deploy SQL Functions via Supabase REST API
Works without direct PostgreSQL access
"""

import os
import sys
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("⚠️  Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

def execute_sql_via_api(sql_content: str, service_key: str, project_ref: str) -> dict:
    """Execute SQL via Supabase Management API"""

    # Try method 1: Direct SQL execution via Supabase client library
    url = f"https://{project_ref}.supabase.co/rest/v1/rpc"

    # The SQL needs to be executed, but we need a way to run arbitrary SQL
    # Let's try creating the functions via the Management API

    # Actually, we need to use the Supabase client to call functions
    # But to CREATE functions, we need direct database access

    return {"error": "REST API cannot create functions, need PostgreSQL access"}

def create_manual_instructions():
    """Create simple copy-paste instructions"""
    print("=" * 70)
    print("📋 MANUAL DEPLOYMENT REQUIRED")
    print("=" * 70)
    print()
    print("psql підключення не працює з цього environment.")
    print("Будь ласка, виконай SQL функції вручну:")
    print()
    print("━" * 70)
    print("ВАРІАНТ 1: Через Supabase Dashboard (найпростіше)")
    print("━" * 70)
    print()
    print("1. Відкрий: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new")
    print()
    print("2. Скопіюй і виконай ці 3 файли ПО ЧЕРЗІ:")
    print()

    base_path = Path(__file__).parent
    files = [
        "function_1_extract_links.sql",
        "function_2_create_jobs.sql",
        "function_3_get_pending.sql"
    ]

    for i, filename in enumerate(files, 1):
        filepath = base_path / filename
        print(f"   Файл {i}: {filename}")
        print(f"   GitHub: https://github.com/SmmShaman/jobbot-norway-public/blob/claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu/database/{filename}")
        print()

    print("3. Після кожного файлу натискай 'Run' та чекай 'Success'")
    print()
    print("━" * 70)
    print("ВАРІАНТ 2: Через psql на локальному ПК")
    print("━" * 70)
    print()
    print("Якщо у тебе встановлений psql локально:")
    print()
    print("cd database")
    print('export PGPASSWORD="QWEpoi123987@"')
    print("psql 'postgresql://postgres@db.ptrmidlhfdbybxmyovtm.supabase.co:5432/postgres' \\")
    print("  -f function_1_extract_links.sql")
    print("psql 'postgresql://postgres@db.ptrmidlhfdbybxmyovtm.supabase.co:5432/postgres' \\")
    print("  -f function_2_create_jobs.sql")
    print("psql 'postgresql://postgres@db.ptrmidlhfdbybxmyovtm.supabase.co:5432/postgres' \\")
    print("  -f function_3_get_pending.sql")
    print()
    print("━" * 70)
    print("ПЕРЕВІРКА:")
    print("━" * 70)
    print()
    print("Після деплою виконай в Supabase SQL Editor:")
    print()
    print("SELECT routine_name FROM information_schema.routines")
    print("WHERE routine_schema = 'public' AND routine_name LIKE '%finn%';")
    print()
    print("Має показати 3 функції:")
    print("  - extract_finn_job_links")
    print("  - create_jobs_from_finn_links")
    print("  - get_pending_skyvern_jobs")
    print()
    print("=" * 70)

def main():
    print("🗄️  SQL Functions Deployment")
    print()

    # Check if we can access Supabase
    try:
        response = requests.get(
            "https://ptrmidlhfdbybxmyovtm.supabase.co/rest/v1/",
            timeout=5
        )
        print("✅ Supabase API доступний")
    except Exception as e:
        print(f"⚠️  Supabase API недоступний: {e}")

    print()

    # Show manual instructions
    create_manual_instructions()

if __name__ == "__main__":
    main()
