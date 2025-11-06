"""Monitoring API endpoints"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status/{user_id}")
async def get_monitoring_status(user_id: str):
    """Get monitoring status for user"""
    return {"user_id": user_id, "status": "idle"}


@router.post("/start")
async def start_monitoring():
    """Start automated monitoring"""
    return {"message": "Monitoring started"}


@router.post("/stop")
async def stop_monitoring():
    """Stop automated monitoring"""
    return {"message": "Monitoring stopped"}
