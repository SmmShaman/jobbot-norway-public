"""
JobBot Norway - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import jobs, applications, monitoring
from app.routers import settings as settings_router
from app.config import settings
import traceback

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


# Global exception handler to ensure CORS headers on all responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions and ensure CORS headers are present"""
    error_detail = str(exc)
    error_traceback = traceback.format_exc()

    # Log the error (in production you'd use proper logging)
    print(f"ERROR: {error_detail}")
    print(f"Traceback: {error_traceback}")

    response = JSONResponse(
        status_code=500,
        content={"detail": error_detail, "type": "internal_server_error"}
    )

    # Manually add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"

    return response


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
