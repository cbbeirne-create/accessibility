"""Container smoke check: launch and close Chromium as the image's non-root user."""
import asyncio

from backend.services.playwright_engine import AccessibilityScanner


async def main():
    playwright, browser = await AccessibilityScanner.setup_playwright_browser()
    try:
        print('chromium-ok')
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == '__main__':
    asyncio.run(main())
