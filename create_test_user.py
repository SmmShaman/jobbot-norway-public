#!/usr/bin/env python3
"""
Create test user in Supabase
"""
from supabase import create_client

SUPABASE_URL = "https://ptrmidlhfdbybxmyovtm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0cm1pZGxoZmRieWJ4bXlvdnRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjQzNDc0OSwiZXhwIjoyMDc4MDEwNzQ5fQ.46uj0VMvxoWvApNTDdifgpfkbDv5fBhU3GfUjIGIwtU"

def create_test_user():
    """Create test user via Supabase Admin API"""
    print("🔐 Creating test user...")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # Create user using admin API
        response = supabase.auth.admin.create_user({
            "email": "test@jobbot.no",
            "password": "Test123456",
            "email_confirm": True,
            "user_metadata": {
                "full_name": "Test User"
            }
        })

        print("✅ Test user created successfully!")
        print()
        print("=" * 60)
        print("📧 Email: test@jobbot.no")
        print("🔑 Password: Test123456")
        print("=" * 60)
        print()
        print("🌐 Login at your Netlify URL")
        print()

        return True

    except Exception as e:
        if "already registered" in str(e).lower():
            print("✅ User already exists!")
            print()
            print("=" * 60)
            print("📧 Email: test@jobbot.no")
            print("🔑 Password: Test123456")
            print("=" * 60)
            print()
            return True
        else:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    create_test_user()
