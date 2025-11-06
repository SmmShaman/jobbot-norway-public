"""Database service for Supabase operations"""
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from supabase import create_client, Client
from app.config import settings


class DatabaseService:
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        result = self.client.table("profiles").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None

    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("profiles").update(updates).eq("id", user_id).execute()
        return result.data[0] if result.data else {}

    async def get_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user settings"""
        result = self.client.table("user_settings").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None

    async def create_default_settings(self, user_id: str) -> Dict[str, Any]:
        """Create default settings for new user"""
        default_settings = {
            "user_id": user_id,
            "nav_search_urls": [],
            "finn_search_urls": [],
            "min_relevance_score": 70,
            "auto_apply_threshold": 85,
            "max_applications_per_day": 5,
            "require_manual_approval": True,
            "telegram_enabled": False,
        }
        result = self.client.table("user_settings").insert(default_settings).execute()
        return result.data[0] if result.data else {}

    async def update_settings(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user settings"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("user_settings").update(updates).eq("user_id", user_id).execute()
        return result.data[0] if result.data else {}

    async def upload_resume(self, user_id: str, filename: str, content: bytes) -> str:
        """Upload resume to Supabase Storage"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = f"{user_id}/resume_{timestamp}.pdf"

        # Upload to resumes bucket
        result = self.client.storage.from_("resumes").upload(
            file_path,
            content,
            file_options={"content-type": "application/pdf"}
        )

        return file_path

    async def get_resume_url(self, file_path: str) -> str:
        """Get signed URL for resume (valid for 1 hour)"""
        result = self.client.storage.from_("resumes").create_signed_url(
            file_path,
            expires_in=3600  # 1 hour
        )
        return result.get("signedURL", "")

    async def get_jobs(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get jobs for user"""
        query = self.client.table("jobs").select("*").eq("user_id", user_id)

        if status:
            query = query.eq("status", status)

        query = query.order("discovered_at", desc=True)
        result = query.execute()
        return result.data

    async def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new job entry"""
        job_data["discovered_at"] = datetime.utcnow().isoformat()
        result = self.client.table("jobs").insert(job_data).execute()
        return result.data[0] if result.data else {}

    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update job entry"""
        result = self.client.table("jobs").update(updates).eq("id", job_id).execute()
        return result.data[0] if result.data else {}

    async def get_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard statistics for user"""
        # Get jobs count by status
        jobs = await self.get_jobs(user_id)

        # Calculate statistics
        total_jobs = len(jobs)
        new_jobs = len([j for j in jobs if j.get("status") == "NEW"])
        analyzed_jobs = len([j for j in jobs if j.get("status") == "ANALYZED"])
        applied_jobs = len([j for j in jobs if j.get("status") == "APPLIED"])

        # Get applications count
        applications_result = self.client.table("applications").select("*").eq("user_id", user_id).execute()
        total_applications = len(applications_result.data)

        # Get recent applications (last 7 days)
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        recent_apps = self.client.table("applications").select("*").eq("user_id", user_id).gte("applied_at", week_ago).execute()
        applications_this_week = len(recent_apps.data)

        return {
            "total_jobs": total_jobs,
            "new_jobs": new_jobs,
            "analyzed_jobs": analyzed_jobs,
            "applied_jobs": applied_jobs,
            "total_applications": total_applications,
            "applications_this_week": applications_this_week,
        }

    async def create_application(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create application record"""
        app_data["applied_at"] = datetime.utcnow().isoformat()
        result = self.client.table("applications").insert(app_data).execute()
        return result.data[0] if result.data else {}

    async def log_monitoring_event(self, user_id: str, event_type: str, details: Dict[str, Any]) -> None:
        """Log monitoring event"""
        log_entry = {
            "user_id": user_id,
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.client.table("monitoring_logs").insert(log_entry).execute()
