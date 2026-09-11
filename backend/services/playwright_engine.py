"""Playwright + axe-core accessibility scanning engine with SSRF controls."""
import asyncio
import base64
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from playwright.async_api import Route, async_playwright

from ..core.config import settings
from ..core.database import db
from ..models.scan import ScanStatus, ScanTool
from .storage import store_png_base64
from .url_safety import validate_scan_url

logger = logging.getLogger(__name__)


class AccessibilityScanner:
    @staticmethod
    async def setup_playwright_browser():
        playwright = await async_playwright().start()
        try:
            browser = await playwright.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage'],
            )
            return playwright, browser
        except Exception:
            await playwright.stop()
            raise

    @staticmethod
    async def _secure_route(route: Route):
        url = route.request.url
        parsed = urlparse(url)
        if parsed.scheme in {'data', 'blob', 'about'}:
            await route.continue_()
            return
        if parsed.scheme not in {'http', 'https'}:
            await route.abort()
            return
        try:
            await validate_scan_url(url)
        except Exception as exc:
            logger.warning('Blocked unsafe browser request %s: %s', url, exc)
            await route.abort()
            return
        await route.continue_()

    @staticmethod
    async def capture_element_screenshot(page, selector: str) -> Optional[str]:
        try:
            element = page.locator(selector).first
            if await element.count():
                data = await element.screenshot(type='png')
                return base64.b64encode(data).decode('utf-8')
        except Exception as exc:
            logger.debug('Element screenshot failed for %s: %s', selector, exc)
        return None

    @staticmethod
    async def capture_visual_evidence(page, failed_issues: List[Dict]) -> Dict[str, Any]:
        evidence = {'full_page_screenshot': None, 'issue_screenshots': {}}
        issue_selectors: Dict[str, List[str]] = {}
        all_selectors: List[str] = []
        for issue in failed_issues:
            selectors: List[str] = []
            for selector_group in issue.get('selectors') or []:
                selectors.extend(selector_group if isinstance(selector_group, list) else [selector_group])
            for element in issue.get('elements') or []:
                selectors.extend(element.get('target') or [])
            selectors = [s for s in selectors if isinstance(s, str)][:20]
            if selectors:
                issue_selectors[issue.get('id', 'issue')] = selectors
                all_selectors.extend(selectors)

        if all_selectors:
            await page.add_style_tag(content='.axe-violation-highlight{outline:3px solid #d00!important;outline-offset:2px!important;background:rgba(220,0,0,.08)!important;}')
            await page.evaluate(
                """selectors => selectors.forEach(selector => { try { document.querySelectorAll(selector).forEach(el => el.classList.add('axe-violation-highlight')); } catch (_) {} })""",
                all_selectors[:30],
            )
        screenshot = await page.screenshot(full_page=True, type='png')
        evidence['full_page_screenshot'] = base64.b64encode(screenshot).decode('utf-8')

        for issue_id, selectors in list(issue_selectors.items())[:10]:
            for selector in selectors[:3]:
                shot = await AccessibilityScanner.capture_element_screenshot(page, selector)
                if shot:
                    evidence['issue_screenshots'][f'{issue_id}_{abs(hash(selector))}'] = shot
                    break
        return evidence

    @staticmethod
    def calculate_axe_score(results: Dict[str, Any]) -> int:
        """Auditly health score; this is not a WCAG compliance percentage."""
        violations = results.get('violations', [])
        passes = results.get('passes', [])
        if not violations and not passes:
            return 0
        impact_weights = {'critical': 10, 'serious': 5, 'moderate': 3, 'minor': 1}
        penalty = sum(impact_weights.get(v.get('impact'), 1) * max(1, len(v.get('nodes', []))) for v in violations)
        return int(max(0, 100 - min(penalty * 2, 100)))

    @staticmethod
    def format_axe_issues(results: Dict[str, Any]) -> Dict[str, Any]:
        failed = []
        passed = []
        incomplete = []
        for violation in results.get('violations', []):
            nodes = violation.get('nodes', [])
            failed.append({
                'id': violation.get('id', 'unknown'),
                'description': violation.get('description', ''),
                'impact': violation.get('impact', 'moderate'),
                'help': violation.get('help', ''),
                'helpUrl': violation.get('helpUrl', ''),
                'count': len(nodes),
                'wcag': violation.get('tags', []),
                'selectors': [node.get('target', []) for node in nodes],
                'elements': [{
                    'html': node.get('html', ''),
                    'target': node.get('target', []),
                    'failureSummary': node.get('failureSummary', ''),
                } for node in nodes],
                'type': 'violation',
            })
        for item in results.get('passes', []):
            passed.append({
                'id': item.get('id', 'unknown'),
                'description': item.get('description', ''),
                'help': item.get('help', ''),
                'helpUrl': item.get('helpUrl', ''),
                'count': len(item.get('nodes', [])),
                'wcag': item.get('tags', []),
                'type': 'passed_test',
            })
        for item in results.get('incomplete', []):
            incomplete.append({
                'id': item.get('id', 'unknown'),
                'description': item.get('description', ''),
                'help': item.get('help', ''),
                'helpUrl': item.get('helpUrl', ''),
                'count': len(item.get('nodes', [])),
                'wcag': item.get('tags', []),
                'reason': 'Automated testing cannot determine whether this passes or fails.',
                'type': 'incomplete_test',
            })
        return {'passed': passed, 'failed': failed, 'incomplete': incomplete}

    @staticmethod
    async def scan_with_axe(url: str) -> Dict[str, Any]:
        await validate_scan_url(url)
        playwright = browser = page = None
        try:
            playwright, browser = await AccessibilityScanner.setup_playwright_browser()
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=False,
            )
            page = await context.new_page()
            await page.route('**/*', AccessibilityScanner._secure_route)
            response = await page.goto(url, wait_until='load', timeout=settings.SCAN_NAVIGATION_TIMEOUT_MS)
            if not response:
                raise RuntimeError('No response received from target')
            await page.wait_for_timeout(750)

            axe_path = Path(settings.AXE_CORE_PATH)
            if not axe_path.is_file():
                raise RuntimeError(f'Local axe-core bundle not found at {axe_path}')
            await page.add_script_tag(path=str(axe_path))
            axe_results = await page.evaluate("""async () => { if (!window.axe) throw new Error('axe-core not loaded'); return await window.axe.run(document); }""")
            formatted = AccessibilityScanner.format_axe_issues(axe_results)
            evidence = await AccessibilityScanner.capture_visual_evidence(page, formatted['failed'])
            return {
                'success': True,
                'score': AccessibilityScanner.calculate_axe_score(axe_results),
                'results': formatted,
                'tool': 'axe-core',
                'visual_evidence': evidence,
                'scan_metadata': {
                    'viewport': {'width': 1920, 'height': 1080},
                    'scan_timestamp': datetime.now(timezone.utc).isoformat(),
                    'final_url': page.url,
                    'total_violations': len(formatted['failed']),
                    'total_passes': len(formatted['passed']),
                    'total_incomplete': len(formatted['incomplete']),
                    'score_name': 'Auditly Accessibility Health Score',
                    'score_disclaimer': 'Automated health score only; it is not a WCAG compliance percentage or certification.',
                },
            }
        except Exception as exc:
            logger.exception('axe-core scan failed for %s', url)
            return {'success': False, 'error': str(exc), 'tool': 'axe-core'}
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


