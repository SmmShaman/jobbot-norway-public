"""Applications API endpoints"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/apply")
async def apply_to_job():
    """Submit job application using Skyvern"""
    # TODO: Implement Skyvern integration
    return {"message": "Application submitted"}


@router.post("/report-nav")
async def report_to_nav():
    """Report application to NAV"""
    # TODO: Implement NAV reporting
    return {"message": "Reported to NAV"}
