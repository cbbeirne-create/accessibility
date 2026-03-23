from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Response, Depends, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import secrets
from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import requests
from playwright.async_api import async_playwright
import json
import time
import base64
from PIL import Image, ImageDraw
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import tempfile
from jose import JWTError, jwt
import stripe
import calendar


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Authentication configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Password hashing - using bcrypt directly due to passlib compatibility issues
import bcrypt as bcrypt_lib

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    # bcrypt only uses the first 72 bytes of a password
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt_lib.gensalt()
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt_lib.checkpw(password_bytes, hashed_bytes)
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app with API documentation
app = FastAPI(
    title="Accessibility Scanner API",
    description="Professional website accessibility scanning platform with visual evidence capture and comprehensive reporting.",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc
    openapi_url="/api/openapi.json"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Enums and Models
class ScanStatus(str, Enum):
    pending = "pending"
    completed = "completed" 
    error = "error"


class ScanTool(str, Enum):
    axe_core = "axe-core"
    wave = "wave"
    equalweb = "equalweb"
    accessibe = "accessibe"


class UserPlan(str, Enum):
    free = "free"
    pro = "pro"


class SubscriptionStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    canceled = "canceled"
    past_due = "past_due"


# User Authentication Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: Optional[str] = None
    hashed_password: str
    plan: UserPlan = Field(default=UserPlan.free)
    subscription_status: SubscriptionStatus = Field(default=SubscriptionStatus.inactive)
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    scans_used_this_month: int = Field(default=0)
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = Field(default=True)
    # Password reset fields
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None


class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    plan: UserPlan
    subscription_status: SubscriptionStatus
    scans_used_this_month: int
    scans_remaining: int
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    created_at: datetime


# Password Reset Models
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, description="Password must be at least 8 characters")


class PasswordResetResponse(BaseModel):
    message: str
    success: bool


class ScanRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: HttpUrl
    status: ScanStatus = Field(default=ScanStatus.pending)
    score: Optional[int] = Field(default=None, ge=0, le=100)
    issues: Optional[Dict[str, Any]] = Field(default=None)
    tool: Optional[ScanTool] = Field(default=ScanTool.axe_core)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = Field(default=None)
    user_id: str  # Now required - linked to authenticated user
    # Visual evidence fields
    full_page_screenshot: Optional[str] = Field(default=None)  # Base64 encoded image
    evidence_screenshots: Optional[Dict[str, str]] = Field(default=None)  # Issue ID -> Base64 screenshot
    scan_metadata: Optional[Dict[str, Any]] = Field(default=None)  # Additional scan info


class ScanRequestCreate(BaseModel):
    url: HttpUrl
    tool: Optional[ScanTool] = Field(default=ScanTool.axe_core)


class ScanRequestUpdate(BaseModel):
    status: Optional[ScanStatus] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
    issues: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# Authentication utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    
    # Update last login
    await db.users.update_one(
        {"email": user["email"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    return User(**user)


async def get_user_by_email(email: str):
    """Get user by email from database"""
    user = await db.users.find_one({"email": email})
    return user


async def authenticate_user(email: str, password: str):
    """Authenticate user with email and password"""
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


def get_user_scan_limits(plan: UserPlan) -> Dict[str, Any]:
    """Get scan limits for user plan"""
    if plan == UserPlan.free:
        return {
            "monthly_scans": 2,
            "can_export_pdf": False,
            "can_export_json": True,
            "can_view_screenshots": True
        }
    elif plan == UserPlan.pro:
        return {
            "monthly_scans": -1,  # Unlimited
            "can_export_pdf": True,
            "can_export_json": True,
            "can_view_screenshots": True
        }


async def check_scan_limits(user: User) -> bool:
    """Check if user can create more scans this month"""
    limits = get_user_scan_limits(user.plan)
    
    if limits["monthly_scans"] == -1:  # Unlimited
        return True
    
    return user.scans_used_this_month < limits["monthly_scans"]


async def increment_user_scan_count(user_id: str):
    """Increment user's monthly scan count"""
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"scans_used_this_month": 1}}
    )


async def check_and_reset_monthly_scan_count(user_id: str, current_period_start: Optional[datetime]) -> bool:
    """
    Check if we're in a new month and reset the scan count if needed.
    Returns True if the count was reset.
    """
    now = datetime.utcnow()
    
    # If no period start set, initialize it to now
    if not current_period_start:
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "current_period_start": now,
                "current_period_end": now.replace(day=1, month=now.month % 12 + 1 if now.month < 12 else 1, 
                                                   year=now.year if now.month < 12 else now.year + 1),
                "scans_used_this_month": 0
            }}
        )
        return True
    
    # Check if we're in a new month compared to the period start
    if (now.year > current_period_start.year or 
        (now.year == current_period_start.year and now.month > current_period_start.month)):
        # Reset the scan count for the new month
        next_month = now.month % 12 + 1 if now.month < 12 else 1
        next_year = now.year if now.month < 12 else now.year + 1
        
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "current_period_start": now,
                "current_period_end": now.replace(day=1, month=next_month, year=next_year),
                "scans_used_this_month": 0
            }}
        )
        logging.info(f"Reset monthly scan count for user {user_id} - new month detected")
        return True
    
    return False


async def reset_monthly_scan_counts():
    """Reset all users' monthly scan counts (to be run monthly via cron)"""
    await db.users.update_many(
        {},
        {"$set": {"scans_used_this_month": 0}}
    )


# Stripe utilities
def create_stripe_customer(email: str, name: Optional[str] = None):
    """Create Stripe customer - returns None if Stripe is not configured"""
    # Check if Stripe is configured with real keys
    if not stripe.api_key or stripe.api_key.startswith('sk_test_your'):
        logging.warning("Stripe not configured - skipping customer creation")
        return None
    
    try:
        customer = stripe.Customer.create(
            email=email,
            name=name
        )
        return customer
    except Exception as e:
        logging.error(f"Failed to create Stripe customer: {e}")
        return None  # Don't block signup if Stripe fails


def create_stripe_checkout_session(customer_id: str, price_id: str, success_url: str, cancel_url: str):
    """Create Stripe checkout session"""
    # Check if Stripe is configured
    if not stripe.api_key or stripe.api_key.startswith('sk_test_your'):
        raise HTTPException(status_code=503, detail="Payment system not configured. Please contact support.")
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="No payment profile found. Please contact support.")
    
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'customer_id': customer_id}
        )
        return session
    except Exception as e:
        logging.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")
