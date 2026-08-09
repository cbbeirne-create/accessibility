"""
Scan API routes: create, retrieve, export, and manage accessibility scans.
"""
import json
import logging
import base64
from typing import List, Dict, Any
import os

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Response

from ...core.config import settings
from ...core.database import db
from ...core.security import get_current_user
from ...models.user import User, UserPlan
from ...models.scan import ScanRequest, ScanRequestCreate, ScanRequestUpdate, ScanStatus
from ...services.playwright_engine import perform_accessibility_scan
from ...services.pdf_generator import ReportExporter
from ...services.external_scanners import runScanWithExternalApi

router = APIRouter()


def get_user_scan_limits(plan: UserPlan) -> Dict[str, Any]:
    """Get scan limits for user plan."""
    if plan == UserPlan.free:
        return {
            "monthly_scans": 2,
            "can_export_pdf": False,
            "can_export_json": True,
            "can_view_screenshots": True
        }
    elif plan == UserPlan.pro:
        return {
            "monthly_scans": -1,
            "can_export_pdf": True,
            "can_export_json": True,
            "can_view_screenshots": True
        }


async def get_effective_user_plan(user: User) -> UserPlan:
    """
    Get user's effective plan considering team membership.
    If user is in an org, they inherit the owner's plan.
    """
    if not user.organization_id:
        return user.plan
    
    # Get organization owner's plan
    org = await db.organizations.find_one({"id": user.organization_id})
    if not org:
        return user.plan
    
    owner = await db.users.find_one({"id": org["owner_id"]})
    if not owner:
        return user.plan
    
    return UserPlan(owner.get("plan", "free"))


async def check_scan_limits(user: User) -> bool:
    """Check if user can create more scans this month."""
    effective_plan = await get_effective_user_plan(user)
    limits = get_user_scan_limits(effective_plan)
    if limits["monthly_scans"] == -1:
        return True
    return user.scans_used_this_month < limits["monthly_scans"]


async def increment_user_scan_count(user_id: str):
    """Increment user's monthly scan count."""
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"scans_used_this_month": 1}}
    )


async def get_user_scan_query(user: User) -> Dict[str, Any]:
    """
    Get the query for fetching user's scans.
    If user is in an org, fetch all org scans. Otherwise, fetch personal scans.
    """
    if user.organization_id:
        return {"organization_id": user.organization_id}
    return {"user_id": user.id, "organization_id": None}


@router.get("/scans", response_model=List[ScanRequest])
async def get_scan_requests(current_user: User = Depends(get_current_user)):
    """Get all scan requests for the authenticated user (or their organization)."""
    try:
        query = await get_user_scan_query(current_user)
        scan_requests = await db.scan_requests.find(query).sort("createdAt", -1).to_list(100)
        return [ScanRequest(**scan_request) for scan_request in scan_requests]
    except Exception as e:
        logging.error(f"Error fetching scan requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan requests")


