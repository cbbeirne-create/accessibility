"""Scan API routes: create, retrieve, export, compare and manage accessibility scans."""
import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response

from ...core.config import settings
from ...core.database import db
from ...core.security import get_current_user
from ...models.scan import ScanRequest, ScanRequestCreate
from ...models.user import User
from ...services.entitlements import (
    get_effective_plan,
    get_limits,
    get_scan_by_id_for_user,
    get_scan_scope,
    release_scan_quota,
    reserve_scan_quota,
)
from ...services.evidence_storage import load_png
from ...services.external_scanners import runScanWithExternalApi
from ...services.pdf_generator import ReportExporter
from ...services.scan_queue import enqueue_scan
from ...services.url_security import UnsafeScanTarget, validate_scan_url

router = APIRouter()
logger = logging.getLogger(__name__)


def _require_verified_email(user: User) -> None:
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email address before running scans")


@router.get("/scans", response_model=List[ScanRequest])
async def get_scan_requests(current_user: User = Depends(get_current_user)):
    scope = await get_scan_scope(current_user)
    documents = await db.scan_requests.find(scope).sort("createdAt", -1).to_list(100)
    return [ScanRequest(**document) for document in documents]


@router.post("/scans", response_model=ScanRequest)
async def create_scan_request(input: ScanRequestCreate, current_user: User = Depends(get_current_user)):
    _require_verified_email(current_user)
    try:
        await validate_scan_url(str(input.url))
    except UnsafeScanTarget as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not await reserve_scan_quota(current_user):
        plan = await get_effective_plan(current_user)
        limits = await get_limits(current_user)
        raise HTTPException(
            status_code=403,
            detail=f"Scan limit exceeded. {plan.value.title()} plan allows {limits['monthly_scans']} scans per month.",
        )

    try:
        scan_obj = ScanRequest(
            url=input.url,
            tool=input.tool,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
        )
        scan_data = scan_obj.dict()
        scan_data["url"] = str(scan_data["url"])
        await db.scan_requests.insert_one(scan_data)
        await enqueue_scan(scan_obj.id, str(input.url), input.tool.value if input.tool else "axe-core")
    except Exception:
        await release_scan_quota(current_user.id)
        await db.scan_requests.delete_one({"id": locals().get("scan_obj").id}) if locals().get("scan_obj") else None
        logger.exception("Failed to create scan request")
        raise HTTPException(status_code=500, detail="Failed to create scan request")

    return scan_obj


