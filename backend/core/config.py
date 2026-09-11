"""Application configuration and settings."""
import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")


def _csv_env(name: str, default: str = "") -> List[str]:
    return [value.strip() for value in os.environ.get(name, default).split(",") if value.strip()]


class Settings:
    """Application settings loaded from environment variables."""

    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development").lower()

    # MongoDB
    MONGO_URL: str = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.environ.get("DB_NAME", "auditly")

    # Authentication
    SECRET_KEY: Optional[str] = os.environ.get("SECRET_KEY")
    ALGORITHM: str = "HS256"
    JWT_ISSUER: str = os.environ.get("JWT_ISSUER", "auditly-api")
    JWT_AUDIENCE: str = os.environ.get("JWT_AUDIENCE", "auditly-web")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    REFRESH_COOKIE_NAME: str = os.environ.get("REFRESH_COOKIE_NAME", "auditly_refresh")
    REFRESH_COOKIE_SECURE: bool = os.environ.get("REFRESH_COOKIE_SECURE", "true").lower() == "true"

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = os.environ.get("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.environ.get("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.environ.get("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRO_PRICE_ID: Optional[str] = os.environ.get("STRIPE_PRO_PRICE_ID")

    # SendGrid
    SENDGRID_API_KEY: Optional[str] = os.environ.get("SENDGRID_API_KEY")
    SENDER_EMAIL: str = os.environ.get("SENDER_EMAIL", "noreply@auditly.com")

    # Frontend / CORS
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    ALLOWED_ORIGINS: List[str] = _csv_env("ALLOWED_ORIGINS", FRONTEND_URL)

    # Scanner safety limits
    SCAN_NAVIGATION_TIMEOUT_MS: int = int(os.environ.get("SCAN_NAVIGATION_TIMEOUT_MS", "30000"))
    SCAN_MAX_REDIRECTS: int = int(os.environ.get("SCAN_MAX_REDIRECTS", "5"))
    SCAN_ALLOWED_PORTS: List[int] = [int(p) for p in _csv_env("SCAN_ALLOWED_PORTS", "80,443")]

    # External API Keys
    WAVE_API_KEY: Optional[str] = os.environ.get("WAVE_API_KEY")
    EQUALWEB_API_KEY: Optional[str] = os.environ.get("EQUALWEB_API_KEY")
    ACCESSIBE_API_KEY: Optional[str] = os.environ.get("ACCESSIBE_API_KEY")

    def validate_runtime(self) -> None:
        """Fail fast when production-critical settings are unsafe or missing."""
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            raise RuntimeError("SECRET_KEY must be configured with at least 32 characters")
        if self.ENVIRONMENT == "production":
            if any(origin == "*" for origin in self.ALLOWED_ORIGINS):
                raise RuntimeError("Wildcard CORS origins are forbidden in production")
            if not self.FRONTEND_URL.startswith("https://"):
                raise RuntimeError("FRONTEND_URL must use HTTPS in production")
            if not self.REFRESH_COOKIE_SECURE:
                raise RuntimeError("Refresh cookies must be Secure in production")


settings = Settings()
