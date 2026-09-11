"""Auditly FastAPI application entry point."""
import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from backend.api import api_router
from backend.core.config import settings
from backend.core.database import close_db_connection, ensure_indexes
from backend.core.rate_limit import RateLimitMiddleware
from backend.services.scheduler_service import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Accessibility Scanner API",
    description="Website accessibility scanning platform with visual evidence and reporting.",
    version="1.1.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
)
app.include_router(api_router)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.on_event("startup")
async def startup_event():
    settings.validate_runtime()
    await ensure_indexes()
    logger.info("Auditly API starting in %s mode", settings.ENVIRONMENT)
    await start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    await stop_scheduler()
    await close_db_connection()
    logger.info("Application shutdown complete")
