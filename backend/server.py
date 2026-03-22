from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse
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
    user_id: Optional[str] = Field(default=None)
    # Visual evidence fields
    full_page_screenshot: Optional[str] = Field(default=None)  # Base64 encoded image
    evidence_screenshots: Optional[Dict[str, str]] = Field(default=None)  # Issue ID -> Base64 screenshot
    scan_metadata: Optional[Dict[str, Any]] = Field(default=None)  # Additional scan info


class ScanRequestCreate(BaseModel):
    url: HttpUrl
    tool: Optional[ScanTool] = Field(default=ScanTool.axe_core)
    user_id: Optional[str] = Field(default=None)  # Optional user identifier


class ScanRequestUpdate(BaseModel):
    status: Optional[ScanStatus] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
    issues: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# External API Integration Classes
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


# Server Action: Run Scan with External API
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
    """Background task to perform accessibility scan"""
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
async def get_scan_requests(user_id: Optional[str] = None):
    """Get all scan requests, optionally filtered by user_id"""
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
            
        scan_requests = await db.scan_requests.find(query).sort("createdAt", -1).to_list(100)
        return [ScanRequest(**scan_request) for scan_request in scan_requests]
    except Exception as e:
        logging.error(f"Error fetching scan requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan requests")


@api_router.get("/users/{user_id}/scans", response_model=List[ScanRequest])
async def get_user_scans(user_id: str):
    """Get all scan requests for a specific user"""
    try:
        scan_requests = await db.scan_requests.find({"user_id": user_id}).sort("createdAt", -1).to_list(100)
        return [ScanRequest(**scan_request) for scan_request in scan_requests]
    except Exception as e:
        logging.error(f"Error fetching user scans: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user scans")


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