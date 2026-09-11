"""Playwright-based accessibility scanning engine using axe-core."""
import base64
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from ..core.config import settings
from ..core.database import db
from ..models.scan import ScanStatus, ScanTool
from .evidence_storage import store_base64_png
from .url_security import UnsafeScanTarget, validate_scan_url

logger = logging.getLogger(__name__)


class AccessibilityScanner:
    """Accessibility scanning service using Playwright and axe-core."""

    @staticmethod
    async def setup_playwright_browser():
        playwright = await async_playwright().start()
        try:
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                    "--disable-gpu",
                    "--disable-features=TranslateUI",
                ],
            )
            return playwright, browser
        except Exception:
            await playwright.stop()
            raise

    @staticmethod
    async def _install_network_guard(page) -> None:
        """Abort HTTP(S) requests that resolve outside the public internet."""
        validated_hosts: set[tuple[str, int]] = set()

        async def guard(route):
            request_url = route.request.url
            parsed = urlparse(request_url)
            if parsed.scheme not in {"http", "https"}:
                await route.continue_()
                return
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            key = ((parsed.hostname or "").lower(), port)
            try:
                if key not in validated_hosts:
                    await validate_scan_url(request_url)
                    validated_hosts.add(key)
                await route.continue_()
            except UnsafeScanTarget:
                logger.warning("Blocked unsafe browser request to %s", request_url)
                await route.abort("blockedbyclient")

        await page.route("**/*", guard)

    @staticmethod
    async def capture_element_screenshot(page, selector: str) -> Optional[str]:
        try:
            element = await page.query_selector(selector)
            if not element:
                return None
            return base64.b64encode(await element.screenshot(type="png")).decode("utf-8")
        except Exception as exc:
            logger.debug("Could not capture element screenshot for %s: %s", selector, exc)
            return None

    @staticmethod
    async def highlight_elements_on_page(page, selectors: List[str]) -> str:
        await page.add_style_tag(content="""
            .axe-violation-highlight {
                outline: 3px solid #dc2626 !important;
                outline-offset: 2px !important;
                background: rgba(220, 38, 38, 0.08) !important;
            }
        """)
        for selector in selectors[:10]:
            try:
                await page.locator(selector).first.evaluate("el => el.classList.add('axe-violation-highlight')")
            except Exception:
                continue
        return base64.b64encode(await page.screenshot(full_page=True, type="png")).decode("utf-8")

    @staticmethod
    async def scan_with_axe(url: str) -> Dict[str, Any]:
        playwright = browser = context = page = None
        try:
            await validate_scan_url(url)
            playwright, browser = await AccessibilityScanner.setup_playwright_browser()
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                ignore_https_errors=False,
                service_workers="block",
            )
            page = await context.new_page()
            await AccessibilityScanner._install_network_guard(page)
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=settings.SCAN_NAVIGATION_TIMEOUT_MS,
            )
            if response and response.status >= 400:
                raise RuntimeError(f"Target returned HTTP {response.status}")
            await page.wait_for_timeout(1000)

            # Pinned version for deterministic rule behavior. TODO: vendor axe-core in the image.
            await page.add_script_tag(url="https://unpkg.com/axe-core@4.8.2/axe.min.js")
            axe_results = await page.evaluate("""
                async () => {
                    if (typeof axe === 'undefined') throw new Error('axe-core not loaded');
                    return await axe.run(document, {
                        resultTypes: ['violations', 'passes', 'incomplete', 'inapplicable']
                    });
                }
            """)

            formatted = AccessibilityScanner.format_axe_issues(axe_results)
            evidence = await AccessibilityScanner.capture_visual_evidence(page, formatted.get("failed", []))
            score = AccessibilityScanner.calculate_axe_score(axe_results)
            return {
                "success": True,
                "score": score,
                "results": formatted,
                "tool": "axe-core",
                "visual_evidence": evidence,
                "scan_metadata": {
                    "viewport": {"width": 1440, "height": 900},
                    "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                    "total_violations": len(formatted.get("failed", [])),
                    "total_passes": len(formatted.get("passed", [])),
                    "total_incomplete": len(formatted.get("incomplete", [])),
                    "score_name": "Auditly Accessibility Health Score",
                    "score_disclaimer": "Automated health score only; it is not a WCAG conformance certification.",
                    "axe_core_version": "4.8.2",
                },
            }
        except Exception as exc:
            logger.error("axe-core scan failed for %s: %s", url, exc)
            return {"success": False, "error": str(exc), "tool": "axe-core"}
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()

    @staticmethod
    async def capture_visual_evidence(page, failed_issues: List[Dict]) -> Dict[str, Any]:
        evidence: Dict[str, Any] = {"full_page_screenshot": None, "issue_screenshots": {}}
        try:
            issue_selectors: Dict[str, List[str]] = {}
            all_selectors: List[str] = []
            for issue in failed_issues:
                selectors: List[str] = []
                for selector_group in issue.get("selectors", []):
                    selectors.extend(selector_group if isinstance(selector_group, list) else [selector_group])
                if selectors:
                    issue_selectors[issue.get("id", "unknown")] = selectors
                    all_selectors.extend(selectors)

            if all_selectors:
                evidence["full_page_screenshot"] = await AccessibilityScanner.highlight_elements_on_page(page, all_selectors)
            else:
                evidence["full_page_screenshot"] = base64.b64encode(
                    await page.screenshot(full_page=True, type="png")
                ).decode("utf-8")

            for issue_id, selectors in list(issue_selectors.items())[:5]:
                for selector in selectors[:3]:
                    screenshot = await AccessibilityScanner.capture_element_screenshot(page, selector)
                    if screenshot:
                        evidence["issue_screenshots"][f"{issue_id}_{abs(hash(selector))}"] = screenshot
                        break
        except Exception as exc:
            logger.warning("Failed to capture visual evidence: %s", exc)
        return evidence

    @staticmethod
    def calculate_axe_score(axe_results: Dict[str, Any]) -> int:
        """Return a proprietary automated health score, not a WCAG conformance percentage."""
        violations = axe_results.get("violations", [])
        passes = axe_results.get("passes", [])
        impact_weights = {"critical": 10, "serious": 5, "moderate": 3, "minor": 1}
        weighted_failures = sum(
            impact_weights.get(violation.get("impact") or "minor", 1) * max(1, len(violation.get("nodes", [])))
            for violation in violations
        )
        passed_nodes = sum(max(1, len(rule.get("nodes", []))) for rule in passes)
        denominator = passed_nodes + weighted_failures
        if denominator == 0:
            return 100
        return max(0, min(100, round((passed_nodes / denominator) * 100)))

    @staticmethod
    def format_axe_issues(axe_results: Dict[str, Any]) -> Dict[str, Any]:
        failed = []
        for violation in axe_results.get("violations", []):
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
                        "failureSummary": node.get("failureSummary", ""),
                    }
                    for node in nodes
                ],
                "type": "violation",
            })

        passed = [
            {
                "id": rule.get("id", "unknown"),
                "description": rule.get("description", ""),
                "help": rule.get("help", ""),
                "helpUrl": rule.get("helpUrl", ""),
                "count": len(rule.get("nodes", [])),
                "wcag": rule.get("tags", []),
                "type": "passed_test",
            }
            for rule in axe_results.get("passes", [])
        ]
        incomplete = [
            {
                "id": rule.get("id", "unknown"),
                "description": rule.get("description", ""),
                "help": rule.get("help", ""),
                "helpUrl": rule.get("helpUrl", ""),
                "count": len(rule.get("nodes", [])),
                "wcag": rule.get("tags", []),
                "reason": "Automated testing cannot determine if this passes or fails",
                "type": "incomplete_test",
            }
            for rule in axe_results.get("incomplete", [])
        ]
        return {"passed": passed, "failed": failed, "incomplete": incomplete}


