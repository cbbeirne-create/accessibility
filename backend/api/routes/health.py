"""Lightweight health and readiness endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ...core.database import db

router = APIRouter()


@router.get("/health/live")
async def liveness_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.1.0",
    }


@router.get("/health/ready")
async def readiness_check():
    try:
        await db.command("ping")
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {"database": "healthy"},
        "version": "1.1.0",
    }


@router.get("/health")
async def health_check():
    """Backwards-compatible readiness alias used by existing deployments."""
    return await readiness_check()


@router.get("/")
async def root():
    return {"message": "Accessibility Scanner API", "status": "running", "version": "1.1.0"}
