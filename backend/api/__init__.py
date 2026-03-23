# API Routes module
from fastapi import APIRouter

# Create the main API router with /api prefix
api_router = APIRouter(prefix="/api")

# Import and include sub-routers
from .routes.auth import router as auth_router
from .routes.scans import router as scans_router
from .routes.stripe import router as stripe_router
from .routes.health import router as health_router

api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(scans_router, tags=["Scans"])
api_router.include_router(stripe_router, tags=["Subscription"])
api_router.include_router(health_router, tags=["Health"])

__all__ = ["api_router"]
