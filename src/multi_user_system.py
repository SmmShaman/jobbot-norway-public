"""Multi-user job search system with separate profiles."""
import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from .resume_analyzer import ResumeAnalyzer

class MultiUserJobSystem:
    def __init__(self, base_data_dir: str = "/app/data"):
        self.base_dir = Path(base_data_dir)
        self.users_dir = self.base_dir / "users"
        self.users_dir.mkdir(parents=True, exist_ok=True)

    def get_user_list(self) -> List[str]:
        """Get list of all configured users."""
        users = []
        for user_dir in self.users_dir.iterdir():
            if user_dir.is_dir():
                users.append(user_dir.name)
        return sorted(users)

    def create_user_profile(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Create new user profile with directories and config."""
        try:
            user_dir = self.users_dir / username
            user_dir.mkdir(exist_ok=True)
            
            # Create user subdirectories
            (user_dir / "resumes").mkdir(exist_ok=True)
            (user_dir / "letters").mkdir(exist_ok=True)
            (user_dir / "logs").mkdir(exist_ok=True)
            
            # Create user configuration
            user_config = {
                "user_info": {
                    "username": username,
                    "full_name": user_data.get("full_name", ""),
                    "email": user_data.get("email", ""),
                    "phone": user_data.get("phone", ""),
                    "fnr": user_data.get("fnr", ""),
                    "created_date": user_data.get("created_date", "")
                },
                "search_sources": {
                    "finn.no": {
                        "enabled": False,
                        "rss_urls": [],
                        "keywords": [],
                        "exclude_keywords": []
                    },
                    "arbeidsplassen.nav.no": {
                        "enabled": True,
                        "search_urls": user_data.get("search_urls", [
                            "https://arbeidsplassen.nav.no/stillinger?v=5"
                        ]),
                        "keywords": [],
                        "exclude_keywords": []
                    }
                },
                "user_profile": {
                    "preferred_locations": user_data.get("preferred_locations", []),
                    "job_types": user_data.get("job_types", ["fulltime", "parttime"]),
                    "min_relevance_score": user_data.get("min_relevance_score", 30),
                    "unified_resume": None  # Will be filled by resume analyzer
                },
                "application_settings": {
                    "auto_apply_threshold": user_data.get("auto_apply_threshold", 85),
                    "require_manual_approval": user_data.get("require_manual_approval", True),
                    "max_applications_per_day": user_data.get("max_applications_per_day", 5)
                },
                "telegram_settings": {
                    "bot_token": user_data.get("telegram_bot_token", ""),
                    "chat_id": user_data.get("telegram_chat_id", ""),
                    "enabled": bool(user_data.get("telegram_bot_token"))
                },
                "nav_credentials": {
                    "fnr": user_data.get("fnr", ""),
                    "password": user_data.get("nav_password", "")
                }
            }
            
            # Save user config
            config_file = user_dir / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(user_config, f, indent=2, ensure_ascii=False)
            
            # Create user database
            self.init_user_database(username)
            
            print(f"✅ Created user profile: {username}")
            print(f"📁 User directory: {user_dir}")
            print(f"📄 Add resume files to: {user_dir}/resumes/")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating user {username}: {e}")
            return False

    def init_user_database(self, username: str):
        """Initialize SQLite database for user."""
        user_dir = self.users_dir / username
        db_path = user_dir / "jobs.db"
        
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    company TEXT,
                    description TEXT,
                    source TEXT,
                    relevance_score INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'NEW',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    applied_at TEXT,
                    letter_generated BOOLEAN DEFAULT 0,
                    telegram_sent BOOLEAN DEFAULT 0,
                    unified_profile_used TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    application_date TEXT DEFAULT (datetime('now')),
                    status TEXT,
                    nav_response TEXT,
                    error_message TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            """)
            
            conn.commit()

    def get_user_config(self, username: str) -> Optional[Dict[str, Any]]:
        """Load user configuration."""
        config_file = self.users_dir / username / "config.json"
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config for {username}: {e}")
            return None

    def update_user_config(self, username: str, config: Dict[str, Any]) -> bool:
        """Update user configuration."""
        config_file = self.users_dir / username / "config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error updating config for {username}: {e}")
            return False

    def analyze_user_resumes(self, username: str) -> Dict[str, Any]:
        """Analyze all resumes for specific user."""
        user_dir = self.users_dir / username
        resume_dir = user_dir / "resumes"
        
        if not resume_dir.exists():
            return {"error": f"Resume directory not found for {username}"}
        
        # Create user-specific resume analyzer
        analyzer = ResumeAnalyzer()
        analyzer.resume_dir = resume_dir
        
        # Process resumes
        unified_profile = analyzer.process_all_resumes()
        
        # Update user config with unified profile
        if 'error' not in unified_profile:
            config = self.get_user_config(username)
            if config:
                config['user_profile']['unified_resume'] = unified_profile
                self.update_user_config(username, config)
                print(f"✅ Updated {username}'s profile with unified resume")
        
        return unified_profile

    def list_users_with_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all users."""
        users_status = {}
        
        for username in self.get_user_list():
            user_dir = self.users_dir / username
            resume_dir = user_dir / "resumes"
            config_file = user_dir / "config.json"
            
            # Count resume files
            resume_files = list(resume_dir.glob("*")) if resume_dir.exists() else []
            resume_count = len([f for f in resume_files if f.suffix.lower() in ['.pdf', '.docx', '.doc', '.txt']])
            
            # Check if profile is analyzed
            config = self.get_user_config(username)
            has_unified_profile = bool(config and config.get('user_profile', {}).get('unified_resume'))
            
            # Check job database
            db_path = user_dir / "jobs.db"
            job_count = 0
            if db_path.exists():
                try:
                    with sqlite3.connect(db_path) as conn:
                        result = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()
                        job_count = result[0] if result else 0
                except:
                    pass
            
            users_status[username] = {
                "resume_count": resume_count,
                "has_unified_profile": has_unified_profile,
                "job_count": job_count,
                "config_exists": config is not None,
                "telegram_configured": bool(config and config.get('telegram_settings', {}).get('enabled'))
            }
        
        return users_status

if __name__ == "__main__":
    system = MultiUserJobSystem()
    
    print("👥 MULTI-USER JOB SEARCH SYSTEM")
    print("=" * 40)
    
    users_status = system.list_users_with_status()
    
    if users_status:
        print(f"📊 Found {len(users_status)} users:")
        for username, status in users_status.items():
            print(f"\n👤 {username}:")
            print(f"   📄 Resumes: {status['resume_count']}")
            print(f"   🤖 AI Profile: {'✅' if status['has_unified_profile'] else '❌'}")
            print(f"   💼 Jobs processed: {status['job_count']}")
            print(f"   📱 Telegram: {'✅' if status['telegram_configured'] else '❌'}")
    else:
        print("📭 No users found. Create first user:")
        print("   Example: system.create_user_profile('vitalii', {...})")
