"""
Playwright-based accessibility scanning engine.
Uses axe-core for WCAG compliance testing with visual evidence capture.
"""
import logging
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional

from playwright.async_api import async_playwright

from ..core.database import db
from ..models.scan import ScanStatus, ScanTool


class AccessibilityScanner:
    """Accessibility scanning service using Playwright and axe-core."""
    
    @staticmethod
    async def setup_playwright_browser():
        """Set up Playwright browser with optimized options."""
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
        """Capture screenshot of specific element and return as base64."""
        try:
            element = await page.query_selector(selector)
            if element:
                screenshot_bytes = await element.screenshot()
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                return screenshot_base64
            return None
        except Exception as e:
            logging.warning(f"Could not capture element screenshot for {selector}: {e}")
            return None
    
    @staticmethod
    async def highlight_elements_on_page(page, selectors: List[str]) -> str:
        """Highlight failing elements and capture full page screenshot."""
        try:
            highlight_css = """
                .axe-violation-highlight {
                    outline: 3px solid #ff0000 !important;
                    outline-offset: 2px !important;
                    background: rgba(255, 0, 0, 0.1) !important;
                }
            """
            await page.add_style_tag(content=highlight_css)
            
            for selector in selectors:
                try:
                    await page.evaluate(f'''
                        document.querySelectorAll("{selector}").forEach(el => {{
                            el.classList.add("axe-violation-highlight");
                        }});
                    ''')
                except Exception:
                    continue
            
            screenshot_bytes = await page.screenshot(full_page=True, type='png')
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            return screenshot_base64
            
        except Exception as e:
            logging.warning(f"Could not highlight elements: {e}")
            screenshot_bytes = await page.screenshot(full_page=True, type='png')
            return base64.b64encode(screenshot_bytes).decode('utf-8')

    @staticmethod
    async def scan_with_axe(url: str) -> Dict[str, Any]:
        """Scan website using axe-core with Playwright and visual evidence."""
        playwright = None
        browser = None
        page = None
        
        try:
            playwright, browser = await AccessibilityScanner.setup_playwright_browser()
            page = await browser.new_page()
            
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(str(url), wait_until='load', timeout=30000)
            await page.wait_for_timeout(2000)
            
            await page.add_script_tag(url='https://unpkg.com/axe-core@4.8.2/axe.min.js')
            await page.wait_for_timeout(1000)
            
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
            
            score = AccessibilityScanner.calculate_axe_score(axe_results)
            formatted_issues = AccessibilityScanner.format_axe_issues(axe_results)
            
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
        """Capture visual evidence for failed accessibility issues."""
        try:
            evidence = {
                "full_page_screenshot": None,
                "issue_screenshots": {}
            }
            
            all_selectors = []
            issue_selectors = {}
            
            for issue in failed_issues:
                issue_id = issue.get('id', '')
                selectors = []
                
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
            
            if all_selectors:
                evidence["full_page_screenshot"] = await AccessibilityScanner.highlight_elements_on_page(
                    page, all_selectors[:10]
                )
            else:
                screenshot_bytes = await page.screenshot(full_page=True, type='png')
                evidence["full_page_screenshot"] = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            for issue_id, selectors in list(issue_selectors.items())[:5]:
                for selector in selectors[:3]:
                    try:
                        element_screenshot = await AccessibilityScanner.capture_element_screenshot(
                            page, selector
                        )
                        if element_screenshot:
                            evidence["issue_screenshots"][f"{issue_id}_{hash(selector)}"] = element_screenshot
                            break
                    except Exception:
                        continue
            
            return evidence
            
        except Exception as e:
            logging.error(f"Failed to capture visual evidence: {e}")
            return {"full_page_screenshot": None, "issue_screenshots": {}}
    
    @staticmethod
    def calculate_axe_score(axe_results: Dict[str, Any]) -> int:
        """Calculate accessibility score from axe results."""
        try:
            violations = axe_results.get("violations", [])
            passes = axe_results.get("passes", [])
            
            impact_weights = {"critical": 10, "serious": 5, "moderate": 3, "minor": 1}
            violation_score = 0
            
            for violation in violations:
                impact = violation.get("impact", "minor")
                node_count = len(violation.get("nodes", []))
                violation_score += impact_weights.get(impact, 1) * node_count
            
            total_rules = len(violations) + len(passes)
            if total_rules == 0:
                return 85
            
            penalty = min(violation_score * 2, 85)
            score = max(100 - penalty, 15)
            
            return int(score)
        except Exception as e:
            logging.error(f"Score calculation failed: {e}")
            return 50

    @staticmethod
    def format_axe_issues(axe_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format axe-core results to standardized issues format."""
        try:
            passed = []
            failed = []
            incomplete = []
            
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


async def perform_accessibility_scan(scan_id: str, url: str, tool: ScanTool):
    """Background task to perform accessibility scan with visual evidence."""
    try:
        logging.info(f"Starting accessibility scan for {url} using {tool}")
        
        if tool == ScanTool.axe_core:
            result = await AccessibilityScanner.scan_with_axe(url)
        else:
            # For external APIs, import and use the external scanner
            from .external_scanners import runScanWithExternalApi
            await runScanWithExternalApi(scan_id)
            return
        
        if result["success"]:
            update_data = {
                "status": ScanStatus.completed,
                "score": result["score"],
                "issues": result["results"]
            }
            
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
