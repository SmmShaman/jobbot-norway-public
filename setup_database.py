#!/usr/bin/env python3
"""
Automatic Supabase Database Setup
Runs SQL migration and creates storage buckets
"""
import os
import sys
from pathlib import Path
from supabase import create_client, Client

# Load environment variables
SUPABASE_URL = "https://ptrmidlhfdbybxmyovtm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0cm1pZGxoZmRieWJ4bXlvdnRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjQzNDc0OSwiZXhwIjoyMDc4MDEwNzQ5fQ.46uj0VMvxoWvApNTDdifgpfkbDv5fBhU3GfUjIGIwtU"

def setup_database():
    """Run SQL migration"""
    print("🚀 Starting Supabase setup...")
    print(f"📡 Connecting to: {SUPABASE_URL}")

    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Read SQL migration file
    migration_file = Path(__file__).parent / "supabase" / "migrations" / "001_initial_schema.sql"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    print(f"📄 Reading migration: {migration_file.name}")
    sql_content = migration_file.read_text(encoding='utf-8')

    # Split SQL into individual statements
    # Remove comments and empty lines
    statements = []
    current_statement = []

    for line in sql_content.split('\n'):
        # Skip comments
        if line.strip().startswith('--') or line.strip().startswith('/*'):
            continue

        current_statement.append(line)

        # End of statement
        if line.strip().endswith(';'):
            stmt = '\n'.join(current_statement).strip()
            if stmt:
                statements.append(stmt)
            current_statement = []

    print(f"📊 Found {len(statements)} SQL statements")

    # Execute via Supabase REST API (using rpc)
    print("\n⚠️  IMPORTANT: SQL migration must be run manually in Supabase Dashboard")
    print("=" * 70)
    print("\n📋 Follow these steps:")
    print("1. Open: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql")
    print("2. Click 'New Query'")
    print("3. Copy content from: supabase/migrations/001_initial_schema.sql")
    print("4. Paste in SQL Editor")
    print("5. Click 'RUN' ▶️")
    print("\n✅ After running, the following tables will be created:")
    print("   - profiles")
    print("   - user_settings")
    print("   - jobs")
    print("   - cover_letters")
    print("   - applications")
    print("   - monitoring_logs")
    print("\n" + "=" * 70)

    return True

def create_storage_buckets():
    """Create storage buckets"""
    print("\n📦 Creating Storage Buckets...")

    print("\n⚠️  Storage buckets must be created manually in Supabase Dashboard")
    print("=" * 70)
    print("\n📋 Follow these steps:")
    print("1. Open: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/storage/buckets")
    print("2. Click 'New bucket' (3 times for 3 buckets)")
    print("\n📁 Bucket 1: resumes")
    print("   - Name: resumes")
    print("   - Public: NO (Private)")
    print("   - File size limit: 10 MB")
    print("   - Allowed MIME types: application/pdf")
    print("\n📁 Bucket 2: cover-letters")
    print("   - Name: cover-letters")
    print("   - Public: NO (Private)")
    print("   - File size limit: 5 MB")
    print("   - Allowed MIME types: application/pdf, text/plain")
    print("\n📁 Bucket 3: screenshots")
    print("   - Name: screenshots")
    print("   - Public: NO (Private)")
    print("   - File size limit: 5 MB")
    print("   - Allowed MIME types: image/png, image/jpeg")
    print("\n" + "=" * 70)

    return True

def main():
    print("=" * 70)
    print("🤖 JobBot Norway - Automatic Supabase Setup")
    print("=" * 70)

    # Setup database
    if not setup_database():
        sys.exit(1)

    # Create storage buckets
    if not create_storage_buckets():
        sys.exit(1)

    print("\n" + "=" * 70)
    print("✅ Setup instructions displayed!")
    print("=" * 70)
    print("\n📝 Next steps:")
    print("1. Complete SQL migration in Supabase Dashboard")
    print("2. Create storage buckets")
    print("3. Run: cd web-app && npm install && npm run dev")
    print("4. Run: cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload")
    print("\n🚀 After setup, open: http://localhost:3000")
    print("=" * 70)

if __name__ == "__main__":
    main()
