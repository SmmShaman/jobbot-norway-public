"""Jobs API endpoints"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from app.services.database import DatabaseService
from app.services.scraper_service import ScraperService
from app.services.ai_service import AIService

router = APIRouter()
db_service = DatabaseService()
scraper_service = ScraperService()
ai_service = AIService()


class ScanJobsRequest(BaseModel):
    user_id: str
    scan_type: str = "MANUAL"  # MANUAL, SCHEDULED, or QUICK


class CreateScanTaskRequest(BaseModel):
    user_id: str
    url: str
    source: str  # FINN or NAV
    scan_type: str = "MANUAL"


class AnalyzeJobRequest(BaseModel):
    job_id: str
    user_id: str


class ApproveJobRequest(BaseModel):
    job_id: str
    user_id: str


class JobsFilterRequest(BaseModel):
    user_id: str
    status: Optional[str] = None


@router.post("/scan-jobs")
async def scan_jobs(request: ScanJobsRequest, background_tasks: BackgroundTasks):
    """
    Trigger job scanning for user.
    Creates scan tasks in queue for Worker to process.
    """
    try:
        # Get user settings
        settings = await db_service.get_settings(request.user_id)

        if not settings:
            raise HTTPException(status_code=404, detail="User settings not found")

        nav_urls = settings.get('nav_search_urls', [])
        finn_urls = settings.get('finn_search_urls', [])

        if not nav_urls and not finn_urls:
            raise HTTPException(
                status_code=400,
                detail="No search URLs configured. Please add NAV or FINN search URLs in Settings."
            )

        # Create scan tasks for each URL
        created_tasks = []

        # Create tasks for NAV URLs
        for url in nav_urls:
            task = await db_service.create_scan_task(
                user_id=request.user_id,
                url=url,
                source='NAV',
                scan_type=request.scan_type
            )
            created_tasks.append(task)

        # Create tasks for FINN URLs
        for url in finn_urls:
            task = await db_service.create_scan_task(
                user_id=request.user_id,
                url=url,
                source='FINN',
                scan_type=request.scan_type
            )
            created_tasks.append(task)

        # Log scan start
        await db_service.create_monitoring_log(
            user_id=request.user_id,
            scan_type=request.scan_type,
            status='RUNNING',
            jobs_found=0,
            jobs_relevant=0
        )

        return {
            "message": f"Created {len(created_tasks)} scan tasks. Worker will process them shortly.",
            "user_id": request.user_id,
            "scan_type": request.scan_type,
            "tasks_created": len(created_tasks),
            "tasks": [{"id": t.get('id'), "url": t.get('url')[:50] + "..."} for t in created_tasks]
        }

    except HTTPException:
        raise
    except Exception as e:
        await db_service.log_monitoring_event(
            request.user_id,
            'SCAN_ERROR',
            {'error': str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-job")
async def analyze_job(request: AnalyzeJobRequest):
    """
    Re-analyze a single job with AI.
    Useful for jobs that need manual re-evaluation.
    """
    try:
        # Get job details
        jobs = await db_service.get_jobs(request.user_id)
        job = next((j for j in jobs if j['id'] == request.job_id), None)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get user profile
        settings = await db_service.get_settings(request.user_id)
        profile = await db_service.get_profile(request.user_id)

        user_profile = {
            'full_name': profile.get('full_name', ''),
            'email': profile.get('email', ''),
            'skills': settings.get('unified_profile', {}).get('skills', ''),
            'experience': settings.get('unified_profile', {}).get('experience', ''),
            'preferred_locations': settings.get('unified_profile', {}).get('preferred_locations', []),
        }

        # Run AI analysis
        analysis = await ai_service.analyze_job_relevance(
            job['title'],
            job['description'],
            job['company'],
            job['location'],
            user_profile
        )

        # Update job with new analysis
        await db_service.update_job(
            request.job_id,
            {
                'relevance_score': analysis.get('relevance_score', 0),
                'ai_analysis': analysis,
                'status': 'ANALYZED'
            }
        )

        return {
            "message": "Job re-analyzed successfully",
            "job_id": request.job_id,
            "analysis": analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve-job")
async def approve_job(request: ApproveJobRequest):
    """
    Approve a job for application.
    This moves the job to APPROVED status, ready for auto-application.
    """
    try:
        await db_service.update_job(
            request.job_id,
            {'status': 'APPROVED'}
        )

        await db_service.log_monitoring_event(
            request.user_id,
            'JOB_APPROVED',
            {'job_id': request.job_id}
        )

        return {
            "message": "Job approved successfully",
            "job_id": request.job_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs")
async def get_jobs(request: JobsFilterRequest):
    """
    Get all jobs for user, optionally filtered by status.
    """
    try:
        jobs = await db_service.get_jobs(request.user_id, request.status)
        return {
            "jobs": jobs,
            "count": len(jobs)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard-stats/{user_id}")
async def get_dashboard_stats(user_id: str):
    """
    Get dashboard statistics for user.
    """
    try:
        stats = await db_service.get_dashboard_stats(user_id)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
