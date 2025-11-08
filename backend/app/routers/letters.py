"""Cover Letter API endpoints"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services import CoverLetterGenerator

router = APIRouter()

# Initialize service
letter_generator = CoverLetterGenerator()


class GenerateLetterRequest(BaseModel):
    job_title: str
    company: str
    job_description: str
    user_profile: Dict[str, Any]
    custom_prompt: Optional[str] = None
    language: str = "norwegian"


class BatchGenerateRequest(BaseModel):
    jobs: List[Dict[str, Any]]
    user_profile: Dict[str, Any]
    custom_prompt: Optional[str] = None
    language: str = "norwegian"


class GeneratePDFRequest(BaseModel):
    cover_letter_text: str
    job_title: str
    company: str


@router.post("/generate")
async def generate_cover_letter(request: GenerateLetterRequest):
    """Generate a personalized cover letter for a job"""
    try:
        job_data = {
            "title": request.job_title,
            "company": request.company,
            "description": request.job_description
        }

        result = await letter_generator.generate_cover_letter(
            job_data=job_data,
            user_profile=request.user_profile,
            custom_prompt=request.custom_prompt,
            language=request.language
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-batch")
async def generate_batch(request: BatchGenerateRequest):
    """Generate cover letters for multiple jobs"""
    try:
        results = await letter_generator.generate_batch(
            jobs=request.jobs,
            user_profile=request.user_profile,
            custom_prompt=request.custom_prompt,
            language=request.language
        )

        successful = [r for r in results if r.get('letter', {}).get('success', False)]

        return {
            "success": True,
            "message": "Batch generation completed",
            "total_jobs": len(results),
            "successful": len(successful),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-pdf")
async def generate_pdf(request: GeneratePDFRequest):
    """Generate PDF version of cover letter"""
    try:
        pdf_bytes = letter_generator.generate_pdf(
            cover_letter_text=request.cover_letter_text,
            job_title=request.job_title,
            company=request.company
        )

        if not pdf_bytes:
            raise HTTPException(
                status_code=500,
                detail="PDF generation failed. Is reportlab installed?"
            )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=cover_letter_{request.job_title}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default-prompt")
async def get_default_prompt(language: str = "norwegian"):
    """Get default cover letter generation prompt"""
    try:
        prompt = letter_generator.get_default_prompt(language=language)
        return {
            "success": True,
            "language": language,
            "prompt": prompt
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
