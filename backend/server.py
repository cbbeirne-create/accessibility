from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from enum import Enum
import asyncio
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from axe_selenium_python import Axe
import json


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

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


class ScanRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: HttpUrl
    status: ScanStatus = Field(default=ScanStatus.pending)
    score: Optional[int] = Field(default=None, ge=0, le=100)
    issues: Optional[Dict[str, Any]] = Field(default=None)
    tool: Optional[ScanTool] = Field(default=ScanTool.axe_core)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = Field(default=None)


class ScanRequestCreate(BaseModel):
    url: HttpUrl
    tool: Optional[ScanTool] = Field(default=ScanTool.axe_core)


class ScanRequestUpdate(BaseModel):
    status: Optional[ScanStatus] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
    issues: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# Accessibility Scanning Service
class AccessibilityScanner:
    
    @staticmethod
    def setup_chrome_driver():
        """Set up Chrome driver with headless options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--ignore-certificate-errors")
        
        # Use system chromium binary
        chrome_options.binary_location = "/usr/bin/chromium"
        
        try:
            # Use system chromedriver
            service = Service("/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver
        except Exception as e:
            logging.error(f"Failed to setup Chrome driver: {e}")
            raise Exception(f"Chrome driver setup failed: {e}")
    
    @staticmethod
    async def scan_with_axe(url: str) -> Dict[str, Any]:
        """Scan website using axe-core"""
        driver = None
        try:
            # Set up Chrome driver
            driver = AccessibilityScanner.setup_chrome_driver()
            
            # Navigate to the URL
            driver.get(str(url))
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Inject axe-core and run scan
            axe = Axe(driver)
            axe.inject()
            results = axe.run()
            
            # Calculate score based on violations
            score = AccessibilityScanner.calculate_axe_score(results)
            
            return {
                "success": True,
                "score": score,
                "results": results,
                "tool": "axe-core"
            }
            
        except Exception as e:
            logging.error(f"axe-core scan failed for {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": "axe-core"
            }
        finally:
            if driver:
                driver.quit()
    
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
    async def scan_with_wave(url: str, api_key: str) -> Dict[str, Any]:
        """Scan website using WAVE API (placeholder for future implementation)"""
        # TODO: Implement WAVE API integration
        return {
            "success": False,
            "error": "WAVE API integration not yet implemented",
            "tool": "wave"
        }
    
    @staticmethod
    async def scan_with_equalweb(url: str, api_key: str) -> Dict[str, Any]:
        """Scan website using EqualWeb API (placeholder for future implementation)"""
        # TODO: Implement EqualWeb API integration
        return {
            "success": False,
            "error": "EqualWeb API integration not yet implemented",
            "tool": "equalweb"
        }
    
    @staticmethod
    async def scan_with_accessibe(url: str, api_key: str) -> Dict[str, Any]:
        """Scan website using AccessiBe API (placeholder for future implementation)"""
        # TODO: Implement AccessiBe API integration
        return {
            "success": False,
            "error": "AccessiBe API integration not yet implemented", 
            "tool": "accessibe"
        }


async def perform_accessibility_scan(scan_id: str, url: str, tool: ScanTool):
    """Background task to perform accessibility scan"""
    try:
        logging.info(f"Starting accessibility scan for {url} using {tool}")
        
        # Perform the scan based on tool selection
        if tool == ScanTool.axe_core:
            result = await AccessibilityScanner.scan_with_axe(url)
        elif tool == ScanTool.wave:
            api_key = os.getenv("WAVE_API_KEY")
            result = await AccessibilityScanner.scan_with_wave(url, api_key)
        elif tool == ScanTool.equalweb:
            api_key = os.getenv("EQUALWEB_API_KEY")
            result = await AccessibilityScanner.scan_with_equalweb(url, api_key)
        elif tool == ScanTool.accessibe:
            api_key = os.getenv("ACCESSIBE_API_KEY")
            result = await AccessibilityScanner.scan_with_accessibe(url, api_key)
        else:
            result = {"success": False, "error": f"Unknown scan tool: {tool}"}
        
        # Update scan request in database
        if result["success"]:
            await db.scan_requests.update_one(
                {"id": scan_id},
                {"$set": {
                    "status": ScanStatus.completed,
                    "score": result["score"],
                    "issues": result["results"]
                }}
            )
            logging.info(f"Scan completed successfully for {url}")
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


# API Routes
@api_router.get("/")
async def root():
    return {"message": "Accessibility Scanner API", "status": "running"}


@api_router.post("/scans", response_model=ScanRequest)
async def create_scan_request(input: ScanRequestCreate, background_tasks: BackgroundTasks):
    """Create a new accessibility scan request and start scanning"""
    try:
        scan_dict = input.dict()
        scan_dict['url'] = str(scan_dict['url'])  # Convert HttpUrl to string for MongoDB
        scan_obj = ScanRequest(**scan_dict)
        scan_data = scan_obj.dict()
        scan_data['url'] = str(scan_data['url'])  # Ensure URL is string
        
        await db.scan_requests.insert_one(scan_data)
        
        # Start background scanning task
        background_tasks.add_task(
            perform_accessibility_scan,
            scan_obj.id,
            str(input.url),
            input.tool
        )
        
        return scan_obj
    except Exception as e:
        logging.error(f"Error creating scan request: {e}")
        raise HTTPException(status_code=500, detail="Failed to create scan request")


@api_router.get("/scans", response_model=List[ScanRequest])
async def get_scan_requests():
    """Get all scan requests"""
    try:
        scan_requests = await db.scan_requests.find().sort("createdAt", -1).to_list(100)
        return [ScanRequest(**scan_request) for scan_request in scan_requests]
    except Exception as e:
        logging.error(f"Error fetching scan requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan requests")


@api_router.get("/scans/{scan_id}", response_model=ScanRequest)
async def get_scan_request(scan_id: str):
    """Get a specific scan request by ID"""
    try:
        scan_request = await db.scan_requests.find_one({"id": scan_id})
        if not scan_request:
            raise HTTPException(status_code=404, detail="Scan request not found")
        return ScanRequest(**scan_request)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching scan request {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan request")


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