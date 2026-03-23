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


async def check_scan_limits(user: User) -> bool:
    """Check if user can create more scans this month."""
    limits = get_user_scan_limits(user.plan)
    if limits["monthly_scans"] == -1:
        return True
    return user.scans_used_this_month < limits["monthly_scans"]


async def increment_user_scan_count(user_id: str):
    """Increment user's monthly scan count."""
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"scans_used_this_month": 1}}
    )


@router.get("/scans", response_model=List[ScanRequest])
async def get_scan_requests(current_user: User = Depends(get_current_user)):
    """Get all scan requests for the authenticated user."""
    try:
        scan_requests = await db.scan_requests.find(
            {"user_id": current_user.id}
        ).sort("createdAt", -1).to_list(100)
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
            limits = get_user_scan_limits(current_user.plan)
            raise HTTPException(
                status_code=403, 
                detail=f"Scan limit exceeded. {current_user.plan.title()} plan allows {limits['monthly_scans']} scans per month. Upgrade to Pro for unlimited scans."
            )
        
        scan_dict = input.dict()
        scan_dict['url'] = str(scan_dict['url'])
        scan_dict['user_id'] = current_user.id
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
