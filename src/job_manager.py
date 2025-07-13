"""Job management system for storing and tracking applications."""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

DB_PATH = Path("/app/data/app.db")

class JobManager:
    def __init__(self):
        self.setup_database()
    
    def setup_database(self):
        """Create enhanced database schema."""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(DB_PATH) as conn:
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
                    manual_approval_required BOOLEAN DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    application_date TEXT DEFAULT (datetime('now')),
                    status TEXT,
                    error_message TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            """)
            
            conn.commit()
    
    def add_job(self, job_data: Dict[str, Any]) -> Optional[int]:
        """Add new job to database."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.execute("""
                    INSERT OR IGNORE INTO jobs 
                    (url, title, company, description, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    job_data.get('url'),
                    job_data.get('title'),
                    job_data.get('company', ''),
                    job_data.get('description', ''),
                    job_data.get('source'),
                    datetime.now().isoformat()
                ))
                
                if cursor.rowcount > 0:
                    return cursor.lastrowid
                else:
                    # Job already exists, get ID
                    result = conn.execute(
                        "SELECT id FROM jobs WHERE url = ?", 
                        (job_data.get('url'),)
                    ).fetchone()
                    return result[0] if result else None
                    
        except Exception as e:
            print(f"Error adding job: {e}")
            return None
    
    def update_job_status(self, job_id: int, status: str, error_message: str = None):
        """Update job status."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    UPDATE jobs 
                    SET status = ?, updated_at = datetime('now')
                    WHERE id = ?
                """, (status, job_id))
                
                # Add application record
                conn.execute("""
                    INSERT INTO applications (job_id, status, error_message)
                    VALUES (?, ?, ?)
                """, (job_id, status, error_message))
                
                conn.commit()
        except Exception as e:
            print(f"Error updating job status: {e}")
    
    def get_pending_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs pending for processing."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT * FROM jobs 
                    WHERE status IN ('NEW', 'ANALYZED', 'APPROVED')
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting pending jobs: {e}")
            return []
    
    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get single job by ID."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                row = cursor.fetchone()
                
                return dict(row) if row else None
        except Exception as e:
            print(f"Error getting job: {e}")
            return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get application statistics."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                stats = {}
                
                # Total jobs
                result = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()
                stats['total_jobs'] = result[0]
                
                # By status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM jobs 
                    GROUP BY status
                """)
                
                for row in cursor.fetchall():
                    stats[f"status_{row[0].lower()}"] = row[1]
                
                return stats
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}

if __name__ == "__main__":
    # Test job manager
    jm = JobManager()
    
    test_job = {
        'url': 'https://example.com/job/123',
        'title': 'Test Developer',
        'company': 'Test AS',
        'source': 'finn.no'
    }
    
    job_id = jm.add_job(test_job)
    print(f"Added job with ID: {job_id}")
    print(f"Stats: {jm.get_stats()}")