@router.get("/scans/stats")
async def get_scan_stats(current_user: User = Depends(get_current_user)):
    scope = await get_scan_scope(current_user)
    scans = await db.scan_requests.find({**scope, "status": "completed"}).sort("createdAt", -1).to_list(100)
    if not scans:
        return {
            "total_scans": 0,
            "average_score": 0,
            "best_score": 0,
            "worst_score": 0,
            "unique_urls": 0,
            "score_history": [],
            "recent_trend": None,
        }

    scores = [s["score"] for s in scans if s.get("score") is not None]
    score_history = [
        {"date": scan.get("createdAt"), "score": scan.get("score"), "url": scan.get("url")}
        for scan in reversed(scans[:10])
    ]
    recent_scores = scores[:5]
    recent_trend = None
    if len(recent_scores) >= 2:
        midpoint = max(1, len(recent_scores) // 2)
        recent_average = sum(recent_scores[:midpoint]) / len(recent_scores[:midpoint])
        older_average = sum(recent_scores[midpoint:]) / len(recent_scores[midpoint:])
        recent_trend = {
            "direction": "up" if recent_average > older_average else "down" if recent_average < older_average else "stable",
            "recent_average": round(recent_average, 1),
            "older_average": round(older_average, 1),
        }

    return {
        "total_scans": len(scans),
        "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "best_score": max(scores) if scores else 0,
        "worst_score": min(scores) if scores else 0,
        "unique_urls": len({s.get("url") for s in scans}),
        "score_history": score_history,
        "recent_trend": recent_trend,
    }


@router.get("/scans/urls")
async def get_scanned_urls(current_user: User = Depends(get_current_user)):
    scope = await get_scan_scope(current_user)
    pipeline = [
        {"$match": {**scope, "status": "completed"}},
        {"$sort": {"createdAt": 1}},
        {"$group": {
            "_id": "$url",
            "scan_count": {"$sum": 1},
            "latest_scan": {"$max": "$createdAt"},
            "latest_score": {"$last": "$score"},
            "avg_score": {"$avg": "$score"},
        }},
        {"$sort": {"latest_scan": -1}},
        {"$limit": 50},
    ]
    results = await db.scan_requests.aggregate(pipeline).to_list(50)
    return {
        "urls": [
            {
                "url": row["_id"],
                "scan_count": row["scan_count"],
                "latest_scan": row["latest_scan"],
                "latest_score": row["latest_score"],
                "avg_score": round(row["avg_score"], 1) if row.get("avg_score") is not None else 0,
            }
            for row in results
        ],
        "total": len(results),
    }


@router.get("/scans/history/by-url")
async def get_scan_history_by_url(url: str, current_user: User = Depends(get_current_user)):
    scope = await get_scan_scope(current_user)
    normalized = url.rstrip("/")
    candidates = list({url, normalized, f"{normalized}/"})
    scans = await db.scan_requests.find(
        {**scope, "status": "completed", "url": {"$in": candidates}}
    ).sort("createdAt", -1).to_list(100)

    if not scans:
        return {"url": url, "total_scans": 0, "scans": [], "trend": None}

    scores = [s["score"] for s in scans if s.get("score") is not None]
    trend = None
    if len(scores) >= 2:
        change = scores[0] - scores[1]
        trend = {
            "direction": "up" if change > 0 else "down" if change < 0 else "stable",
            "change": change,
            "change_percent": round((change / scores[1] * 100), 1) if scores[1] else 0,
            "average_score": round(sum(scores) / len(scores), 1),
            "best_score": max(scores),
            "worst_score": min(scores),
            "total_scans": len(scores),
        }

    formatted = []
    for scan in scans:
        issues = scan.get("issues") or {}
        formatted.append({
            "id": scan.get("id"),
            "url": scan.get("url"),
            "score": scan.get("score"),
            "status": scan.get("status"),
            "createdAt": scan.get("createdAt"),
            "tool": scan.get("tool"),
            "issues_summary": {
                "failed": len(issues.get("failed", [])),
                "passed": len(issues.get("passed", [])),
                "incomplete": len(issues.get("incomplete", [])),
            },
        })
    return {"url": url, "total_scans": len(formatted), "scans": formatted, "trend": trend}


@router.get("/scans/{scan_id}", response_model=ScanRequest)
async def get_scan_request(scan_id: str, current_user: User = Depends(get_current_user)):
    scan = await get_scan_by_id_for_user(scan_id, current_user)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan request not found")
    return ScanRequest(**scan)


@router.delete("/scans/{scan_id}")
async def delete_scan_request(scan_id: str, current_user: User = Depends(get_current_user)):
    scope = await get_scan_scope(current_user)
    result = await db.scan_requests.delete_one({"id": scan_id, **scope})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scan request not found")
    await db.scan_jobs.delete_many({"scan_id": scan_id, "status": {"$in": ["queued", "retry"]}})
    return {"message": "Scan request deleted successfully"}


@router.get("/scans/{scan_id}/export/pdf")
async def export_scan_pdf(scan_id: str, current_user: User = Depends(get_current_user)):
    limits = await get_limits(current_user)
    if not limits["can_export_pdf"]:
        raise HTTPException(status_code=403, detail="PDF export requires Pro plan")
    scan_data = await get_scan_by_id_for_user(scan_id, current_user)
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")
    pdf_bytes = await ReportExporter.generate_pdf_report(scan_data)
    url_safe = scan_data.get("url", "scan").replace("https://", "").replace("http://", "").replace("/", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=accessibility_report_{url_safe}_{scan_id[:8]}.pdf"},
    )


@router.get("/scans/{scan_id}/export/json")
async def export_scan_json(scan_id: str, current_user: User = Depends(get_current_user)):
    scan_data = await get_scan_by_id_for_user(scan_id, current_user)
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")
    report = await ReportExporter.generate_json_report(scan_data)
    url_safe = scan_data.get("url", "scan").replace("https://", "").replace("http://", "").replace("/", "_")
    return Response(
        content=json.dumps(report, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=accessibility_data_{url_safe}_{scan_id[:8]}.json"},
    )


@router.get("/scans/{scan_id}/screenshot")
async def get_scan_screenshot(scan_id: str, current_user: User = Depends(get_current_user)):
    scan_data = await get_scan_by_id_for_user(scan_id, current_user)
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")
    screenshot_ref = scan_data.get("full_page_screenshot")
    if not screenshot_ref:
        raise HTTPException(status_code=404, detail="Screenshot not available")
    try:
        image_bytes = await load_png(screenshot_ref)
    except Exception as exc:
        logger.exception("Failed to load screenshot evidence for %s", scan_id)
        raise HTTPException(status_code=502, detail="Screenshot evidence could not be loaded") from exc
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=scan_{scan_id[:8]}_screenshot.png"},
    )


@router.post("/scans/{scan_id}/run-external")
async def run_external_api_scan(scan_id: str, current_user: User = Depends(get_current_user)):
    _require_verified_email(current_user)
    scan_request = await get_scan_by_id_for_user(scan_id, current_user)
    if not scan_request:
        raise HTTPException(status_code=404, detail="Scan request not found")
    result = await runScanWithExternalApi(scan_id)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=f"External API scan failed: {result.get('error', 'Unknown error')}")
    return {
        "message": "External API scan completed successfully",
        "scan_id": scan_id,
        "score": result.get("score"),
        "tool": result.get("tool"),
    }


