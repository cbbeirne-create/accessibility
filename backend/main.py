"""Auditly FastAPI application entrypoint."""
import logging

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from backend.api import api_router
from backend.core.config import settings
from backend.core.database import close_db_connection, ensure_indexes
from backend.services.rate_limit import enforce_rate_limit

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title='Accessibility Scanner API',
    description='Website accessibility scanning, remediation evidence, monitoring and reporting.',
    version='1.1.0',
    docs_url='/api/docs' if settings.ENVIRONMENT != 'production' else None,
    redoc_url='/api/redoc' if settings.ENVIRONMENT != 'production' else None,
    openapi_url='/api/openapi.json' if settings.ENVIRONMENT != 'production' else None,
)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type'],
)


@app.middleware('http')
async def security_headers(request: Request, call_next):
    path = request.url.path
    if request.method == 'POST':
        if path in {'/api/auth/login', '/api/auth/refresh'}:
            await enforce_rate_limit(request, f'auth:{path}', 20, 60)
        elif path in {'/api/auth/signup', '/api/auth/forgot-password', '/api/auth/resend-verification'}:
            await enforce_rate_limit(request, f'auth:{path}', 5, 300)
        elif path == '/api/scans':
            await enforce_rate_limit(request, 'scan:create', 10, 60)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if settings.ENVIRONMENT == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


@app.on_event('startup')
async def startup_event():
    await ensure_indexes()
    logger.info('Auditly API started')


@app.on_event('shutdown')
async def shutdown_event():
    await close_db_connection()
    logger.info('Auditly API stopped')
