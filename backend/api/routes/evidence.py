"""Authenticated scan-evidence retrieval endpoints."""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Response

from ...core.security import get_current_user
from ...models.user import User
from ...services.entitlements import get_authorized_scan
from ...services.storage import load_png_bytes

router = APIRouter()


@router.get('/scans/{scan_id}/evidence/{evidence_id}')
async def get_issue_evidence(
    scan_id: str,
    evidence_id: str,
    current_user: User = Depends(get_current_user),
):
    scan = await get_authorized_scan(current_user, scan_id)
    base64_map = scan.get('evidence_screenshots') or {}
    key_map = scan.get('evidence_screenshot_keys') or {}
    if evidence_id not in base64_map and evidence_id not in key_map:
        raise HTTPException(status_code=404, detail='Evidence screenshot not found')
    image = await asyncio.to_thread(
        load_png_bytes,
        base64_data=base64_map.get(evidence_id),
        key=key_map.get(evidence_id),
    )
    if not image:
        raise HTTPException(status_code=404, detail='Evidence screenshot not available')
    return Response(
        content=image,
        media_type='image/png',
        headers={
            'Cache-Control': 'private, max-age=300',
            'Content-Disposition': f'inline; filename="evidence_{scan_id[:8]}.png"',
        },
    )