async def perform_accessibility_scan(scan_id: str, url: str, tool: ScanTool | str):
    try:
        normalized_tool = ScanTool(tool)
        if normalized_tool == ScanTool.axe_core:
            result = await AccessibilityScanner.scan_with_axe(url)
        else:
            from .external_scanners import runScanWithExternalApi
            await runScanWithExternalApi(scan_id)
            return

        if result["success"]:
            evidence = result.get("visual_evidence") or {}
            full_page = await store_base64_png(
                evidence.get("full_page_screenshot"), f"{scan_id}/full-page.png"
            )
            issue_refs = {}
            for evidence_id, screenshot in (evidence.get("issue_screenshots") or {}).items():
                issue_refs[evidence_id] = await store_base64_png(
                    screenshot, f"{scan_id}/issues/{evidence_id}.png"
                )
            update_data = {
                "status": ScanStatus.completed,
                "score": result["score"],
                "issues": result["results"],
                "full_page_screenshot": full_page,
                "evidence_screenshots": issue_refs,
                "scan_metadata": result.get("scan_metadata", {}),
            }
        else:
            update_data = {"status": ScanStatus.error, "error_message": result["error"]}

        await db.scan_requests.update_one({"id": scan_id}, {"$set": update_data})
    except Exception as exc:
        logger.exception("Scan task failed for %s", scan_id)
        await db.scan_requests.update_one(
            {"id": scan_id},
            {"$set": {"status": ScanStatus.error, "error_message": str(exc)}},
        )
