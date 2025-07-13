"""Initialize the complete JobBot system."""
import os
from pathlib import Path
from .job_manager import JobManager
from .telegram_bot import TelegramBot
from .sheets_integration import SheetsTracker

def initialize_system():
    """Initialize all system components."""
    print("🚀 Initializing JobBot System")
    print("=" * 40)
    
    # Create necessary directories
    print("📁 Creating directories...")
    directories = [
        "/app/data",
        "/app/data/letters", 
        "/app/data/attachments",
        "/app/src/config"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {dir_path}")
    
    # Initialize database
    print("\n💾 Initializing database...")
    job_manager = JobManager()
    print("  ✅ Database schema created")
    
    # Test Telegram connection
    print("\n📱 Testing Telegram connection...")
    telegram_bot = TelegramBot()
    if telegram_bot.send_message("🤖 JobBot system initialized successfully!"):
        print("  ✅ Telegram connection working")
    else:
        print("  ❌ Telegram connection failed")
    
    # Test Google Sheets connection
    print("\n📊 Testing Google Sheets connection...")
    sheets_tracker = SheetsTracker()
    if sheets_tracker.gc:
        print("  ✅ Google Sheets connection working")
    else:
        print("  ❌ Google Sheets connection failed")
    
    # Check environment variables
    print("\n🔧 Checking environment variables...")
    required_vars = [
        "OPENAI_ENDPOINT",
        "OPENAI_KEY", 
        "TELEGRAM_TOKEN",
        "TELEGRAM_CHAT_ID",
        "GOOGLE_CREDENTIALS_JSON",
        "NAME",
        "EMAIL",
        "PHONE"
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} - MISSING")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Missing environment variables: {', '.join(missing_vars)}")
    else:
        print("\n✅ All environment variables configured")
    
    # Create sample resume file
    resume_path = Path("/app/data/attachments/resume.pdf")
    if not resume_path.exists():
        print(f"\n📄 Please add your resume to: {resume_path}")
        print("   This file is required for job applications")
    else:
        print("\n✅ Resume file found")
    
    print("\n🎉 System initialization complete!")
    print("\nNext steps:")
    print("1. Add your resume.pdf to /app/data/attachments/")
    print("2. Configure your Telegram webhook URL in bot settings")
    print("3. Review and adjust config in src/config/search_config.json")
    print("4. Run the daily workflow: python -m src.main_workflow")

if __name__ == "__main__":
    initialize_system()
