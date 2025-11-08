"""
JobBot Norway - FastAPI Backend
Main application entry point with integrated AI services
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import jobs, applications, monitoring, letters, forms
from app.config import settings

app = FastAPI(
    title="JobBot Norway API",
    description="Automated job search and application system with AI-powered analysis, cover letter generation, and form automation",
    version="2.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(letters.router, prefix="/api/letters", tags=["cover-letters"])
app.include_router(forms.router, prefix="/api/forms", tags=["form-automation"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])


@app.get("/")
async def root():
    return {
        "message": "JobBot Norway API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "AI Job Analysis",
            "Web Scraping (NAV, FINN)",
            "Cover Letter Generation",
            "Form Automation"
        ]
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/info")
async def api_info():
    """Get API information and available endpoints"""
    return {
        "title": "JobBot Norway API",
        "version": "2.0.0",
        "services": {
            "jobs": {
                "scan": "/api/jobs/scan-jobs",
                "analyze": "/api/jobs/analyze-job",
                "batch_analyze": "/api/jobs/analyze-jobs-batch"
            },
            "letters": {
                "generate": "/api/letters/generate",
                "batch": "/api/letters/generate-batch",
                "pdf": "/api/letters/generate-pdf"
            },
            "forms": {
                "analyze": "/api/forms/analyze",
                "submit": "/api/forms/submit",
                "status": "/api/forms/check-status",
                "script": "/api/forms/generate-script"
            }
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