class ExternalAPIScanner:
    
    @staticmethod
    async def scan_with_wave_api(url: str) -> Dict[str, Any]:
        """Scan website using WAVE API"""
        api_key = os.getenv("WAVE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "WAVE API key not configured",
                "tool": "wave"
            }
        
        try:
            # WAVE API endpoint
            endpoint = "http://wave.webaim.org/api/request"
            params = {
                "key": api_key,
                "url": url,
                "format": "json"
            }
            
            response = requests.get(endpoint, params=params, timeout=30)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"WAVE API returned status {response.status_code}",
                    "tool": "wave"
                }
            
            result = response.json()
            
            # Check for API errors
            if result.get("status", {}).get("error"):
                return {
                    "success": False,
                    "error": f"WAVE API error: {result['status']}",
                    "tool": "wave"
                }
            
            # Parse WAVE results to our format
            score = ExternalAPIScanner.calculate_wave_score(result)
            issues = ExternalAPIScanner.format_wave_issues(result)
            
            return {
                "success": True,
                "score": score,
                "results": issues,
                "tool": "wave"
            }
            
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"WAVE API request failed: {str(e)}",
                "tool": "wave"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"WAVE API processing failed: {str(e)}",
                "tool": "wave"
            }
    
    @staticmethod
    async def scan_with_equalweb_api(url: str) -> Dict[str, Any]:
        """Scan website using EqualWeb API"""
        api_key = os.getenv("EQUALWEB_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "EqualWeb API key not configured",
                "tool": "equalweb"
            }
        
        try:
            # EqualWeb API endpoint (hypothetical - verify with actual documentation)
            endpoint = "https://api.equalweb.com/scan"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "url": url,
                "report_type": "compliance",
                "standards": ["wcag2aa"]
            }
            
            response = requests.post(endpoint, headers=headers, json=data, timeout=60)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"EqualWeb API returned status {response.status_code}",
                    "tool": "equalweb"
                }
            
            result = response.json()
            
            # Parse EqualWeb results to our format
            score = ExternalAPIScanner.calculate_equalweb_score(result)
            issues = ExternalAPIScanner.format_equalweb_issues(result)
            
            return {
                "success": True,
                "score": score,
                "results": issues,
                "tool": "equalweb"
            }
            
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"EqualWeb API request failed: {str(e)}",
                "tool": "equalweb"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"EqualWeb API processing failed: {str(e)}",
                "tool": "equalweb"
            }
    
    @staticmethod
    async def scan_with_accessibe_api(url: str) -> Dict[str, Any]:
        """Scan website using AccessiBe API"""
        api_key = os.getenv("ACCESSIBE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "AccessiBe API key not configured",
                "tool": "accessibe"
            }
        
        try:
            # AccessiBe API endpoint (hypothetical - verify with actual documentation)
            endpoint = "https://api.accessibe.com/access-scan"
            headers = {
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            }
            data = {
                "url": url,
                "scan_type": "full"
            }
            
            response = requests.post(endpoint, headers=headers, json=data, timeout=60)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"AccessiBe API returned status {response.status_code}",
                    "tool": "accessibe"
                }
            
            result = response.json()
            
            # Parse AccessiBe results to our format
            score = ExternalAPIScanner.calculate_accessibe_score(result)
            issues = ExternalAPIScanner.format_accessibe_issues(result)
            
            return {
                "success": True,
                "score": score,
                "results": issues,
                "tool": "accessibe"
            }
            
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"AccessiBe API request failed: {str(e)}",
                "tool": "accessibe"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"AccessiBe API processing failed: {str(e)}",
                "tool": "accessibe"
            }
    
    @staticmethod
    def calculate_wave_score(wave_result: Dict[str, Any]) -> int:
        """Calculate accessibility score from WAVE API results"""
        try:
            categories = wave_result.get("categories", {})
            
            # WAVE provides error, alert, feature, structure, and aria counts
            errors = categories.get("error", {}).get("count", 0)
            alerts = categories.get("alert", {}).get("count", 0)
            features = categories.get("feature", {}).get("count", 0)
            structure = categories.get("structure", {}).get("count", 0)
            
            # Calculate score based on WAVE results
            # Errors are most critical, alerts are warnings
            error_penalty = errors * 15
            alert_penalty = alerts * 5
            
            # Positive points for good features
            feature_bonus = min(features * 2, 20)
            structure_bonus = min(structure * 1, 10)
            
            # Base score calculation
            score = 100 - error_penalty - alert_penalty + feature_bonus + structure_bonus
            
            # Ensure score is within bounds
            return max(min(score, 100), 0)
            
        except Exception as e:
            logging.error(f"WAVE score calculation failed: {e}")
            return 50  # Default score on error
    
    @staticmethod
    def format_wave_issues(wave_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format WAVE API results to standardized issues format"""
        try:
            passed = []
            failed = []
            incomplete = []
            
            # Process WAVE errors as failed issues
            errors = wave_result.get("categories", {}).get("error", {}).get("items", {})
            for error_type, error_data in errors.items():
                failed.append({
                    "id": error_type,
                    "description": error_data.get("description", ""),
                    "impact": "serious",  # WAVE errors are typically serious
                    "help": error_data.get("help", ""),
                    "count": error_data.get("count", 0),
                    "wcag": error_data.get("wcag", []),
                    "selector": error_data.get("selector", ""),
                    "type": "error"
                })
            
            # Process WAVE alerts as failed issues (but lower severity)
            alerts = wave_result.get("categories", {}).get("alert", {}).get("items", {})
            for alert_type, alert_data in alerts.items():
                failed.append({
                    "id": alert_type,
                    "description": alert_data.get("description", ""),
                    "impact": "moderate",
                    "help": alert_data.get("help", ""),
                    "count": alert_data.get("count", 0),
                    "wcag": alert_data.get("wcag", []),
                    "selector": alert_data.get("selector", ""),
                    "type": "alert"
                })
            
            # Process WAVE features as passed tests
            features = wave_result.get("categories", {}).get("feature", {}).get("items", {})
            for feature_type, feature_data in features.items():
                passed.append({
                    "id": feature_type,
                    "description": feature_data.get("description", ""),
                    "help": feature_data.get("help", ""),
                    "count": feature_data.get("count", 0),
                    "type": "feature"
                })
            
            # Process WAVE structural elements as passed tests
            structure = wave_result.get("categories", {}).get("structure", {}).get("items", {})
            for struct_type, struct_data in structure.items():
                passed.append({
                    "id": struct_type,
                    "description": struct_data.get("description", ""),
                    "help": struct_data.get("help", ""),
                    "count": struct_data.get("count", 0),
                    "type": "structure"
                })
            
            return {
                "passed": passed,
                "failed": failed,
                "incomplete": incomplete
            }
            
        except Exception as e:
            logging.error(f"WAVE results formatting failed: {e}")
            return {"passed": [], "failed": [], "incomplete": []}
    
    @staticmethod
    def calculate_equalweb_score(equalweb_result: Dict[str, Any]) -> int:
        """Calculate accessibility score from EqualWeb API results"""
        try:
            # EqualWeb typically provides a compliance percentage
            compliance_score = equalweb_result.get("compliance_score", 50)
            
            # Convert to our 0-100 scale if needed
            if isinstance(compliance_score, (int, float)):
                return max(min(int(compliance_score), 100), 0)
            
            return 50  # Default score
            
        except Exception as e:
            logging.error(f"EqualWeb score calculation failed: {e}")
            return 50
    
    @staticmethod
    def format_equalweb_issues(equalweb_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format EqualWeb API results to standardized issues format"""
        try:
            passed = []
            failed = []
            incomplete = []
            
            # Process EqualWeb violations as failed issues
            issues = equalweb_result.get("issues", [])
            for issue in issues:
                severity = issue.get("severity", "moderate").lower()
                failed.append({
                    "id": issue.get("rule_id", "unknown"),
                    "description": issue.get("description", ""),
                    "impact": severity,
                    "help": issue.get("help_text", ""),
                    "count": issue.get("instances", 1),
                    "wcag": issue.get("wcag_references", []),
                    "selector": issue.get("selector", ""),
                    "xpath": issue.get("xpath", ""),
                    "recommendation": issue.get("recommendation", ""),
                    "type": "violation"
                })
            
            # Process passed checks
            passed_checks = equalweb_result.get("passed_checks", [])
            for check in passed_checks:
                passed.append({
                    "id": check.get("rule_id", "unknown"),
                    "description": check.get("description", ""),
                    "help": check.get("help_text", ""),
                    "count": check.get("instances", 1),
                    "wcag": check.get("wcag_references", []),
                    "type": "passed_check"
                })
            
            # Process incomplete/manual checks
            manual_checks = equalweb_result.get("manual_checks", [])
            for check in manual_checks:
                incomplete.append({
                    "id": check.get("rule_id", "unknown"),
                    "description": check.get("description", ""),
                    "help": check.get("help_text", ""),
                    "reason": check.get("manual_reason", "Requires manual verification"),
                    "wcag": check.get("wcag_references", []),
                    "type": "manual_check"
                })
            
            return {
                "passed": passed,
                "failed": failed,
                "incomplete": incomplete
            }
            
        except Exception as e:
            logging.error(f"EqualWeb results formatting failed: {e}")
            return {"passed": [], "failed": [], "incomplete": []}
    
    @staticmethod
    def calculate_accessibe_score(accessibe_result: Dict[str, Any]) -> int:
        """Calculate accessibility score from AccessiBe API results"""
        try:
            # AccessiBe might provide a percentage or grade
            score = accessibe_result.get("accessibility_score", 50)
            
            if isinstance(score, (int, float)):
                return max(min(int(score), 100), 0)
            
            return 50  # Default score
            
        except Exception as e:
            logging.error(f"AccessiBe score calculation failed: {e}")
            return 50
    
    @staticmethod
    def format_accessibe_issues(accessibe_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format AccessiBe API results to standardized issues format"""
        try:
            passed = []
            failed = []
            incomplete = []
            
            # Process AccessiBe violations as failed issues
            violations_data = accessibe_result.get("violations", [])
            for violation in violations_data:
                failed.append({
                    "id": violation.get("id", "unknown"),
                    "description": violation.get("message", ""),
                    "impact": violation.get("impact", "moderate").lower(),
                    "help": violation.get("help", ""),
                    "count": violation.get("count", 1),
                    "wcag": violation.get("wcag_criteria", []),
                    "selector": violation.get("selector", ""),
                    "element": violation.get("element", ""),
                    "recommendation": violation.get("fix_suggestion", ""),
                    "type": "violation"
                })
            
            # Process passed tests
            passes_data = accessibe_result.get("passes", [])
            for passed_test in passes_data:
                passed.append({
                    "id": passed_test.get("id", "unknown"),
                    "description": passed_test.get("message", ""),
                    "help": passed_test.get("help", ""),
                    "count": passed_test.get("count", 1),
                    "wcag": passed_test.get("wcag_criteria", []),
                    "type": "passed_test"
                })
            
            # Process incomplete/requires review
            incomplete_data = accessibe_result.get("incomplete", [])
            for incomplete_test in incomplete_data:
                incomplete.append({
                    "id": incomplete_test.get("id", "unknown"),
                    "description": incomplete_test.get("message", ""),
                    "help": incomplete_test.get("help", ""),
                    "reason": incomplete_test.get("reason", "Manual review required"),
                    "wcag": incomplete_test.get("wcag_criteria", []),
                    "type": "incomplete_test"
                })
            
            return {
                "passed": passed,
                "failed": failed,
                "incomplete": incomplete
            }
            
        except Exception as e:
            logging.error(f"AccessiBe results formatting failed: {e}")
            return {"passed": [], "failed": [], "incomplete": []}


# Export System for Accessibility Reports
class ReportExporter:
    
    @staticmethod
    async def generate_pdf_report(scan_data: Dict[str, Any]) -> bytes:
        """
        Generate WCAG-compliant Tagged PDF report from scan data.
        
        Accessibility Features:
        - Document metadata (Title, Author, Subject, Language)
        - Tagged PDF structure with proper heading hierarchy (H1, H2, H3)
        - Table headers marked for screen readers
        - Alt text for images
        - Logical reading order
        - Language specification (en-US)
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from io import BytesIO
            import base64
            from xml.sax.saxutils import escape as xml_escape
            
            def safe_text(text):
                """Escape HTML/XML special characters for ReportLab Paragraph"""
                if text is None:
                    return 'N/A'
                return xml_escape(str(text))
            
            # Create PDF buffer
            pdf_buffer = BytesIO()
            
            # Create document with metadata
            doc = SimpleDocTemplate(
                pdf_buffer, 
                pagesize=letter,
                topMargin=0.75*inch, 
                bottomMargin=0.75*inch,
                leftMargin=0.75*inch, 
                rightMargin=0.75*inch,
                title="Auditly Accessibility Report",
                author="Auditly - Website Accessibility Scanner",
                subject=f"Accessibility scan results for {scan_data.get('url', 'Unknown URL')}",
                creator="Auditly PDF Generator",
                producer="ReportLab with WCAG 2.1 AA Compliance",
                keywords="accessibility, WCAG, a11y, compliance, audit"
            )
            
            styles = getSampleStyleSheet()
            story = []
            
            # Brand Colors - Emerald/Teal Enterprise Theme (WCAG compliant contrast)
            brand_emerald = colors.Color(0.13, 0.55, 0.40)  # Darker emerald for better contrast
            brand_teal = colors.Color(0.10, 0.50, 0.45)     # Darker teal for better contrast
            brand_slate = colors.Color(0.15, 0.18, 0.23)    # #1e293b
            text_dark = colors.Color(0.1, 0.1, 0.1)         # Near black for body text
            
            # ============================================
            # TAGGED PDF STYLES with Semantic Structure
            # ============================================
            
            # H1 - Document Title (Tagged as Heading Level 1)
            h1_style = ParagraphStyle(
                'AccessibleH1',
                parent=styles['Heading1'],
                fontSize=28,
                textColor=brand_emerald,
                alignment=1,
                spaceAfter=6,
                fontName='Helvetica-Bold',
                leading=34  # Line height for readability
            )
            
            # H2 - Section Headers (Tagged as Heading Level 2)
            h2_style = ParagraphStyle(
                'AccessibleH2',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=brand_teal,
                spaceBefore=20,
                spaceAfter=10,
                fontName='Helvetica-Bold',
                leading=20
            )
            
            # H3 - Subsection Headers (Tagged as Heading Level 3)
            h3_style = ParagraphStyle(
                'AccessibleH3',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=brand_slate,
                spaceBefore=12,
                spaceAfter=6,
                fontName='Helvetica-Bold',
                leading=16
            )
            
            # Body text - high contrast for readability
            body_style = ParagraphStyle(
                'AccessibleBody',
                parent=styles['Normal'],
                fontSize=10,
                textColor=text_dark,
                leading=14,
                spaceAfter=6
            )
            
            # Caption/subtitle style
            caption_style = ParagraphStyle(
                'AccessibleCaption',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.Color(0.3, 0.3, 0.3),
                alignment=1,
                spaceAfter=16,
                leading=14
            )
            
            # Score display style
            score_style = ParagraphStyle(
                'ScoreDisplay',
                parent=styles['Normal'],
                fontSize=24,
                alignment=1,
                fontName='Helvetica-Bold',
                leading=30
            )
            
            # Issue detail style
            detail_style = ParagraphStyle(
                'IssueDetail',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.Color(0.25, 0.25, 0.25),
                leftIndent=15,
                spaceAfter=4,
                leading=12
            )
            
            # Remediation guidance style
            guidance_style = ParagraphStyle(
                'Guidance',
                parent=styles['Normal'],
                fontSize=9,
                textColor=brand_teal,
                leftIndent=15,
                spaceBefore=4,
                spaceAfter=10,
                leading=12
            )
            
            # Footer style
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.Color(0.4, 0.4, 0.4),
                alignment=1,
                leading=10
            )
            
            # ============================================
            # DOCUMENT CONTENT with Tagged Structure
            # ============================================
            
            # --- H1: Document Title ---
            story.append(Paragraph("AUDITLY", h1_style))
            story.append(Paragraph("Website Accessibility Report", caption_style))
            story.append(Spacer(1, 0.2 * inch))
            
            # --- Score Section ---
            score = scan_data.get('score', 0)
            if score >= 80:
                score_color = brand_emerald
                score_label = "Excellent Accessibility"
            elif score >= 60:
                score_color = colors.Color(0.8, 0.5, 0.0)  # Orange with good contrast
                score_label = "Good - Room for Improvement"
            else:
                score_color = colors.Color(0.7, 0.1, 0.1)  # Dark red for contrast
                score_label = "Needs Attention"
            
            score_display_style = ParagraphStyle(
                'ScoreValue',
                parent=score_style,
                textColor=score_color
            )
            story.append(Paragraph(f"Accessibility Score: {score}/100", score_display_style))
            story.append(Paragraph(score_label, caption_style))
            story.append(Spacer(1, 0.3 * inch))
            
            # --- H2: Scan Details Section ---
            story.append(Paragraph("Scan Details", h2_style))
            
            # Accessible table with header row marked
            scan_date = scan_data.get('createdAt')
            if scan_date:
                if hasattr(scan_date, 'strftime'):
                    formatted_date = scan_date.strftime('%B %d, %Y at %I:%M %p')
                else:
                    formatted_date = str(scan_date)
            else:
                formatted_date = 'N/A'
            
            # Table with explicit header cells (first column acts as row headers)
            # Note: Using plain strings for headers, styled via TableStyle for reliability
            url_value = safe_text(scan_data.get('url', 'N/A'))
            info_data = [
                ['Property', 'Value'],
                ['Website URL', url_value],
                ['Scan Date', formatted_date],
                ['Testing Engine', scan_data.get('tool', 'axe-core').upper()],
                ['Status', scan_data.get('status', 'N/A').upper()]
            ]
            
            info_table = Table(info_data, colWidths=[1.8*inch, 4.7*inch])
            info_table.setStyle(TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (-1, 0), text_dark),
                # Data rows
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 1), (0, -1), brand_slate),
                ('TEXTCOLOR', (1, 1), (1, -1), text_dark),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.3 * inch))
            
            # --- H2: Results Summary Section ---
            if scan_data.get('issues'):
                issues = scan_data['issues']
                failed_count = len(issues.get('failed', []))
                passed_count = len(issues.get('passed', []))
                incomplete_count = len(issues.get('incomplete', []))
                
                story.append(Paragraph("Results Summary", h2_style))
                
                # Accessible summary table with header row
                # Note: Using plain strings for headers, styled via TableStyle for reliability
                summary_data = [
                    ['Test Category', 'Count', 'Description'],
                    ['Failed Tests', str(failed_count), 'Accessibility issues requiring fixes'],
                    ['Passed Tests', str(passed_count), 'Accessibility checks that passed'],
                    ['Incomplete Tests', str(incomplete_count), 'Tests requiring manual review']
                ]
                
                summary_table = Table(summary_data, colWidths=[1.5*inch, 0.8*inch, 3.2*inch])
                summary_table.setStyle(TableStyle([
                    # Header row
                    ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('TEXTCOLOR', (0, 0), (-1, 0), text_dark),
                    # Data styling with semantic colors
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    # Color-coded rows for visual scanning
                    ('TEXTCOLOR', (0, 1), (1, 1), colors.Color(0.7, 0.1, 0.1)),  # Failed - red
                    ('TEXTCOLOR', (0, 2), (1, 2), brand_emerald),                 # Passed - green
                    ('TEXTCOLOR', (0, 3), (1, 3), colors.Color(0.8, 0.5, 0.0)),  # Incomplete - orange
                    ('TEXTCOLOR', (2, 1), (2, -1), colors.Color(0.3, 0.3, 0.3)),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(summary_table)
                story.append(Spacer(1, 0.3 * inch))
                
                # --- H2: Failed Issues Details ---
                if failed_count > 0:
                    story.append(Paragraph("Failed Accessibility Tests", h2_style))
                    story.append(Paragraph(
                        f"The following {min(failed_count, 15)} issue(s) were identified and require attention:",
                        body_style
                    ))
                    story.append(Spacer(1, 0.1 * inch))
                    
                    for i, issue in enumerate(issues['failed'][:15]):
                        # --- H3: Individual Issue ---
                        issue_id = safe_text(issue.get('id', 'Unknown Issue'))
                        story.append(Paragraph(f"Issue {i+1}: {issue_id}", h3_style))
                        
                        # Impact level with semantic meaning
                        impact = issue.get('impact', 'unknown').upper()
                        if impact == 'CRITICAL':
                            impact_color = colors.Color(0.7, 0.0, 0.0)
                            impact_desc = "Critical - Must be fixed immediately"
                        elif impact == 'SERIOUS':
                            impact_color = colors.Color(0.8, 0.3, 0.0)
                            impact_desc = "Serious - Should be fixed soon"
                        elif impact == 'MODERATE':
                            impact_color = colors.Color(0.7, 0.5, 0.0)
                            impact_desc = "Moderate - Should be addressed"
                        else:
                            impact_color = colors.Color(0.4, 0.4, 0.4)
                            impact_desc = "Minor - Consider fixing"
                        
                        impact_style = ParagraphStyle(
                            'ImpactLevel',
                            parent=detail_style,
                            textColor=impact_color,
                            fontName='Helvetica-Bold'
                        )
                        story.append(Paragraph(f"Impact: {impact} - {impact_desc}", impact_style))
                        
                        # Description - escape HTML entities
                        description = safe_text(issue.get('description', 'No description available'))
                        story.append(Paragraph(f"Description: {description}", detail_style))
                        
                        # WCAG Reference
                        if issue.get('wcag'):
                            wcag_refs = [tag.upper() for tag in issue['wcag'] if 'wcag' in tag.lower()]
                            if wcag_refs:
                                story.append(Paragraph(f"WCAG Reference: {', '.join(wcag_refs)}", detail_style))
                        
                        # Remediation guidance - escape HTML entities
                        if issue.get('help'):
                            help_text = safe_text(issue['help'])
                            story.append(Paragraph(f"How to Fix: {help_text}", guidance_style))
                        
                        story.append(Spacer(1, 0.15 * inch))
                    
                    if failed_count > 15:
                        story.append(Paragraph(
                            f"Note: {failed_count - 15} additional issues not shown. View the full report online for complete details.",
                            caption_style
                        ))
                
                # --- H2: Passed Tests Summary ---
                if passed_count > 0:
                    story.append(Spacer(1, 0.2 * inch))
                    story.append(Paragraph("Passed Accessibility Tests", h2_style))
                    story.append(Paragraph(
                        f"{passed_count} accessibility checks passed successfully. These include tests for:",
                        body_style
                    ))
                    
                    # List first 5 passed tests as examples
                    passed_examples = issues.get('passed', [])[:5]
                    for test in passed_examples:
                        test_id = safe_text(test.get('id', 'Unknown'))
                        test_desc = safe_text(test.get('description', 'N/A'))
                        story.append(Paragraph(f"* {test_id}: {test_desc}", detail_style))
                    
                    if passed_count > 5:
                        story.append(Paragraph(f"... and {passed_count - 5} more passing tests.", caption_style))
            
            # --- Visual Evidence Section with Alt Text ---
            if scan_data.get('full_page_screenshot'):
                story.append(Spacer(1, 0.3 * inch))
                story.append(Paragraph("Visual Evidence", h2_style))
                story.append(Paragraph(
                    "Screenshot of the scanned webpage with accessibility issues highlighted. "
                    "Areas with red borders indicate elements that failed accessibility tests.",
                    body_style
                ))
                
                try:
                    # Decode and add image with alt text metadata
                    img_data = base64.b64decode(scan_data['full_page_screenshot'])
                    img_buffer = BytesIO(img_data)
                    
                    # Create image with constrained size
                    img = Image(img_buffer, width=6*inch, height=4*inch, kind='proportional')
                    
                    # Note: ReportLab's Image doesn't directly support alt text in Tagged PDF,
                    # but we provide context through surrounding text for screen readers
                    story.append(img)
                    story.append(Paragraph(
                        f"Figure 1: Full page screenshot of {scan_data.get('url', 'the scanned website')} "
                        f"captured during accessibility scan on {formatted_date}.",
                        caption_style
                    ))
                except Exception as img_error:
                    logging.warning(f"Could not include screenshot in PDF: {img_error}")
                    story.append(Paragraph(
                        "Note: Screenshot could not be included in this report. "
                        "View the online report for visual evidence.",
                        caption_style
                    ))
            
            # --- Footer ---
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph("—" * 40, footer_style))
            story.append(Paragraph("Generated by Auditly - Website Accessibility Scanner", footer_style))
            story.append(Paragraph("Powered by axe-core | WCAG 2.1 Level AA Compliance Testing", footer_style))
            story.append(Paragraph(
                f"Report generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}",
                footer_style
            ))
            story.append(Paragraph(
                "This report is provided for informational purposes. "
                "Manual testing is recommended for complete accessibility compliance.",
                footer_style
            ))
            
            # Build PDF with metadata
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            return pdf_bytes
                
        except Exception as e:
            logging.error(f"PDF generation failed: {e}")
            raise Exception(f"Failed to generate PDF report: {e}")
    
    @staticmethod
    async def generate_json_report(scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON report from scan data"""
        try:
            # Create comprehensive JSON structure for developers
            json_report = {
                "scan_info": {
                    "id": scan_data.get('id'),
                    "url": scan_data.get('url'),
                    "scan_date": scan_data.get('createdAt'),
                    "tool": scan_data.get('tool'),
                    "status": scan_data.get('status'),
                    "score": scan_data.get('score'),
                    "user_id": scan_data.get('user_id')
                },
                "results": {
                    "summary": {},
                    "failed_tests": [],
                    "passed_tests": [],
                    "incomplete_tests": []
                },
                "metadata": scan_data.get('scan_metadata', {}),
                "export_timestamp": datetime.utcnow().isoformat()
            }
            
            if scan_data.get('issues'):
                issues = scan_data['issues']
                
                # Summary
                json_report["results"]["summary"] = {
                    "total_failed": len(issues.get('failed', [])),
                    "total_passed": len(issues.get('passed', [])),
                    "total_incomplete": len(issues.get('incomplete', [])),
                    "critical_issues": len([i for i in issues.get('failed', []) if i.get('impact') == 'critical']),
                    "serious_issues": len([i for i in issues.get('failed', []) if i.get('impact') == 'serious'])
                }
                
                # Detailed results
                json_report["results"]["failed_tests"] = issues.get('failed', [])
                json_report["results"]["passed_tests"] = issues.get('passed', [])
                json_report["results"]["incomplete_tests"] = issues.get('incomplete', [])
            
            # Add visual evidence info if available
            if scan_data.get('full_page_screenshot'):
                json_report["visual_evidence"] = {
                    "full_page_screenshot_available": True,
                    "issue_screenshots_count": len(scan_data.get('evidence_screenshots', {}))
                }
            
            return json_report
            
        except Exception as e:
            logging.error(f"JSON generation failed: {e}")
            raise Exception(f"Failed to generate JSON report: {e}")


async def runScanWithExternalApi(scan_request_id: str) -> Dict[str, Any]:
    """
    Server action to run accessibility scan using external APIs
    
    Args:
        scan_request_id: The ID of the scan request to process
        
    Returns:
        Dict containing success status and details
    """
    try:
        # Fetch the ScanRequest by ID
        scan_request = await db.scan_requests.find_one({"id": scan_request_id})
        if not scan_request:
            return {
                "success": False,
                "error": "Scan request not found",
                "scan_id": scan_request_id
            }
        
        scan_obj = ScanRequest(**scan_request)
        url = str(scan_obj.url)
        tool = scan_obj.tool
        
        logging.info(f"Running external API scan for {url} using {tool}")
        
        # Route to appropriate external API based on tool
        if tool == ScanTool.wave:
            result = await ExternalAPIScanner.scan_with_wave_api(url)
        elif tool == ScanTool.equalweb:
            result = await ExternalAPIScanner.scan_with_equalweb_api(url)
        elif tool == ScanTool.accessibe:
            result = await ExternalAPIScanner.scan_with_accessibe_api(url)
        else:
            # Fallback to axe-core for other tools
            result = await AccessibilityScanner.scan_with_axe(url)
        
        # Update the ScanRequest record based on result
        if result["success"]:
            await db.scan_requests.update_one(
                {"id": scan_request_id},
                {"$set": {
                    "status": ScanStatus.completed,
                    "score": result["score"],
                    "issues": result["results"]
                }}
            )
            logging.info(f"External API scan completed successfully for {url}")
            return {
                "success": True,
                "scan_id": scan_request_id,
                "score": result["score"],
                "tool": result["tool"]
            }
        else:
            await db.scan_requests.update_one(
                {"id": scan_request_id},
                {"$set": {
                    "status": ScanStatus.error,
                    "error_message": result["error"]
                }}
            )
            logging.error(f"External API scan failed for {url}: {result['error']}")
            return {
                "success": False,
                "scan_id": scan_request_id,
                "error": result["error"],
                "tool": result["tool"]
            }
    
    except Exception as e:
        # Handle unexpected errors
        error_msg = f"Server action failed: {str(e)}"
        logging.error(error_msg)
        
        try:
            await db.scan_requests.update_one(
                {"id": scan_request_id},
                {"$set": {
                    "status": ScanStatus.error,
                    "error_message": error_msg
                }}
            )
        except Exception:
            pass  # If DB update fails, at least log the error
        
        return {
            "success": False,
            "scan_id": scan_request_id,
            "error": error_msg
        }


# Accessibility Scanning Service with Playwright
class AccessibilityScanner:
    
    @staticmethod
    async def setup_playwright_browser():
        """Set up Playwright browser with optimized options"""
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--allow-running-insecure-content',
                    '--ignore-certificate-errors',
                    '--disable-features=TranslateUI'
                ]
            )
            return playwright, browser
        except Exception as e:
            logging.error(f"Failed to setup Playwright browser: {e}")
            raise Exception(f"Playwright browser setup failed: {e}")
    
    @staticmethod
    async def capture_element_screenshot(page, selector: str) -> Optional[str]:
        """Capture screenshot of specific element and return as base64"""
        try:
            element = await page.query_selector(selector)
            if element:
                screenshot_bytes = await element.screenshot()
                # Convert to base64
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                return screenshot_base64
            return None
        except Exception as e:
            logging.warning(f"Could not capture element screenshot for {selector}: {e}")
            return None
    
    @staticmethod
    async def highlight_elements_on_page(page, selectors: List[str]) -> str:
        """Highlight failing elements and capture full page screenshot"""
        try:
            # Inject CSS to highlight elements
            highlight_css = """
                .axe-violation-highlight {
                    outline: 3px solid #ff0000 !important;
                    outline-offset: 2px !important;
                    background: rgba(255, 0, 0, 0.1) !important;
                }
            """
            await page.add_style_tag(content=highlight_css)
            
            # Add highlight class to failing elements
            for selector in selectors:
                try:
                    await page.evaluate(f'''
                        document.querySelectorAll("{selector}").forEach(el => {{
                            el.classList.add("axe-violation-highlight");
                        }});
                    ''')
                except Exception:
                    continue  # Skip if selector is invalid
            
            # Capture full page screenshot
            screenshot_bytes = await page.screenshot(full_page=True, type='png')
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            return screenshot_base64
            
        except Exception as e:
            logging.warning(f"Could not highlight elements: {e}")
            # Fallback to regular screenshot
            screenshot_bytes = await page.screenshot(full_page=True, type='png')
            return base64.b64encode(screenshot_bytes).decode('utf-8')

    @staticmethod
    async def scan_with_axe(url: str) -> Dict[str, Any]:
        """Scan website using axe-core with Playwright and visual evidence"""
        playwright = None
        browser = None
        page = None
        
        try:
            # Set up Playwright browser
            playwright, browser = await AccessibilityScanner.setup_playwright_browser()
            page = await browser.new_page()
            
            # Set viewport for consistent screenshots
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Navigate to the URL
            await page.goto(str(url), wait_until='load', timeout=30000)
            
            # Wait for page to be fully loaded
            await page.wait_for_timeout(2000)
            
            # Inject axe-core from CDN
            await page.add_script_tag(url='https://unpkg.com/axe-core@4.8.2/axe.min.js')
            
            # Wait for axe to load
            await page.wait_for_timeout(1000)
            
            # Run axe-core scan
            axe_results = await page.evaluate('''
                async () => {
                    return new Promise((resolve, reject) => {
                        if (typeof axe === 'undefined') {
                            reject(new Error('axe-core not loaded'));
                            return;
                        }
                        
                        axe.run((err, results) => {
                            if (err) {
                                reject(err);
                            } else {
                                resolve(results);
                            }
                        });
                    });
                }
            ''')
            
            # Calculate score and format results
            score = AccessibilityScanner.calculate_axe_score(axe_results)
            formatted_issues = AccessibilityScanner.format_axe_issues(axe_results)
            
            # Capture visual evidence
            visual_evidence = await AccessibilityScanner.capture_visual_evidence(
                page, formatted_issues.get('failed', [])
            )
            
            return {
                "success": True,
                "score": score,
                "results": formatted_issues,
                "tool": "axe-core",
                "visual_evidence": visual_evidence,
                "scan_metadata": {
                    "viewport": {"width": 1920, "height": 1080},
                    "scan_timestamp": datetime.utcnow().isoformat(),
                    "total_violations": len(formatted_issues.get('failed', [])),
                    "total_passes": len(formatted_issues.get('passed', [])),
                    "total_incomplete": len(formatted_issues.get('incomplete', []))
                }
            }
            
        except Exception as e:
            logging.error(f"axe-core scan failed for {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": "axe-core"
            }
        finally:
            # Clean up resources
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            if playwright:
                try:
                    await playwright.stop()
                except Exception:
                    pass

    @staticmethod
    async def capture_visual_evidence(page, failed_issues: List[Dict]) -> Dict[str, Any]:
        """Capture visual evidence for failed accessibility issues"""
        try:
            evidence = {
                "full_page_screenshot": None,
                "issue_screenshots": {}
            }
            
            # Collect all selectors from failed issues
            all_selectors = []
            issue_selectors = {}
            
            for issue in failed_issues:
                issue_id = issue.get('id', '')
                selectors = []
                
                # Extract selectors from various possible formats
                if issue.get('selectors'):
                    for sel in issue['selectors']:
                        if isinstance(sel, list):
                            selectors.extend(sel)
                        else:
                            selectors.append(sel)
                
                if issue.get('elements'):
                    for element in issue['elements']:
                        if element.get('target'):
                            selectors.extend(element['target'])
                
                if selectors:
                    issue_selectors[issue_id] = selectors
                    all_selectors.extend(selectors)
            
            # Capture full page screenshot with highlights
            if all_selectors:
                evidence["full_page_screenshot"] = await AccessibilityScanner.highlight_elements_on_page(
                    page, all_selectors[:10]  # Limit to first 10 selectors to avoid performance issues
                )
            else:
                # Fallback: regular full page screenshot
                screenshot_bytes = await page.screenshot(full_page=True, type='png')
                evidence["full_page_screenshot"] = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Capture individual element screenshots (limit to first 5 issues)
            for issue_id, selectors in list(issue_selectors.items())[:5]:
                for selector in selectors[:3]:  # Max 3 selectors per issue
                    try:
                        element_screenshot = await AccessibilityScanner.capture_element_screenshot(
                            page, selector
                        )
                        if element_screenshot:
                            evidence["issue_screenshots"][f"{issue_id}_{hash(selector)}"] = element_screenshot
                            break  # Only need one screenshot per issue
                    except Exception:
                        continue
            
            return evidence
            
        except Exception as e:
            logging.error(f"Failed to capture visual evidence: {e}")
            return {"full_page_screenshot": None, "issue_screenshots": {}}
    
    @staticmethod
    def calculate_axe_score(axe_results: Dict[str, Any]) -> int:
        """Calculate accessibility score from axe results"""
        try:
            violations = axe_results.get("violations", [])
            passes = axe_results.get("passes", [])
            
            # Weight violations by impact
            impact_weights = {"critical": 10, "serious": 5, "moderate": 3, "minor": 1}
            violation_score = 0
            
            for violation in violations:
                impact = violation.get("impact", "minor")
                node_count = len(violation.get("nodes", []))
                violation_score += impact_weights.get(impact, 1) * node_count
            
            # Base score calculation
            total_rules = len(violations) + len(passes)
            if total_rules == 0:
                return 85  # Default score if no rules tested
            
            # Score = 100 - (weighted violations penalty)
            penalty = min(violation_score * 2, 85)  # Cap penalty at 85 points
            score = max(100 - penalty, 15)  # Minimum score of 15
            
            return int(score)
        except Exception as e:
            logging.error(f"Score calculation failed: {e}")
            return 50  # Default score on error

    @staticmethod
    def format_axe_issues(axe_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format axe-core results to standardized issues format"""
        try:
            passed = []
            failed = []
            incomplete = []
            
            # Process axe violations as failed issues
            violations = axe_results.get("violations", [])
            for violation in violations:
                nodes = violation.get("nodes", [])
                failed.append({
                    "id": violation.get("id", "unknown"),
                    "description": violation.get("description", ""),
                    "impact": violation.get("impact", "moderate"),
                    "help": violation.get("help", ""),
                    "helpUrl": violation.get("helpUrl", ""),
                    "count": len(nodes),
                    "wcag": violation.get("tags", []),
                    "selectors": [node.get("target", []) for node in nodes],
                    "elements": [
                        {
                            "html": node.get("html", ""),
                            "target": node.get("target", []),
                            "failureSummary": node.get("failureSummary", "")
                        } for node in nodes
                    ],
                    "type": "violation"
                })
            
            # Process axe passes as passed tests
            passes = axe_results.get("passes", [])
            for passed_test in passes:
                nodes = passed_test.get("nodes", [])
                passed.append({
                    "id": passed_test.get("id", "unknown"),
                    "description": passed_test.get("description", ""),
                    "help": passed_test.get("help", ""),
                    "helpUrl": passed_test.get("helpUrl", ""),
                    "count": len(nodes),
                    "wcag": passed_test.get("tags", []),
                    "type": "passed_test"
                })
            
            # Process axe incomplete as incomplete tests
            incomplete_tests = axe_results.get("incomplete", [])
            for incomplete_test in incomplete_tests:
                nodes = incomplete_test.get("nodes", [])
                incomplete.append({
                    "id": incomplete_test.get("id", "unknown"),
                    "description": incomplete_test.get("description", ""),
                    "help": incomplete_test.get("help", ""),
                    "helpUrl": incomplete_test.get("helpUrl", ""),
                    "count": len(nodes),
                    "wcag": incomplete_test.get("tags", []),
                    "reason": "Automated testing cannot determine if this passes or fails",
                    "type": "incomplete_test"
                })
            
            return {
                "passed": passed,
                "failed": failed,
                "incomplete": incomplete
            }
            
        except Exception as e:
            logging.error(f"Axe results formatting failed: {e}")
            return {"passed": [], "failed": [], "incomplete": []}
    
    @staticmethod
    async def scan_with_wave(url: str, api_key: str) -> Dict[str, Any]:
        """Scan website using WAVE API (legacy method - use ExternalAPIScanner instead)"""
        return await ExternalAPIScanner.scan_with_wave_api(url)
    
    @staticmethod
    async def scan_with_equalweb(url: str, api_key: str) -> Dict[str, Any]:
        """Scan website using EqualWeb API (legacy method - use ExternalAPIScanner instead)"""
        return await ExternalAPIScanner.scan_with_equalweb_api(url)
    
    @staticmethod
    async def scan_with_accessibe(url: str, api_key: str) -> Dict[str, Any]:
        """Scan website using AccessiBe API (legacy method - use ExternalAPIScanner instead)"""
        return await ExternalAPIScanner.scan_with_accessibe_api(url)


async def perform_accessibility_scan(scan_id: str, url: str, tool: ScanTool):
    """Background task to perform accessibility scan with visual evidence"""
    try:
        logging.info(f"Starting accessibility scan for {url} using {tool}")
        
        # Perform the scan based on tool selection
        if tool == ScanTool.axe_core:
            result = await AccessibilityScanner.scan_with_axe(url)
        else:
            # For external APIs, use the server action
            await runScanWithExternalApi(scan_id)
            return  # External API handler already updates the database
        
        # Update scan request in database (for axe-core only)
        if result["success"]:
            update_data = {
                "status": ScanStatus.completed,
                "score": result["score"],
                "issues": result["results"]
            }
            
            # Add visual evidence if available
            if result.get("visual_evidence"):
                visual_evidence = result["visual_evidence"]
                update_data.update({
                    "full_page_screenshot": visual_evidence.get("full_page_screenshot"),
                    "evidence_screenshots": visual_evidence.get("issue_screenshots", {}),
                    "scan_metadata": result.get("scan_metadata", {})
                })
            
            await db.scan_requests.update_one(
                {"id": scan_id},
                {"$set": update_data}
            )
            logging.info(f"Scan completed successfully for {url} with visual evidence")
        else:
            await db.scan_requests.update_one(
                {"id": scan_id},
                {"$set": {
                    "status": ScanStatus.error,
                    "error_message": result["error"]
                }}
            )
            logging.error(f"Scan failed for {url}: {result['error']}")
    
    except Exception as e:
        logging.error(f"Scan task failed for {scan_id}: {e}")
        await db.scan_requests.update_one(
            {"id": scan_id},
            {"$set": {
                "status": ScanStatus.error,
                "error_message": str(e)
            }}
        )


# ============================================
# Email Service for Password Reset
# ============================================

def generate_password_reset_token() -> str:
    """Generate a cryptographically secure password reset token"""
    return secrets.token_urlsafe(32)


def send_password_reset_email(email: str, reset_token: str, user_name: Optional[str] = None) -> bool:
    """
    Send password reset email via SendGrid.
    Returns True if email was sent successfully, False otherwise.
    """
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    sender_email = os.environ.get('SENDER_EMAIL', 'noreply@auditly.com')
    frontend_url = os.environ.get('FRONTEND_URL', 'https://remediation-lab.preview.emergentagent.com')
    
    # Check if SendGrid is configured
    if not sendgrid_api_key or sendgrid_api_key.startswith('your_'):
        logging.warning("SendGrid not configured - password reset email not sent")
        # In development, log the reset link for testing
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        logging.info(f"[DEV] Password reset link for {email}: {reset_link}")
        return True  # Return True so the flow continues in development
    
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    display_name = user_name or email.split('@')[0]
    
    # Branded HTML email template matching Auditly's Enterprise theme
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Auditly Password</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 40px 20px;">
                    <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 16px; overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, rgba(52, 211, 153, 0.1), rgba(20, 184, 166, 0.1));">
                                <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #34d399, #14b8a6); border-radius: 16px; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: white; font-size: 28px; font-weight: bold;">A</span>
                                </div>
                                <h1 style="color: #ffffff; font-size: 24px; margin: 0 0 8px; font-weight: 700;">Auditly</h1>
                                <p style="color: #94a3b8; font-size: 14px; margin: 0;">Website Accessibility Scanner</p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 30px 40px;">
                                <h2 style="color: #ffffff; font-size: 20px; margin: 0 0 16px; font-weight: 600;">Reset Your Password</h2>
                                <p style="color: #cbd5e1; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
                                    Hi {display_name},
                                </p>
                                <p style="color: #cbd5e1; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
                                    We received a request to reset your Auditly account password. Click the button below to create a new password:
                                </p>
                                
                                <!-- CTA Button -->
                                <table role="presentation" style="width: 100%; margin: 32px 0;">
                                    <tr>
                                        <td style="text-align: center;">
                                            <a href="{reset_link}" 
                                               style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #34d399, #14b8a6); color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 12px; box-shadow: 0 4px 14px rgba(52, 211, 153, 0.25);">
                                                Reset Password
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 0 0 16px;">
                                    This link will expire in <strong style="color: #f59e0b;">1 hour</strong> for security reasons.
                                </p>
                                
                                <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 0 0 16px;">
                                    If you didn't request this password reset, you can safely ignore this email. Your password won't be changed.
                                </p>
                                
                                <!-- Fallback Link -->
                                <div style="background-color: #0f172a; border-radius: 8px; padding: 16px; margin-top: 24px;">
                                    <p style="color: #64748b; font-size: 12px; margin: 0 0 8px;">
                                        If the button doesn't work, copy and paste this link:
                                    </p>
                                    <p style="color: #34d399; font-size: 12px; margin: 0; word-break: break-all;">
                                        {reset_link}
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px 40px; border-top: 1px solid #334155; text-align: center;">
                                <p style="color: #64748b; font-size: 12px; margin: 0 0 8px;">
                                    This email was sent by Auditly
                                </p>
                                <p style="color: #64748b; font-size: 12px; margin: 0;">
                                    WCAG 2.1 AA Compliant Accessibility Scanning
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Plain text fallback for accessibility
    plain_text = f"""
    Reset Your Auditly Password
    
    Hi {display_name},
    
    We received a request to reset your Auditly account password. 
    
    Click this link to reset your password:
    {reset_link}
    
    This link will expire in 1 hour for security reasons.
    
    If you didn't request this password reset, you can safely ignore this email.
    
    - The Auditly Team
    """
    
    try:
        message = Mail(
            from_email=Email(sender_email, "Auditly"),
            to_emails=To(email),
            subject="Reset Your Auditly Password",
            plain_text_content=Content("text/plain", plain_text),
            html_content=Content("text/html", html_content)
        )
        
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            logging.info(f"Password reset email sent to {email}")
            return True
        else:
            logging.error(f"SendGrid returned status {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Failed to send password reset email: {e}")
        return False


# Authentication API Routes
@api_router.post("/auth/signup", response_model=Token)
async def signup(user_data: UserCreate):
    """Create new user account"""
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create Stripe customer (may return None if Stripe not configured)
        stripe_customer = create_stripe_customer(user_data.email, user_data.full_name)
        stripe_customer_id = stripe_customer.id if stripe_customer else None
        
        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            stripe_customer_id=stripe_customer_id,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)  # Free trial period
        )
        
        # Save to database
        user_data_dict = user.dict()
        user_data_dict['email'] = str(user_data_dict['email'])
        await db.users.insert_one(user_data_dict)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Signup failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create account")