@router.post("/scans", response_model=ScanRequest)
async def create_scan_request(
    input: ScanRequestCreate, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Create a new accessibility scan request (requires authentication)."""
    try:
        can_scan = await check_scan_limits(current_user)
        if not can_scan:
            effective_plan = await get_effective_user_plan(current_user)
            limits = get_user_scan_limits(effective_plan)
            raise HTTPException(
                status_code=403, 
                detail=f"Scan limit exceeded. {effective_plan.title()} plan allows {limits['monthly_scans']} scans per month. Upgrade to Pro for unlimited scans."
            )
        
        scan_dict = input.dict()
        scan_dict['url'] = str(scan_dict['url'])
        scan_dict['user_id'] = current_user.id
        # If user is in an org, scan belongs to the org
        scan_dict['organization_id'] = current_user.organization_id
        scan_obj = ScanRequest(**scan_dict)
        scan_data = scan_obj.dict()
        scan_data['url'] = str(scan_data['url'])
        
        await db.scan_requests.insert_one(scan_data)
        await increment_user_scan_count(current_user.id)
        
        background_tasks.add_task(
            perform_accessibility_scan,
            scan_obj.id,
            str(input.url),
            input.tool
        )
        
        return scan_obj
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating scan request: {e}")
        raise HTTPException(status_code=500, detail="Failed to create scan request")


# ============================================
# Static routes MUST be defined before parameterized routes
# ============================================

@router.get("/scans/stats")
async def get_scan_stats(current_user: User = Depends(get_current_user)):
    """
    Get overall scan statistics for the user.
    Includes total scans, average score, score trend over time.
    """
    try:
        scans = await db.scan_requests.find({
            "user_id": current_user.id,
            "status": "completed"
        }).sort("createdAt", -1).to_list(100)
        
        if not scans:
            return {
                "total_scans": 0,
                "average_score": 0,
                "best_score": 0,
                "worst_score": 0,
                "unique_urls": 0,
                "score_history": [],
                "recent_trend": None
            }
        
        scores = [s.get("score", 0) for s in scans if s.get("score") is not None]
        urls = list(set(s.get("url") for s in scans))
        
        score_history = []
        for scan in scans[:10]:
            score_history.append({
                "date": scan.get("createdAt"),
                "score": scan.get("score"),
                "url": scan.get("url")
            })
        score_history.reverse()
        
        recent_scores = scores[:5] if len(scores) >= 5 else scores
        recent_trend = None
        if len(recent_scores) >= 2:
            avg_recent = sum(recent_scores[:3]) / 3 if len(recent_scores) >= 3 else recent_scores[0]
            avg_older = sum(recent_scores[-3:]) / 3 if len(recent_scores) >= 3 else recent_scores[-1]
            trend_direction = "up" if avg_recent > avg_older else "down" if avg_recent < avg_older else "stable"
            recent_trend = {
                "direction": trend_direction,
                "recent_average": round(avg_recent, 1),
                "older_average": round(avg_older, 1)
            }
        
        return {
            "total_scans": len(scans),
            "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "best_score": max(scores) if scores else 0,
            "worst_score": min(scores) if scores else 0,
            "unique_urls": len(urls),
            "score_history": score_history,
            "recent_trend": recent_trend
        }
        
    except Exception as e:
        logging.error(f"Error fetching scan stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan statistics")


@router.get("/scans/urls")
async def get_scanned_urls(current_user: User = Depends(get_current_user)):
    """Get list of unique URLs the user has scanned with scan counts."""
    try:
        pipeline = [
            {"$match": {"user_id": current_user.id, "status": "completed"}},
            {"$group": {
                "_id": "$url",
                "scan_count": {"$sum": 1},
                "latest_scan": {"$max": "$createdAt"},
                "latest_score": {"$last": "$score"},
                "avg_score": {"$avg": "$score"}
            }},
            {"$sort": {"latest_scan": -1}},
            {"$limit": 50}
        ]
        
        results = await db.scan_requests.aggregate(pipeline).to_list(50)
        
        urls = []
        for r in results:
            urls.append({
                "url": r["_id"],
                "scan_count": r["scan_count"],
                "latest_scan": r["latest_scan"],
                "latest_score": r["latest_score"],
                "avg_score": round(r["avg_score"], 1) if r["avg_score"] else 0
            })
        
        return {"urls": urls, "total": len(urls)}
        
    except Exception as e:
        logging.error(f"Error fetching scanned URLs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scanned URLs")


@router.get("/scans/history/by-url")
async def get_scan_history_by_url_early(
    url: str,
    current_user: User = Depends(get_current_user)
):
    """Get scan history for a specific URL."""
    try:
        normalized_url = url.rstrip('/')
        
        scans = await db.scan_requests.find({
            "user_id": current_user.id,
            "status": "completed",
            "$or": [
                {"url": url},
                {"url": normalized_url},
                {"url": url + "/"},
                {"url": normalized_url + "/"}
            ]
        }).sort("createdAt", -1).to_list(100)
        
        if not scans:
            return {"url": url, "total_scans": 0, "scans": [], "trend": None}
        
        scores = [s.get("score", 0) for s in scans if s.get("score") is not None]
        
        trend = None
        if len(scores) >= 2:
            latest_score = scores[0]
            previous_score = scores[1]
            change = latest_score - previous_score
            avg_score = sum(scores) / len(scores)
            
            trend = {
                "direction": "up" if change > 0 else "down" if change < 0 else "stable",
                "change": change,
                "change_percent": round((change / previous_score * 100), 1) if previous_score > 0 else 0,
                "average_score": round(avg_score, 1),
                "best_score": max(scores),
                "worst_score": min(scores),
                "total_scans": len(scores)
            }
        
        formatted_scans = []
        for scan in scans:
            formatted_scans.append({
                "id": scan.get("id"),
                "url": scan.get("url"),
                "score": scan.get("score"),
                "status": scan.get("status"),
                "createdAt": scan.get("createdAt"),
                "tool": scan.get("tool"),
                "issues_summary": {
                    "failed": len(scan.get("issues", {}).get("failed", [])),
                    "passed": len(scan.get("issues", {}).get("passed", [])),
                    "incomplete": len(scan.get("issues", {}).get("incomplete", []))
                } if scan.get("issues") else None
            })
        
        return {"url": url, "total_scans": len(formatted_scans), "scans": formatted_scans, "trend": trend}
        
    except Exception as e:
        logging.error(f"Error fetching scan history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan history")


@router.get("/scans/{scan_id}", response_model=ScanRequest)
async def get_scan_request(scan_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific scan request by ID (user can only access their own scans)."""
    try:
        scan_request = await db.scan_requests.find_one(
            {"id": scan_id, "user_id": current_user.id}
        )
        if not scan_request:
            raise HTTPException(status_code=404, detail="Scan request not found")
        return ScanRequest(**scan_request)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching scan request {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan request")


@router.put("/scans/{scan_id}", response_model=ScanRequest)
async def update_scan_request(scan_id: str, update_data: ScanRequestUpdate):
    """Update a scan request (used for updating status, score, issues)."""
    try:
        current_scan = await db.scan_requests.find_one({"id": scan_id})
        if not current_scan:
            raise HTTPException(status_code=404, detail="Scan request not found")
        
        update_dict = {}
        if update_data.status is not None:
            update_dict["status"] = update_data.status
        if update_data.score is not None:
            update_dict["score"] = update_data.score
        if update_data.issues is not None:
            update_dict["issues"] = update_data.issues
        if update_data.error_message is not None:
            update_dict["error_message"] = update_data.error_message
            
        if update_dict:
            await db.scan_requests.update_one(
                {"id": scan_id}, 
                {"$set": update_dict}
            )
        
        updated_scan = await db.scan_requests.find_one({"id": scan_id})
        return ScanRequest(**updated_scan)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating scan request {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update scan request")


@router.delete("/scans/{scan_id}")
async def delete_scan_request(scan_id: str):
    """Delete a scan request."""
    try:
        result = await db.scan_requests.delete_one({"id": scan_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Scan request not found")
        return {"message": "Scan request deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting scan request {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete scan request")


@router.get("/scans/{scan_id}/export/pdf")
async def export_scan_pdf(scan_id: str, current_user: User = Depends(get_current_user)):
    """Export scan results as PDF (Pro plan required)."""
    try:
        limits = get_user_scan_limits(current_user.plan)
        if not limits["can_export_pdf"]:
            raise HTTPException(
                status_code=403, 
                detail="PDF export requires Pro plan. Upgrade to access this feature."
            )
        
        scan_data = await db.scan_requests.find_one(
            {"id": scan_id, "user_id": current_user.id}
        )
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        pdf_bytes = await ReportExporter.generate_pdf_report(scan_data)
        
        url_safe = scan_data.get('url', 'scan').replace('https://', '').replace('http://', '').replace('/', '_')
        filename = f"accessibility_report_{url_safe}_{scan_id[:8]}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"PDF export failed for scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")


@router.get("/scans/{scan_id}/export/json")
async def export_scan_json(scan_id: str, current_user: User = Depends(get_current_user)):
    """Export scan results as JSON (available for all plans)."""
    try:
        scan_data = await db.scan_requests.find_one(
            {"id": scan_id, "user_id": current_user.id}
        )
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        json_report = await ReportExporter.generate_json_report(scan_data)
        
        url_safe = scan_data.get('url', 'scan').replace('https://', '').replace('http://', '').replace('/', '_')
        filename = f"accessibility_data_{url_safe}_{scan_id[:8]}.json"
        
        return Response(
            content=json.dumps(json_report, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"JSON export failed for scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate JSON report")


@router.get("/scans/{scan_id}/screenshot")
async def get_scan_screenshot(scan_id: str, current_user: User = Depends(get_current_user)):
    """Get full page screenshot for scan (available for all plans)."""
    try:
        scan_data = await db.scan_requests.find_one(
            {"id": scan_id, "user_id": current_user.id}
        )
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        screenshot_data = scan_data.get('full_page_screenshot')
        if not screenshot_data:
            raise HTTPException(status_code=404, detail="Screenshot not available")
        
        image_bytes = base64.b64decode(screenshot_data)
        
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=scan_{scan_id[:8]}_screenshot.png"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Screenshot retrieval failed for scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve screenshot")


@router.post("/scans/{scan_id}/run-external")
async def run_external_api_scan(scan_id: str):
    """Manually trigger external API scan for a specific scan request."""
    try:
        scan_request = await db.scan_requests.find_one({"id": scan_id})
        if not scan_request:
            raise HTTPException(status_code=404, detail="Scan request not found")
        
        result = await runScanWithExternalApi(scan_id)
        
        if result["success"]:
            return {
                "message": "External API scan completed successfully",
                "scan_id": scan_id,
                "score": result.get("score"),
                "tool": result.get("tool")
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"External API scan failed: {result.get('error', 'Unknown error')}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error running external API scan for {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to run external API scan")


@router.get("/external-apis/status")
async def get_external_apis_status():
    """Get status of external API integrations."""
    return {
        "wave": {
            "configured": bool(settings.WAVE_API_KEY),
            "status": "ready" if settings.WAVE_API_KEY else "api_key_required"
        },
        "equalweb": {
            "configured": bool(settings.EQUALWEB_API_KEY),
            "status": "ready" if settings.EQUALWEB_API_KEY else "api_key_required"
        },
        "accessibe": {
            "configured": bool(settings.ACCESSIBE_API_KEY),
            "status": "ready" if settings.ACCESSIBE_API_KEY else "api_key_required"
        }
    }



# ============================================
# Scan Comparison Endpoint
# ============================================

@router.get("/scans/compare/{scan_id_1}/{scan_id_2}")
async def compare_scans(
    scan_id_1: str,
    scan_id_2: str,
    current_user: User = Depends(get_current_user)
):
    """
    Compare two scans side by side.
    Returns detailed comparison including fixed issues, new issues, and unchanged issues.
    """
    try:
        # Fetch both scans
        scan1 = await db.scan_requests.find_one({
            "id": scan_id_1,
            "user_id": current_user.id
        })
        scan2 = await db.scan_requests.find_one({
            "id": scan_id_2,
            "user_id": current_user.id
        })
        
        if not scan1 or not scan2:
            raise HTTPException(status_code=404, detail="One or both scans not found")
        
        # Determine which scan is older/newer
        scan1_date = scan1.get("createdAt")
        scan2_date = scan2.get("createdAt")
        
        if scan1_date > scan2_date:
            older_scan, newer_scan = scan2, scan1
        else:
            older_scan, newer_scan = scan1, scan2
        
        # Get issues from both scans
        older_issues = older_scan.get("issues", {}).get("failed", [])
        newer_issues = newer_scan.get("issues", {}).get("failed", [])
        
        # Create sets of issue IDs for comparison
        older_issue_ids = {issue.get("id") for issue in older_issues}
        newer_issue_ids = {issue.get("id") for issue in newer_issues}
        
        # Calculate differences
        fixed_issue_ids = older_issue_ids - newer_issue_ids
        new_issue_ids = newer_issue_ids - older_issue_ids
        unchanged_issue_ids = older_issue_ids & newer_issue_ids
        
        # Get full issue details
        fixed_issues = [i for i in older_issues if i.get("id") in fixed_issue_ids]
        new_issues = [i for i in newer_issues if i.get("id") in new_issue_ids]
        unchanged_issues = [i for i in newer_issues if i.get("id") in unchanged_issue_ids]
        
        # Score comparison
        older_score = older_scan.get("score", 0)
        newer_score = newer_scan.get("score", 0)
        score_change = newer_score - older_score
        
        return {
            "comparison": {
                "older_scan": {
                    "id": older_scan.get("id"),
                    "url": older_scan.get("url"),
                    "score": older_score,
                    "createdAt": older_scan.get("createdAt"),
                    "total_failed": len(older_issues),
                    "total_passed": len(older_scan.get("issues", {}).get("passed", [])),
                    "total_incomplete": len(older_scan.get("issues", {}).get("incomplete", []))
                },
                "newer_scan": {
                    "id": newer_scan.get("id"),
                    "url": newer_scan.get("url"),
                    "score": newer_score,
                    "createdAt": newer_scan.get("createdAt"),
                    "total_failed": len(newer_issues),
                    "total_passed": len(newer_scan.get("issues", {}).get("passed", [])),
                    "total_incomplete": len(newer_scan.get("issues", {}).get("incomplete", []))
                },
                "score_change": score_change,
                "score_change_percent": round((score_change / older_score * 100), 1) if older_score > 0 else 0,
                "improved": score_change > 0
            },
            "issues": {
                "fixed": {
                    "count": len(fixed_issues),
                    "items": fixed_issues[:20]  # Limit to 20 for performance
                },
                "new": {
                    "count": len(new_issues),
                    "items": new_issues[:20]
                },
                "unchanged": {
                    "count": len(unchanged_issues),
                    "items": unchanged_issues[:20]
                }
            },
            "summary": {
                "issues_fixed": len(fixed_issues),
                "new_issues": len(new_issues),
                "unchanged_issues": len(unchanged_issues),
                "net_change": len(fixed_issues) - len(new_issues)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error comparing scans: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare scans")
