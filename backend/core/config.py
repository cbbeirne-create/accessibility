"""Application configuration and validation."""
import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')


def _csv(name: str, default: str = "") -> List[str]:
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


class Settings:
    """Application settings loaded from environment variables."""

    ENVIRONMENT: str = os.environ.get('ENVIRONMENT', 'development').lower()

    # MongoDB
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'auditly')

    # JWT / sessions
    SECRET_KEY: str = os.environ.get('SECRET_KEY', '')
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', '20'))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS', '30'))
    JWT_ISSUER: str = os.environ.get('JWT_ISSUER', 'auditly-api')
    JWT_AUDIENCE: str = os.environ.get('JWT_AUDIENCE', 'auditly-web')
    REFRESH_COOKIE_NAME: str = os.environ.get('REFRESH_COOKIE_NAME', 'auditly_refresh')
    COOKIE_SECURE: bool = os.environ.get('COOKIE_SECURE', 'true' if ENVIRONMENT == 'production' else 'false').lower() == 'true'
    COOKIE_SAMESITE: str = os.environ.get('COOKIE_SAMESITE', 'lax')
    COOKIE_DOMAIN: Optional[str] = os.environ.get('COOKIE_DOMAIN') or None

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.environ.get('STRIPE_WEBHOOK_SECRET')
    STRIPE_PRO_PRICE_ID: Optional[str] = os.environ.get('STRIPE_PRO_PRICE_ID')

    # Email
    SENDGRID_API_KEY: Optional[str] = os.environ.get('SENDGRID_API_KEY')
    SENDER_EMAIL: str = os.environ.get('SENDER_EMAIL', 'noreply@auditly.com')

    # Frontend / CORS
    FRONTEND_URL: str = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    CORS_ALLOWED_ORIGINS: List[str] = _csv('CORS_ALLOWED_ORIGINS', FRONTEND_URL)

    # External scanners
    WAVE_API_KEY: Optional[str] = os.environ.get('WAVE_API_KEY')
    EQUALWEB_API_KEY: Optional[str] = os.environ.get('EQUALWEB_API_KEY')
    ACCESSIBE_API_KEY: Optional[str] = os.environ.get('ACCESSIBE_API_KEY')

    # Scanner safety/runtime
    SCAN_ALLOWED_PORTS: List[int] = [int(p) for p in _csv('SCAN_ALLOWED_PORTS', '80,443')]
    SCAN_NAVIGATION_TIMEOUT_MS: int = int(os.environ.get('SCAN_NAVIGATION_TIMEOUT_MS', '30000'))
    SCAN_MAX_REDIRECTS: int = int(os.environ.get('SCAN_MAX_REDIRECTS', '8'))
    MAX_CONCURRENT_SCANS: int = int(os.environ.get('MAX_CONCURRENT_SCANS', '2'))
    AXE_CORE_PATH: str = os.environ.get('AXE_CORE_PATH', str(ROOT_DIR / 'node_modules' / 'axe-core' / 'axe.min.js'))

    # Object storage (optional; DB base64 fallback remains for development)
    S3_BUCKET: Optional[str] = os.environ.get('S3_BUCKET')
    S3_REGION: Optional[str] = os.environ.get('S3_REGION')
    S3_ENDPOINT_URL: Optional[str] = os.environ.get('S3_ENDPOINT_URL')
    S3_PUBLIC_BASE_URL: Optional[str] = os.environ.get('S3_PUBLIC_BASE_URL')

    def validate(self) -> None:
        if self.ENVIRONMENT == 'production':
            if not self.SECRET_KEY or self.SECRET_KEY == 'your-secret-key-change-in-production' or len(self.SECRET_KEY) < 32:
                raise RuntimeError('SECRET_KEY must be set to a strong value (>=32 chars) in production')
            if not self.CORS_ALLOWED_ORIGINS or '*' in self.CORS_ALLOWED_ORIGINS:
                raise RuntimeError('CORS_ALLOWED_ORIGINS must contain explicit origins in production')
            if self.COOKIE_SAMESITE not in {'lax', 'strict', 'none'}:
                raise RuntimeError('COOKIE_SAMESITE must be lax, strict, or none')
            if not self.STRIPE_PRO_PRICE_ID and self.STRIPE_SECRET_KEY:
                raise RuntimeError('STRIPE_PRO_PRICE_ID is required when Stripe is configured')
        elif not self.SECRET_KEY:
            self.SECRET_KEY = os.urandom(32).hex()


settings = Settings()
settings.validate()
