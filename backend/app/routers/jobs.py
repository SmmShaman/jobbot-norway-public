"""Jobs API endpoints"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services import AIAnalyzer, JobScraper

router = APIRouter()

# Initialize services
ai_analyzer = AIAnalyzer()
job_scraper = JobScraper()


class ScanJobsRequest(BaseModel):
    user_id: str
    search_url: str
    limit: Optional[int] = 10


class AnalyzeJobRequest(BaseModel):
    job_title: str
    job_description: str
    user_skills: str
    user_preferences: Optional[str] = None


class BatchAnalyzeRequest(BaseModel):
    jobs: List[Dict[str, Any]]
    user_skills: str
    user_preferences: Optional[str] = None


@router.post("/scan-jobs")
async def scan_jobs(request: ScanJobsRequest):
    """Scan and scrape jobs from various sources"""
    try:
        # Determine source from URL
        if 'arbeidsplassen.nav.no' in request.search_url:
            jobs = await job_scraper.scrape_nav_no(
                search_url=request.search_url,
                limit=request.limit
            )
            source = "NAV"
        elif 'finn.no' in request.search_url:
            jobs = await job_scraper.scrape_finn_no(
                search_url=request.search_url,
                limit=request.limit
            )
            source = "FINN"
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported job board. Use arbeidsplassen.nav.no or finn.no"
            )

        return {
            "success": True,
            "message": "Job scan completed",
            "user_id": request.user_id,
            "source": source,
            "jobs_found": len(jobs),
            "jobs": jobs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-job")
async def analyze_job(request: AnalyzeJobRequest):
    """Analyze single job with AI for relevance"""
    try:
        analysis = ai_analyzer.analyze_job_relevance(
            job_title=request.job_title,
            job_description=request.job_description,
            user_skills=request.user_skills,
            user_preferences=request.user_preferences
        )

        return {
            "success": True,
            "message": "Job analysis completed",
            "analysis": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-jobs-batch")
async def analyze_jobs_batch(request: BatchAnalyzeRequest):
    """Analyze multiple jobs with AI"""
    try:
        results = ai_analyzer.analyze_batch(
            jobs=request.jobs,
            user_skills=request.user_skills,
            user_preferences=request.user_preferences
        )

        relevant_jobs = [r for r in results if r.get('analysis', {}).get('is_relevant', False)]

        return {
            "success": True,
            "message": "Batch analysis completed",
            "total_jobs": len(results),
            "relevant_jobs": len(relevant_jobs),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
