"""
External API scanners for WAVE, EqualWeb, and AccessiBe.
"""
import logging
import requests
from typing import Dict, Any

from ..core.config import settings
from ..core.database import db
from ..models.scan import ScanRequest, ScanStatus, ScanTool


class ExternalAPIScanner:
    """External accessibility scanning API integrations."""
    
    @staticmethod
    async def scan_with_wave_api(url: str) -> Dict[str, Any]:
        """Scan website using WAVE API."""
        api_key = settings.WAVE_API_KEY
        if not api_key:
            return {
                "success": False,
                "error": "WAVE API key not configured",
                "tool": "wave"
            }
        
        try:
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
            
            if result.get("status", {}).get("error"):
                return {
                    "success": False,
                    "error": f"WAVE API error: {result['status']}",
                    "tool": "wave"
                }
            
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
        """Scan website using EqualWeb API."""
        api_key = settings.EQUALWEB_API_KEY
        if not api_key:
            return {
                "success": False,
                "error": "EqualWeb API key not configured",
                "tool": "equalweb"
            }
        
        try:
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
        """Scan website using AccessiBe API."""
        api_key = settings.ACCESSIBE_API_KEY
        if not api_key:
            return {
                "success": False,
                "error": "AccessiBe API key not configured",
                "tool": "accessibe"
            }
        
        try:
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
        """Calculate accessibility score from WAVE API results."""
        try:
            categories = wave_result.get("categories", {})
            errors = categories.get("error", {}).get("count", 0)
            alerts = categories.get("alert", {}).get("count", 0)
            features = categories.get("feature", {}).get("count", 0)
            structure = categories.get("structure", {}).get("count", 0)
            
            error_penalty = errors * 15
            alert_penalty = alerts * 5
            feature_bonus = min(features * 2, 20)
            structure_bonus = min(structure * 1, 10)
            
            score = 100 - error_penalty - alert_penalty + feature_bonus + structure_bonus
            return max(min(score, 100), 0)
            
        except Exception as e:
            logging.error(f"WAVE score calculation failed: {e}")
            return 50
    
    @staticmethod
    def format_wave_issues(wave_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format WAVE API results to standardized issues format."""
        try:
            passed = []
            failed = []
            incomplete = []
            
            errors = wave_result.get("categories", {}).get("error", {}).get("items", {})
            for error_type, error_data in errors.items():
                failed.append({
                    "id": error_type,
                    "description": error_data.get("description", ""),
                    "impact": "serious",
                    "help": error_data.get("help", ""),
                    "count": error_data.get("count", 0),
                    "wcag": error_data.get("wcag", []),
                    "selector": error_data.get("selector", ""),
                    "type": "error"
                })
            
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
            
            features = wave_result.get("categories", {}).get("feature", {}).get("items", {})
            for feature_type, feature_data in features.items():
                passed.append({
                    "id": feature_type,
                    "description": feature_data.get("description", ""),
                    "help": feature_data.get("help", ""),
                    "count": feature_data.get("count", 0),
                    "type": "feature"
                })
            
            structure = wave_result.get("categories", {}).get("structure", {}).get("items", {})
            for struct_type, struct_data in structure.items():
                passed.append({
                    "id": struct_type,
                    "description": struct_data.get("description", ""),
                    "help": struct_data.get("help", ""),
                    "count": struct_data.get("count", 0),
                    "type": "structure"
                })
            
            return {"passed": passed, "failed": failed, "incomplete": incomplete}
            
        except Exception as e:
            logging.error(f"WAVE results formatting failed: {e}")
            return {"passed": [], "failed": [], "incomplete": []}
    
    @staticmethod
    def calculate_equalweb_score(equalweb_result: Dict[str, Any]) -> int:
        """Calculate accessibility score from EqualWeb API results."""
        try:
            compliance_score = equalweb_result.get("compliance_score", 50)
            if isinstance(compliance_score, (int, float)):
                return max(min(int(compliance_score), 100), 0)
            return 50
        except Exception as e:
            logging.error(f"EqualWeb score calculation failed: {e}")
            return 50
    
    @staticmethod
    def format_equalweb_issues(equalweb_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format EqualWeb API results to standardized issues format."""
        try:
            passed = []
            failed = []
            incomplete = []
            
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
            
            return {"passed": passed, "failed": failed, "incomplete": incomplete}
            
        except Exception as e:
            logging.error(f"EqualWeb results formatting failed: {e}")
            return {"passed": [], "failed": [], "incomplete": []}
    
    @staticmethod
    def calculate_accessibe_score(accessibe_result: Dict[str, Any]) -> int:
        """Calculate accessibility score from AccessiBe API results."""
        try:
            score = accessibe_result.get("accessibility_score", 50)
            if isinstance(score, (int, float)):
                return max(min(int(score), 100), 0)
            return 50
        except Exception as e:
            logging.error(f"AccessiBe score calculation failed: {e}")
            return 50
    
    @staticmethod
    def format_accessibe_issues(accessibe_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format AccessiBe API results to standardized issues format."""
        try:
            passed = []
            failed = []
            incomplete = []
            
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
            
            return {"passed": passed, "failed": failed, "incomplete": incomplete}
            
        except Exception as e:
            logging.error(f"AccessiBe results formatting failed: {e}")
            return {"passed": [], "failed": [], "incomplete": []}


async def runScanWithExternalApi(scan_request_id: str) -> Dict[str, Any]:
    """
    Server action to run accessibility scan using external APIs.
    """
    from .playwright_engine import AccessibilityScanner
    
    try:
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
        
        if tool == ScanTool.wave:
            result = await ExternalAPIScanner.scan_with_wave_api(url)
        elif tool == ScanTool.equalweb:
            result = await ExternalAPIScanner.scan_with_equalweb_api(url)
        elif tool == ScanTool.accessibe:
            result = await ExternalAPIScanner.scan_with_accessibe_api(url)
        else:
            result = await AccessibilityScanner.scan_with_axe(url)
        
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
            pass
        
        return {
            "success": False,
            "scan_id": scan_request_id,
            "error": error_msg
        }
