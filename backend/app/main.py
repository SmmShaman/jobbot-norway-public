"""
JobBot Norway - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import jobs, applications, monitoring
from app.routers import settings as settings_router
from app.config import settings

app = FastAPI(
    title="JobBot Norway API",
    description="Automated job search and application system",
    version="1.0.0",
)

# CORS configuration
# Temporarily allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(applications.router, prefix="/api", tags=["applications"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])


@app.get("/")
async def root():
    return {
        "message": "JobBot Norway API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with CORS enabled"""
    return {"status": "healthy", "cors": "enabled"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
