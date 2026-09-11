"""Low-cost liveness and readiness checks."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ...core.database import db

router = APIRouter()


@router.get('/health/live')
async def liveness():
    return {'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()}


@router.get('/health/ready')
async def readiness():
    try:
        await db.command('ping')
    except Exception as exc:
        raise HTTPException(status_code=503, detail='Database unavailable') from exc
    return {'status': 'ready', 'timestamp': datetime.now(timezone.utc).isoformat()}


@router.get('/health')
async def health_check():
    """Backward-compatible readiness alias."""
    return await readiness()


@router.get('/')
async def root():
    return {'message': 'Accessibility Scanner API', 'status': 'running', 'version': '1.1.0'}