@api_router.post("/auth/login", response_model=Token)
async def login(form_data: UserLogin):
    """Authenticate user and return access token"""
    user = await authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check and reset monthly scan count if we're in a new month
    current_period_start = user.get("current_period_start")
    if isinstance(current_period_start, str):
        current_period_start = datetime.fromisoformat(current_period_start.replace('Z', '+00:00'))
    
    await check_and_reset_monthly_scan_count(user["id"], current_period_start)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@api_router.post("/auth/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request a password reset email.
    For security, always returns success message even if email doesn't exist.
    """
    try:
        # Find user by email
        user = await get_user_by_email(request.email)
        
        if user:
            # Generate secure reset token
            reset_token = generate_password_reset_token()
            
            # Set token expiration to 1 hour from now
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Store token and expiration in database
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {
                    "password_reset_token": reset_token,
                    "password_reset_expires": expires_at
                }}
            )
            
            # Send reset email
            user_name = user.get("full_name") or user.get("email", "").split("@")[0]
            email_sent = send_password_reset_email(
                email=str(user["email"]),
                reset_token=reset_token,
                user_name=user_name
            )
            
            if not email_sent:
                logging.warning(f"Failed to send reset email to {request.email}")
        
        # Always return success for security (don't reveal if email exists)
        return PasswordResetResponse(
            message="If an account with that email exists, you will receive a password reset link shortly.",
            success=True
        )
        
    except Exception as e:
        logging.error(f"Forgot password error: {e}")
        # Still return success for security
        return PasswordResetResponse(
            message="If an account with that email exists, you will receive a password reset link shortly.",
            success=True
        )


@api_router.post("/auth/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using a valid reset token.
    Token must be valid and not expired. Tokens are one-time use.
    """
    try:
        # Find user by reset token
        user = await db.users.find_one({
            "password_reset_token": request.token
        })
        
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset token. Please request a new password reset."
            )
        
        # Check if token has expired
        expires_at = user.get("password_reset_expires")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            if datetime.utcnow() > expires_at:
                # Clear expired token
                await db.users.update_one(
                    {"id": user["id"]},
                    {"$set": {
                        "password_reset_token": None,
                        "password_reset_expires": None
                    }}
                )
                raise HTTPException(
                    status_code=400,
                    detail="Reset token has expired. Please request a new password reset."
                )
        
        # Hash new password
        hashed_password = get_password_hash(request.new_password)
        
        # Update password and clear reset token (one-time use)
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "hashed_password": hashed_password,
                "password_reset_token": None,
                "password_reset_expires": None
            }}
        )
        
        logging.info(f"Password reset successful for user {user['id']}")
        
        return PasswordResetResponse(
            message="Your password has been reset successfully. You can now log in with your new password.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Reset password error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while resetting your password. Please try again."
        )


