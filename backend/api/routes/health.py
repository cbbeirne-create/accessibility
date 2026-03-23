"""
Health check API routes.
"""
import json
from datetime import datetime

from fastapi import APIRouter, Response

from ...core.database import db
from ...services.playwright_engine import AccessibilityScanner

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring system status."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "unknown",
                "playwright": "unknown"
            },
            "version": "1.0.0"
        }
        
        # Check database connection
        try:
            await db.scan_requests.find_one()
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check Playwright browser availability
        try:
            playwright, browser = await AccessibilityScanner.setup_playwright_browser()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
            health_status["services"]["playwright"] = "healthy"
        except Exception as e:
            health_status["services"]["playwright"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return Response(
            content=json.dumps(health_status, indent=2),
            status_code=status_code,
            media_type="application/json"
        )
        
    except Exception as e:
        error_response = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "1.0.0"
        }
        return Response(
            content=json.dumps(error_response, indent=2),
            status_code=503,
            media_type="application/json"
        )


@router.get("/")
async def root():
    """API root endpoint."""
    return {"message": "Accessibility Scanner API", "status": "running", "version": "1.0.0"}
