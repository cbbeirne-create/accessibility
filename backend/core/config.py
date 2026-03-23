"""
Application configuration and settings.
Loads environment variables and provides centralized config access.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')


class Settings:
    """Application settings loaded from environment variables."""
    
    # MongoDB
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'auditly')
    
    # JWT Authentication
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 days
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.environ.get('STRIPE_WEBHOOK_SECRET')
    STRIPE_PRO_PRICE_ID: str = os.environ.get('STRIPE_PRO_PRICE_ID', 'price_1234567890abcdef')
    
    # SendGrid
    SENDGRID_API_KEY: Optional[str] = os.environ.get('SENDGRID_API_KEY')
    SENDER_EMAIL: str = os.environ.get('SENDER_EMAIL', 'noreply@auditly.com')
    
    # Frontend URL (for email links, CORS, etc.)
    FRONTEND_URL: str = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    # External API Keys
    WAVE_API_KEY: Optional[str] = os.environ.get('WAVE_API_KEY')
    EQUALWEB_API_KEY: Optional[str] = os.environ.get('EQUALWEB_API_KEY')
    ACCESSIBE_API_KEY: Optional[str] = os.environ.get('ACCESSIBE_API_KEY')


# Global settings instance
settings = Settings()