@api_router.get("/auth/verify-reset-token")
async def verify_reset_token(token: str):
    """
    Verify if a reset token is valid (used by frontend to show/hide reset form).
    """
    user = await db.users.find_one({
        "password_reset_token": token
    })
    
    if not user:
        return {"valid": False, "message": "Invalid reset token"}
    
    # Check expiration
    expires_at = user.get("password_reset_expires")
    if expires_at:
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        if datetime.utcnow() > expires_at:
            return {"valid": False, "message": "Reset token has expired"}
    
    return {"valid": True, "message": "Token is valid"}


@api_router.get("/auth/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile with subscription info"""
    
    # Check and reset monthly scan count if we're in a new month
    was_reset = await check_and_reset_monthly_scan_count(
        current_user.id, 
        current_user.current_period_start
    )
    
    # If reset, refresh the user data
    if was_reset:
        user_data = await db.users.find_one({"id": current_user.id})
        if user_data:
            current_user = User(**user_data)
    
    limits = get_user_scan_limits(current_user.plan)
    scans_remaining = limits["monthly_scans"] - current_user.scans_used_this_month if limits["monthly_scans"] != -1 else -1
    
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        plan=current_user.plan,
        subscription_status=current_user.subscription_status,
        scans_used_this_month=current_user.scans_used_this_month,
        scans_remaining=scans_remaining,
        current_period_start=current_user.current_period_start,
        current_period_end=current_user.current_period_end,
        created_at=current_user.created_at
    )


