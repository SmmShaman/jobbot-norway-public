"""Lightweight helper for reading & writing to the app.db SQLite database."""

from pathlib import Path
import sqlite3
from typing import Optional, Dict, Any

# Absolute path inside the container
DB_PATH = Path("/app/data/app.db")

def _conn() -> sqlite3.Connection:
    """Return a connection with row_factory=dict for easier access."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """Creates the 'jobs' table if it doesn't exist."""
    with _conn() as cx:
        cx.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY,
                url TEXT,
                title TEXT,
                status TEXT DEFAULT 'NEW',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        cx.commit()
    print("Database table 'jobs' is ready.")

def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Return a single row dict or None."""
    with _conn() as cx:
        row = cx.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None

def update_status(job_id: int, status: str) -> None:
    """Set the status column and updated_at timestamp."""
    with _conn() as cx:
        cx.execute(
            "UPDATE jobs SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, job_id),
        )
        cx.commit()
