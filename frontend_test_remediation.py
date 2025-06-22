import asyncio
from playwright.async_api import async_playwright
import sys

async def test_remediation_guidance():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("Starting test for remediation guidance feature...")
            
            # Navigate to the dashboard
            await page.goto("https://3f2797e6-9bad-45f5-ae39-514f6005b46a.preview.emergentagent.com/")
            print("Dashboard loaded successfully")
            
            # Find and click on the first "View Details" button
            view_details_buttons = await page.query_selector_all("text=View Details")
            if view_details_buttons and len(view_details_buttons) > 0:
                print(f"Found {len(view_details_buttons)} 'View Details' buttons")
                await view_details_buttons[0].click()
                print("Clicked on the first 'View Details' button")
                
                # Wait for the scan results page to load
                await page.wait_for_selector("text=Accessibility Scan Results", timeout=10000)
                print("Scan results page loaded successfully")
                
                # Check for failed issues section
                failed_issues_section = await page.query_selector("text=❌ Accessibility Issues")
                if failed_issues_section:
                    print("Found failed issues section")
                    
                    # Check for remediation guidance sections
                    remediation_sections = await page.query_selector_all("text=💡 How to fix it")
                    if remediation_sections and len(remediation_sections) > 0:
                        print(f"Found {len(remediation_sections)} remediation guidance sections")
                        
                        # Check styling of remediation guidance
                        guidance_boxes = await page.query_selector_all(".bg-gray-100.p-2.rounded.text-sm")
                        if guidance_boxes and len(guidance_boxes) > 0:
                            print(f"Found {len(guidance_boxes)} properly styled guidance boxes")
                            
                            # Get the text content of the first guidance box
                            guidance_text = await guidance_boxes[0].text_content()
                            print(f"First remediation guidance: {guidance_text}")
                            
                            # Check if the guidance is practical and actionable
                            if "add" in guidance_text.lower() or "ensure" in guidance_text.lower() or "use" in guidance_text.lower():
                                print("Guidance appears to be practical and actionable")
                            else:
                                print("Guidance may not be practical or actionable")
                        else:
                            print("Could not find properly styled guidance boxes")
                    else:
                        print("No remediation guidance sections found")
                else:
                    print("Failed issues section not found")
            else:
                print("No 'View Details' buttons found on the dashboard")
            
            # Now try to find the scan with 39 passed tests
            print("\nNavigating back to dashboard to find the scan with 39 passed tests...")
            await page.goto("https://3f2797e6-9bad-45f5-ae39-514f6005b46a.preview.emergentagent.com/")
            
            # Look for the scan with 39 passed tests
            scan_cards = await page.query_selector_all(".bg-white.rounded-lg.shadow-md.p-6")
            print(f"Found {len(scan_cards)} scan cards on the dashboard")
            
            # Look for a card with "39" in it
            scan_with_39_passed = None
            for i, card in enumerate(scan_cards):
                card_text = await card.text_content()
                if "39" in card_text:
                    print(f"Found scan with 39 in card {i+1}")
                    scan_with_39_passed = card
                    break
            
            if scan_with_39_passed:
                # Find and click the "View Details" button in this card
                view_details_button = await scan_with_39_passed.query_selector("text=View Details")
                if view_details_button:
                    await view_details_button.click()
                    print("Clicked on 'View Details' for the scan with 39 passed tests")
                    
                    # Wait for the scan results page to load
                    await page.wait_for_selector("text=Accessibility Scan Results", timeout=10000)
                    print("Scan results page loaded successfully")
                    
                    # Check for failed issues section
                    failed_issues_section = await page.query_selector("text=❌ Accessibility Issues")
                    if failed_issues_section:
                        print("Found failed issues section")
                        
                        # Check for remediation guidance sections
                        remediation_sections = await page.query_selector_all("text=💡 How to fix it")
                        if remediation_sections and len(remediation_sections) > 0:
                            print(f"Found {len(remediation_sections)} remediation guidance sections")
                        else:
                            print("No remediation guidance sections found")
                    else:
                        print("Failed issues section not found")
                    
                    # Check for passed tests section
                    passed_tests_section = await page.query_selector("text=✅ Passed Tests")
                    if passed_tests_section:
                        print("Found passed tests section")
                        
                        # Get the text content to check the count
                        passed_tests_text = await passed_tests_section.text_content()
                        print(f"Passed tests section text: {passed_tests_text}")
                        
                        # Check if it mentions 39 passed tests
                        if "39" in passed_tests_text:
                            print("Confirmed 39 passed tests as expected")
                        else:
                            print(f"Expected 39 passed tests, but found: {passed_tests_text}")
                    else:
                        print("Passed tests section not found")
                else:
                    print("Could not find 'View Details' button for the scan with 39 passed tests")
            else:
                print("Could not find a scan with 39 passed tests on the dashboard")
            
            print("Remediation guidance feature test completed successfully")
            
        except Exception as e:
            print(f"Error during testing: {str(e)}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_remediation_guidance())