from fastapi import FastAPI, APIRouter, HTTPException
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


class ScanRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: HttpUrl
    status: ScanStatus = Field(default=ScanStatus.pending)
    score: Optional[int] = Field(default=None, ge=0, le=100)
    issues: Optional[Dict[str, Any]] = Field(default=None)
    createdAt: datetime = Field(default_factory=datetime.utcnow)


class ScanRequestCreate(BaseModel):
    url: HttpUrl


class ScanRequestUpdate(BaseModel):
    status: Optional[ScanStatus] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
    issues: Optional[Dict[str, Any]] = None


# API Routes
@api_router.get("/")
async def root():
    return {"message": "Accessibility Scanner API", "status": "running"}


@api_router.post("/scans", response_model=ScanRequest)
async def create_scan_request(input: ScanRequestCreate):
    """Create a new accessibility scan request"""
    try:
        scan_dict = input.dict()
        scan_dict['url'] = str(scan_dict['url'])  # Convert HttpUrl to string for MongoDB
        scan_obj = ScanRequest(**scan_dict)
        scan_data = scan_obj.dict()
        scan_data['url'] = str(scan_data['url'])  # Ensure URL is string
        
        await db.scan_requests.insert_one(scan_data)
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