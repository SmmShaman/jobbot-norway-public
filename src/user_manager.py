"""CLI for managing multiple users."""
import sys
from datetime import datetime
from .multi_user_system import MultiUserJobSystem

def create_new_user():
    """Interactive user creation."""
    system = MultiUserJobSystem()
    
    print("🆕 СТВОРЕННЯ НОВОГО КОРИСТУВАЧА")
    print("=" * 40)
    
    username = input("👤 Username (login): ").strip().lower()
    if not username:
        print("❌ Username is required!")
        return
    
    if username in system.get_user_list():
        print(f"❌ User {username} already exists!")
        return
    
    full_name = input("📝 Full name: ").strip()
    email = input("📧 Email: ").strip()
    phone = input("📱 Phone: ").strip()
    fnr = input("🆔 Norwegian FNR: ").strip()
    
    print("\n📍 Preferred locations (comma separated):")
    locations_input = input("   (e.g. Oslo, Bergen, Trondheim): ").strip()
    preferred_locations = [loc.strip() for loc in locations_input.split(',') if loc.strip()]
    
    print("\n🔍 Search URLs (comma separated):")
    print("   Examples:")
    print("   - Oslo: https://arbeidsplassen.nav.no/stillinger?county=OSLO&v=5")
    print("   - All Norway: https://arbeidsplassen.nav.no/stillinger?v=5")
    urls_input = input("   URLs: ").strip()
    search_urls = [url.strip() for url in urls_input.split(',') if url.strip()]
    
    telegram_token = input("\n📱 Telegram Bot Token (optional): ").strip()
    telegram_chat_id = input("📱 Telegram Chat ID (optional): ").strip()
    
    nav_password = input("\n🔐 NAV Password (optional): ").strip()
    
    user_data = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "fnr": fnr,
        "preferred_locations": preferred_locations,
        "search_urls": search_urls or ["https://arbeidsplassen.nav.no/stillinger?v=5"],
        "telegram_bot_token": telegram_token,
        "telegram_chat_id": telegram_chat_id,
        "nav_password": nav_password,
        "created_date": datetime.now().isoformat(),
        "job_types": ["fulltime", "parttime", "contract"],
        "min_relevance_score": 30,
        "auto_apply_threshold": 85,
        "require_manual_approval": True,
        "max_applications_per_day": 5
    }
    
    if system.create_user_profile(username, user_data):
        print(f"\n✅ User {username} created successfully!")
        print(f"📁 Next steps:")
        print(f"   1. Add resume files to: data/users/{username}/resumes/")
        print(f"   2. Run: python -m src.user_manager analyze {username}")
        print(f"   3. Run: python -m src.user_manager workflow {username}")

def analyze_user_resumes(username: str):
    """Analyze resumes for specific user."""
    system = MultiUserJobSystem()
    
    if username not in system.get_user_list():
        print(f"❌ User {username} not found!")
        return
    
    print(f"🔍 Analyzing resumes for: {username}")
    result = system.analyze_user_resumes(username)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Resume analysis completed for {username}")

def list_all_users():
    """List all users with status."""
    system = MultiUserJobSystem()
    users_status = system.list_users_with_status()
    
    print("👥 ALL USERS STATUS")
    print("=" * 40)
    
    if not users_status:
        print("📭 No users found.")
        print("Create first user: python -m src.user_manager create")
        return
    
    for username, status in users_status.items():
        print(f"\n👤 {username}:")
        print(f"   📄 Resumes: {status['resume_count']}")
        print(f"   🤖 AI Profile: {'✅' if status['has_unified_profile'] else '❌'}")
        print(f"   💼 Jobs: {status['job_count']}")
        print(f"   📱 Telegram: {'✅' if status['telegram_configured'] else '❌'}")

def main():
    """CLI main function."""
    if len(sys.argv) < 2:
        print("📋 MULTI-USER JOB SYSTEM CLI")
        print("Commands:")
        print("  create          - Create new user")
        print("  list            - List all users")
        print("  analyze <user>  - Analyze user resumes")
        print("  workflow <user> - Run workflow for user")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        create_new_user()
    elif command == "list":
        list_all_users()
    elif command == "analyze" and len(sys.argv) > 2:
        analyze_user_resumes(sys.argv[2])
    elif command == "workflow" and len(sys.argv) > 2:
        print(f"🚀 Running workflow for: {sys.argv[2]}")
        print("⚠️ User-specific workflow will be implemented next...")
    else:
        print("❌ Invalid command or missing username")

if __name__ == "__main__":
    main()
