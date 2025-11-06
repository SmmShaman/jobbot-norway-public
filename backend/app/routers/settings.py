"""Settings API endpoints"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from app.services.database import DatabaseService

router = APIRouter()
db_service = DatabaseService()


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    fnr: Optional[str] = None


class SettingsUpdate(BaseModel):
    nav_search_urls: Optional[List[str]] = None
    finn_search_urls: Optional[List[str]] = None
    min_relevance_score: Optional[int] = None
    auto_apply_threshold: Optional[int] = None
    max_applications_per_day: Optional[int] = None
    require_manual_approval: Optional[bool] = None
    nav_fnr: Optional[str] = None
    nav_password_encrypted: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_enabled: Optional[bool] = None


@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile"""
    try:
        profile = await db_service.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/{user_id}")
async def update_profile(user_id: str, updates: ProfileUpdate):
    """Update user profile"""
    try:
        result = await db_service.update_profile(user_id, updates.dict(exclude_unset=True))
        return {"message": "Profile updated successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/{user_id}")
async def get_settings(user_id: str):
    """Get user settings"""
    try:
        settings = await db_service.get_settings(user_id)
        if not settings:
            # Create default settings if they don't exist
            settings = await db_service.create_default_settings(user_id)
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/{user_id}")
async def update_settings(user_id: str, updates: SettingsUpdate):
    """Update user settings"""
    try:
        result = await db_service.update_settings(user_id, updates.dict(exclude_unset=True))
        return {"message": "Settings updated successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume/{user_id}")
async def upload_resume(user_id: str, file: UploadFile = File(...)):
    """Upload user resume to Supabase Storage"""
    try:
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Validate file size (10MB max)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")

        # Upload to Supabase Storage
        file_path = await db_service.upload_resume(user_id, file.filename, content)

        # Update user settings with resume path
        await db_service.update_settings(user_id, {"resume_storage_path": file_path})

        return {
            "message": "Resume uploaded successfully",
            "file_path": file_path
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resume/{user_id}")
async def get_resume_url(user_id: str):
    """Get signed URL for user's resume"""
    try:
        settings = await db_service.get_settings(user_id)
        if not settings or not settings.get("resume_storage_path"):
            raise HTTPException(status_code=404, detail="Resume not found")

        url = await db_service.get_resume_url(settings["resume_storage_path"])
        return {"url": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