async def perform_accessibility_scan(scan_id: str, url: str, tool: ScanTool | str):
    try:
        tool_value = tool.value if isinstance(tool, ScanTool) else str(tool)
        if tool_value == ScanTool.axe_core.value:
            result = await AccessibilityScanner.scan_with_axe(url)
        else:
            from .external_scanners import runScanWithExternalApi
            return await runScanWithExternalApi(scan_id)

        if not result['success']:
            await db.scan_requests.update_one({'id': scan_id}, {'$set': {'status': ScanStatus.error.value, 'error_message': result['error']}})
            return result

        visual = result.get('visual_evidence') or {}
        full = await asyncio.to_thread(store_png_base64, visual.get('full_page_screenshot'), scan_id)
        evidence_base64 = {}
        evidence_keys = {}
        evidence_urls = {}
        for name, data in (visual.get('issue_screenshots') or {}).items():
            stored = await asyncio.to_thread(store_png_base64, data, f'{scan_id}/{name}')
            if stored['base64']:
                evidence_base64[name] = stored['base64']
            if stored['key']:
                evidence_keys[name] = stored['key']
            if stored['url']:
                evidence_urls[name] = stored['url']

        update = {
            'status': ScanStatus.completed.value,
            'score': result['score'],
            'issues': result['results'],
            'scan_metadata': result.get('scan_metadata', {}),
            'full_page_screenshot': full['base64'],
            'full_page_screenshot_key': full['key'],
            'full_page_screenshot_url': full['url'],
            'evidence_screenshots': evidence_base64 or None,
            'evidence_screenshot_keys': evidence_keys or None,
            'evidence_screenshot_urls': evidence_urls or None,
            'error_message': None,
        }
        await db.scan_requests.update_one({'id': scan_id}, {'$set': update})
        return result
    except Exception as exc:
        logger.exception('Scan task failed for %s', scan_id)
        await db.scan_requests.update_one({'id': scan_id}, {'$set': {'status': ScanStatus.error.value, 'error_message': str(exc)}})
        raise
