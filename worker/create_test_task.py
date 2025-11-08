#!/usr/bin/env python3
"""
Test script to create a scan task in Supabase
This will test the Worker + Skyvern + Azure OpenAI integration
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from supabase import create_client, Client
except ImportError:
    print("ERROR: supabase package not installed!")
    print("Install it: pip install supabase")
    sys.exit(1)


def create_test_task():
    """Create a test scan task in Supabase"""

    # Get credentials from environment
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        print("\nSet them first:")
        print("  export SUPABASE_URL='https://...'")
        print("  export SUPABASE_SERVICE_KEY='...'")
        sys.exit(1)

    # Initialize Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)

    # Test task data - Oslo IT jobs on FINN.no
    task_data = {
        'source': 'FINN',
        'url': 'https://www.finn.no/job/search?location=2.20001.22034.20097&occupation=0.23.19',  # Oslo IT jobs
        'user_id': 'test-user-001',  # Test user ID
        'status': 'PENDING',
        'created_at': datetime.utcnow().isoformat(),
        'max_retries': 3,
        'retry_count': 0
    }

    print("\n" + "="*60)
    print("🧪 Creating TEST scan task")
    print("="*60)
    print(f"📍 Source: {task_data['source']}")
    print(f"🔗 URL: {task_data['url'][:60]}...")
    print(f"👤 User: {task_data['user_id']}")
    print("="*60 + "\n")

    try:
        # Insert task
        result = supabase.table('scan_tasks').insert(task_data).execute()

        if result.data:
            task = result.data[0]
            print("✅ TEST TASK CREATED SUCCESSFULLY!")
            print(f"\n📋 Task ID: {task['id']}")
            print(f"📊 Status: {task['status']}")
            print(f"🔗 URL: {task['url'][:60]}...")
            print("\n🎯 The Worker should pick up this task within 10 seconds!")
            print("\n📝 Monitor Worker logs to see:")
            print("   - Task being processed")
            print("   - Skyvern API calls")
            print("   - Azure OpenAI LLM requests")
            print("   - Jobs being extracted and saved")
            print("\n💡 Check logs: tail -f worker/worker.log")
            print("\n" + "="*60)
            return task
        else:
            print("❌ Failed to create task - no data returned")
            return None

    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return None


if __name__ == '__main__':
    create_test_task()
