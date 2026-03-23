"""
Auditly - Website Accessibility Scanner
Main FastAPI application entry point.

This is the refactored modular architecture:
- /core: Configuration, database, security utilities
- /models: Pydantic models for users and scans
- /services: Business logic (scanning, PDF generation, email)
- /api/routes: API endpoints organized by domain
"""
import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from backend.core.database import close_db_connection
from backend.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main FastAPI app
app = FastAPI(
    title="Accessibility Scanner API",
    description="Professional website accessibility scanning platform with visual evidence capture and comprehensive reporting.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Include API router
app.include_router(api_router)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await close_db_connection()
    logger.info("Application shutdown complete")


@app.on_event("startup")
async def startup_event():
    """Log startup."""
    logger.info("Auditly API started successfully")