@router.get("/external-apis/status")
async def get_external_apis_status(current_user: User = Depends(get_current_user)):
    return {
        "wave": {"configured": bool(settings.WAVE_API_KEY)},
        "equalweb": {"configured": bool(settings.EQUALWEB_API_KEY)},
        "accessibe": {"configured": bool(settings.ACCESSIBE_API_KEY)},
    }


@router.get("/scans/compare/{scan_id_1}/{scan_id_2}")
async def compare_scans(scan_id_1: str, scan_id_2: str, current_user: User = Depends(get_current_user)):
    scan1 = await get_scan_by_id_for_user(scan_id_1, current_user)
    scan2 = await get_scan_by_id_for_user(scan_id_2, current_user)
    if not scan1 or not scan2:
        raise HTTPException(status_code=404, detail="One or both scans not found")

    older_scan, newer_scan = (scan1, scan2) if scan1.get("createdAt") <= scan2.get("createdAt") else (scan2, scan1)
    older_issues = (older_scan.get("issues") or {}).get("failed", [])
    newer_issues = (newer_scan.get("issues") or {}).get("failed", [])
    older_ids = {issue.get("id") for issue in older_issues}
    newer_ids = {issue.get("id") for issue in newer_issues}
    fixed_ids = older_ids - newer_ids
    new_ids = newer_ids - older_ids
    unchanged_ids = older_ids & newer_ids

    fixed = [issue for issue in older_issues if issue.get("id") in fixed_ids]
    new = [issue for issue in newer_issues if issue.get("id") in new_ids]
    unchanged = [issue for issue in newer_issues if issue.get("id") in unchanged_ids]
    older_score = older_scan.get("score") or 0
    newer_score = newer_scan.get("score") or 0
    change = newer_score - older_score

    return {
        "comparison": {
            "older_scan": {
                "id": older_scan.get("id"), "url": older_scan.get("url"), "score": older_score,
                "createdAt": older_scan.get("createdAt"), "total_failed": len(older_issues),
                "total_passed": len((older_scan.get("issues") or {}).get("passed", [])),
                "total_incomplete": len((older_scan.get("issues") or {}).get("incomplete", [])),
            },
            "newer_scan": {
                "id": newer_scan.get("id"), "url": newer_scan.get("url"), "score": newer_score,
                "createdAt": newer_scan.get("createdAt"), "total_failed": len(newer_issues),
                "total_passed": len((newer_scan.get("issues") or {}).get("passed", [])),
                "total_incomplete": len((newer_scan.get("issues") or {}).get("incomplete", [])),
            },
            "score_change": change,
            "score_change_percent": round((change / older_score * 100), 1) if older_score else 0,
            "improved": change > 0,
        },
        "issues": {
            "fixed": {"count": len(fixed), "items": fixed[:20]},
            "new": {"count": len(new), "items": new[:20]},
            "unchanged": {"count": len(unchanged), "items": unchanged[:20]},
        },
        "summary": {
            "issues_fixed": len(fixed),
            "new_issues": len(new),
            "unchanged_issues": len(unchanged),
            "net_change": len(fixed) - len(new),
        },
    }
