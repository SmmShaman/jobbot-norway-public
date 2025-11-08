"""Form Automation API endpoints"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services import FormAnalyzer

router = APIRouter()

# Initialize service
form_analyzer = FormAnalyzer()


class AnalyzeFormRequest(BaseModel):
    html_content: str
    job_title: str
    company: str
    screenshot_base64: Optional[str] = None


class SubmitFormRequest(BaseModel):
    url: str
    form_data: Dict[str, Any]
    form_analysis: Optional[Dict[str, Any]] = None


class CheckStatusRequest(BaseModel):
    task_id: str


class GenerateScriptRequest(BaseModel):
    form_analysis: Dict[str, Any]
    form_data: Dict[str, str]


@router.post("/analyze")
async def analyze_form(request: AnalyzeFormRequest):
    """Analyze a job application form and return filling instructions"""
    try:
        analysis = await form_analyzer.analyze_application_form(
            html_content=request.html_content,
            job_title=request.job_title,
            company=request.company,
            screenshot_base64=request.screenshot_base64
        )

        return {
            "success": True,
            "message": "Form analysis completed",
            "analysis": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
async def submit_form(request: SubmitFormRequest):
    """Submit application form using Skyvern automation"""
    try:
        result = await form_analyzer.submit_via_skyvern(
            url=request.url,
            form_data=request.form_data,
            form_analysis=request.form_analysis
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Submission failed")
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-status")
async def check_status(request: CheckStatusRequest):
    """Check status of Skyvern automation task"""
    try:
        status = await form_analyzer.check_skyvern_status(
            task_id=request.task_id
        )

        if not status.get("success"):
            raise HTTPException(
                status_code=500,
                detail=status.get("error", "Status check failed")
            )

        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-script")
async def generate_playwright_script(request: GenerateScriptRequest):
    """Generate Playwright automation script from form analysis"""
    try:
        script = form_analyzer.generate_playwright_script(
            form_analysis=request.form_analysis,
            form_data=request.form_data
        )

        return {
            "success": True,
            "message": "Playwright script generated",
            "script": script
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_skyvern_health():
    """Check if Skyvern service is available"""
    try:
        import httpx
        from app.config import settings

        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{settings.SKYVERN_API_URL}/health")
            response.raise_for_status()

        return {
            "success": True,
            "message": "Skyvern is available",
            "url": settings.SKYVERN_API_URL
        }

    except httpx.ConnectError:
        return {
            "success": False,
            "message": "Skyvern is not available",
            "error": "Connection failed. Is Skyvern running?",
            "url": settings.SKYVERN_API_URL
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Health check failed",
            "error": str(e)
        }