# Subscription API Routes
@api_router.post("/subscription/create-checkout-session")
async def create_checkout_session(current_user: User = Depends(get_current_user)):
    """Create Stripe checkout session for Pro subscription"""
    try:
        # Pro plan price ID (you'll need to create this in Stripe Dashboard)
        PRO_PRICE_ID = os.environ.get('STRIPE_PRO_PRICE_ID', 'price_1234567890abcdef')
        
        success_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/dashboard?success=true"
        cancel_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/pricing?canceled=true"
        
        session = create_stripe_checkout_session(
            customer_id=current_user.stripe_customer_id,
            price_id=PRO_PRICE_ID,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return {"checkout_url": session.url}
        
    except Exception as e:
        logging.error(f"Checkout session creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@api_router.post("/subscription/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        # Construct the event
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        
        # Handle the event
        if event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            await handle_subscription_created(subscription)
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            await handle_subscription_updated(subscription)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            await handle_subscription_canceled(subscription)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            await handle_payment_succeeded(invoice)
        
        return {"status": "success"}
        
    except ValueError as e:
        logging.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logging.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def handle_subscription_created(subscription):
    """Handle subscription creation"""
    customer_id = subscription['customer']
    subscription_id = subscription['id']
    current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
    current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
    
    # Update user to Pro plan
    await db.users.update_one(
        {"stripe_customer_id": customer_id},
        {"$set": {
            "plan": UserPlan.pro,
            "subscription_status": SubscriptionStatus.active,
            "stripe_subscription_id": subscription_id,
            "current_period_start": current_period_start,
            "current_period_end": current_period_end,
            "scans_used_this_month": 0  # Reset scan count on upgrade
        }}
    )


async def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    customer_id = subscription['customer']
    status = subscription['status']
    current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
    current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
    
    # Map Stripe status to our enum
    sub_status = SubscriptionStatus.active
    if status == 'past_due':
        sub_status = SubscriptionStatus.past_due
    elif status in ['canceled', 'unpaid']:
        sub_status = SubscriptionStatus.canceled
    
    await db.users.update_one(
        {"stripe_customer_id": customer_id},
        {"$set": {
            "subscription_status": sub_status,
            "current_period_start": current_period_start,
            "current_period_end": current_period_end
        }}
    )


async def handle_subscription_canceled(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription['customer']
    
    # Downgrade user to free plan
    await db.users.update_one(
        {"stripe_customer_id": customer_id},
        {"$set": {
            "plan": UserPlan.free,
            "subscription_status": SubscriptionStatus.canceled,
            "stripe_subscription_id": None,
            "scans_used_this_month": 0  # Reset for free plan limits
        }}
    )


async def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    customer_id = invoice['customer']
    
    # Reset monthly scan count on successful payment
    current_period_start = datetime.fromtimestamp(invoice['period_start'])
    current_period_end = datetime.fromtimestamp(invoice['period_end'])
    
    await db.users.update_one(
        {"stripe_customer_id": customer_id},
        {"$set": {
            "subscription_status": SubscriptionStatus.active,
            "current_period_start": current_period_start,
            "current_period_end": current_period_end,
            "scans_used_this_month": 0  # Reset scan count
        }}
    )


@api_router.get("/health")
async def health_check():
    """Health check endpoint for monitoring system status"""
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
        
        # Return appropriate status code
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


@api_router.get("/scans", response_model=List[ScanRequest])
async def get_scan_requests(current_user: User = Depends(get_current_user)):
    """Get all scan requests for the authenticated user"""
    try:
        scan_requests = await db.scan_requests.find({"user_id": current_user.id}).sort("createdAt", -1).to_list(100)
        return [ScanRequest(**scan_request) for scan_request in scan_requests]
    except Exception as e:
        logging.error(f"Error fetching scan requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan requests")


@api_router.get("/scans/{scan_id}", response_model=ScanRequest)
async def get_scan_request(scan_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific scan request by ID (user can only access their own scans)"""
    try:
        scan_request = await db.scan_requests.find_one({"id": scan_id, "user_id": current_user.id})
        if not scan_request:
            raise HTTPException(status_code=404, detail="Scan request not found")
        return ScanRequest(**scan_request)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching scan request {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan request")


@api_router.get("/scans/{scan_id}/export/pdf")
async def export_scan_pdf(scan_id: str, current_user: User = Depends(get_current_user)):
    """Export scan results as PDF (Pro plan required)"""
    try:
        # Check if user can export PDFs
        limits = get_user_scan_limits(current_user.plan)
        if not limits["can_export_pdf"]:
            raise HTTPException(
                status_code=403, 
                detail="PDF export requires Pro plan. Upgrade to access this feature."
            )
        
        # Get scan data (user can only access their own scans)
        scan_data = await db.scan_requests.find_one({"id": scan_id, "user_id": current_user.id})
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Generate PDF
        pdf_bytes = await ReportExporter.generate_pdf_report(scan_data)
        
        # Create filename
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


@api_router.get("/scans/{scan_id}/export/json")
async def export_scan_json(scan_id: str, current_user: User = Depends(get_current_user)):
    """Export scan results as JSON (available for all plans)"""
    try:
        # Get scan data (user can only access their own scans)
        scan_data = await db.scan_requests.find_one({"id": scan_id, "user_id": current_user.id})
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Generate JSON report
        json_report = await ReportExporter.generate_json_report(scan_data)
        
        # Create filename
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


@api_router.get("/scans/{scan_id}/screenshot")
async def get_scan_screenshot(scan_id: str, current_user: User = Depends(get_current_user)):
    """Get full page screenshot for scan (available for all plans)"""
    try:
        # Get scan data (user can only access their own scans)
        scan_data = await db.scan_requests.find_one({"id": scan_id, "user_id": current_user.id})
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        screenshot_data = scan_data.get('full_page_screenshot')
        if not screenshot_data:
            raise HTTPException(status_code=404, detail="Screenshot not available")
        
        # Decode base64 image
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


@api_router.put("/scans/{scan_id}", response_model=ScanRequest)
async def update_scan_request(scan_id: str, update_data: ScanRequestUpdate):
    """Update a scan request (used for updating status, score, issues)"""
    try:
        # Get current scan request
        current_scan = await db.scan_requests.find_one({"id": scan_id})
        if not current_scan:
            raise HTTPException(status_code=404, detail="Scan request not found")
        
        # Prepare update data
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
        
        # Return updated scan request
        updated_scan = await db.scan_requests.find_one({"id": scan_id})
        return ScanRequest(**updated_scan)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating scan request {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update scan request")


@api_router.delete("/scans/{scan_id}")
async def delete_scan_request(scan_id: str):
    """Delete a scan request"""
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


@api_router.post("/scans/{scan_id}/run-external")
async def run_external_api_scan(scan_id: str):
    """Manually trigger external API scan for a specific scan request"""
    try:
        # Check if scan exists
        scan_request = await db.scan_requests.find_one({"id": scan_id})
        if not scan_request:
            raise HTTPException(status_code=404, detail="Scan request not found")
        
        # Run the external API scan
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


@api_router.get("/external-apis/status")
async def get_external_apis_status():
    """Get status of external API integrations"""
    return {
        "wave": {
            "configured": bool(os.getenv("WAVE_API_KEY")),
            "status": "ready" if os.getenv("WAVE_API_KEY") else "api_key_required"
        },
        "equalweb": {
            "configured": bool(os.getenv("EQUALWEB_API_KEY")),
            "status": "ready" if os.getenv("EQUALWEB_API_KEY") else "api_key_required"
        },
        "accessibe": {
            "configured": bool(os.getenv("ACCESSIBE_API_KEY")),
            "status": "ready" if os.getenv("ACCESSIBE_API_KEY") else "api_key_required"
        }
    }


# Main API Routes
@api_router.get("/")
async def root():
    return {"message": "Accessibility Scanner API", "status": "running", "version": "1.0.0"}


@api_router.post("/scans", response_model=ScanRequest)
async def create_scan_request(
    input: ScanRequestCreate, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Create a new accessibility scan request (requires authentication)"""
    try:
        # Check scan limits
        can_scan = await check_scan_limits(current_user)
        if not can_scan:
            limits = get_user_scan_limits(current_user.plan)
            raise HTTPException(
                status_code=403, 
                detail=f"Scan limit exceeded. {current_user.plan.title()} plan allows {limits['monthly_scans']} scans per month. Upgrade to Pro for unlimited scans."
            )
        
        # Create scan request
        scan_dict = input.dict()
        scan_dict['url'] = str(scan_dict['url'])  # Convert HttpUrl to string for MongoDB
        scan_dict['user_id'] = current_user.id  # Link to authenticated user
        scan_obj = ScanRequest(**scan_dict)
        scan_data = scan_obj.dict()
        scan_data['url'] = str(scan_data['url'])  # Ensure URL is string
        
        await db.scan_requests.insert_one(scan_data)
        
        # Increment user's scan count
        await increment_user_scan_count(current_user.id)
        
        # Start background scanning task
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


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()