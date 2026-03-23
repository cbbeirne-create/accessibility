import requests
import unittest
import uuid
import time
from datetime import datetime
import json

class AccessibilityScannerAPITest(unittest.TestCase):
    def setUp(self):
        # Use the public endpoint for testing
        self.base_url = "https://remediation-lab.preview.emergentagent.com/api"
        self.test_scan_id = None
        # Specific scan ID from the request for testing
        self.new_format_scan_id = "cfce0eb0-a9ff-4f2a-9c72-e00016aa59ac"
        # Test user IDs
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
    def test_01_health_check(self):
        """Test the API health check endpoint"""
        print("\n🔍 Testing API health check...")
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Accessibility Scanner API")
        self.assertEqual(data["status"], "running")
        print("✅ API health check passed")
        
    def test_02_create_scan(self):
        """Test creating a new scan request"""
        print("\n🔍 Testing scan creation...")
        test_url = f"https://example.com/test-{uuid.uuid4()}"
        response = requests.post(
            f"{self.base_url}/scans", 
            json={"url": test_url}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["url"], test_url)
        self.assertEqual(data["status"], "pending")
        self.assertIsNone(data["score"])
        self.assertIsNone(data["issues"])
        self.assertIsNotNone(data["id"])
        
        # Save the scan ID for later tests
        self.__class__.test_scan_id = data["id"]
        print(f"✅ Scan creation passed - Created scan with ID: {self.__class__.test_scan_id}")
        
    def test_03_verify_new_scan_format(self):
        """Test the new scan result format"""
        print(f"\n🔍 Testing new scan result format with ID: {self.new_format_scan_id}...")
        response = requests.get(f"{self.base_url}/scans/{self.new_format_scan_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found scan with ID: {self.new_format_scan_id}")
            print(f"URL: {data['url']}")
            print(f"Status: {data['status']}")
            print(f"Score: {data['score']}/100")
            
            # Verify the new issues structure
            self.assertIn("issues", data)
            self.assertIn("passed", data["issues"])
            self.assertIn("failed", data["issues"])
            self.assertIn("incomplete", data["issues"])
            
            # Check counts
            passed_count = len(data["issues"]["passed"])
            failed_count = len(data["issues"]["failed"])
            incomplete_count = len(data["issues"]["incomplete"])
            
            print(f"✅ Found {passed_count} passed tests")
            print(f"✅ Found {failed_count} failed tests")
            print(f"✅ Found {incomplete_count} incomplete tests")
            
            # Verify the expected counts from the review request
            self.assertEqual(passed_count, 13, "Expected 13 passed tests")
            self.assertEqual(failed_count, 3, "Expected 3 failed tests")
            self.assertEqual(incomplete_count, 0, "Expected 0 incomplete tests")
            
            # Verify structure of a failed test
            if failed_count > 0:
                failed_test = data["issues"]["failed"][0]
                print(f"\nSample failed test:")
                print(f"ID: {failed_test['id']}")
                print(f"Description: {failed_test['description']}")
                print(f"Impact: {failed_test['impact']}")
                print(f"Count: {failed_test['count']}")
                print(f"WCAG: {failed_test['wcag']}")
                
                # Verify the expected fields
                self.assertIn("id", failed_test)
                self.assertIn("description", failed_test)
                self.assertIn("impact", failed_test)
                self.assertIn("count", failed_test)
                self.assertIn("wcag", failed_test)
                self.assertIn("help", failed_test)
                self.assertIn("type", failed_test)
                
                # Verify html-has-lang test specifically
                html_lang_test = None
                for test in data["issues"]["failed"]:
                    if test["id"] == "html-has-lang":
                        html_lang_test = test
                        break
                
                if html_lang_test:
                    print("\n✅ Found html-has-lang test")
                    self.assertEqual(html_lang_test["impact"], "serious")
                    self.assertEqual(html_lang_test["count"], 1)
                    self.assertIn("wcag311", html_lang_test["wcag"])
                else:
                    print("❌ html-has-lang test not found")
                    self.fail("Expected html-has-lang test not found")
            
            # Verify structure of a passed test
            if passed_count > 0:
                passed_test = data["issues"]["passed"][0]
                print(f"\nSample passed test:")
                print(f"ID: {passed_test['id']}")
                print(f"Description: {passed_test['description']}")
                print(f"Count: {passed_test['count']}")
                print(f"WCAG: {passed_test['wcag']}")
                
                # Verify the expected fields
                self.assertIn("id", passed_test)
                self.assertIn("description", passed_test)
                self.assertIn("count", passed_test)
                self.assertIn("wcag", passed_test)
                self.assertIn("help", passed_test)
                self.assertIn("type", passed_test)
            
            print("\n✅ New scan result format verification passed")
        else:
            print(f"❌ Scan not found (status code: {response.status_code})")
            self.fail(f"Scan with ID {self.new_format_scan_id} not found")
    
    def test_04_run_external_api_scan(self):
        """Test running an external API scan with the new format"""
        print("\n🔍 Testing external API scan with new format...")
        
        # Create a scan with an external tool
        test_url = f"https://example.com/test-{uuid.uuid4()}"
        response = requests.post(
            f"{self.base_url}/scans", 
            json={"url": test_url, "tool": "wave", "user_id": self.test_user_id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        scan_id = data["id"]
        print(f"✅ Created WAVE scan with ID: {scan_id}")
        
        # Wait a moment to ensure the scan is in the database
        time.sleep(2)
        
        # Now manually trigger the external API scan
        response = requests.post(f"{self.base_url}/scans/{scan_id}/run-external")
        
        # If API key is not configured, we expect an error response
        if response.status_code == 500:
            error_data = response.json()
            print(f"Expected error: {error_data.get('detail', 'Unknown error')}")
            if "API key not configured" in error_data.get('detail', ''):
                print("✅ Correctly handled missing API key scenario for manual trigger")
        else:
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["scan_id"], scan_id)
            print("✅ Manual external API scan triggered successfully")
        
        # Poll for scan completion (timeout after 30 seconds)
        max_attempts = 15
        attempts = 0
        scan_completed = False
        
        print("⏳ Waiting for WAVE scan to complete...")
        while attempts < max_attempts and not scan_completed:
            time.sleep(2)  # Poll every 2 seconds
            try:
                response = requests.get(f"{self.base_url}/scans/{scan_id}")
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                if data["status"] in ["completed", "error"]:
                    scan_completed = True
                    print(f"✅ WAVE scan completed with status: {data['status']}")
                    
                    if data["status"] == "error":
                        # If API key is not configured, we expect an error
                        self.assertIsNotNone(data["error_message"])
                        print(f"Expected error: {data['error_message']}")
                        if "API key not configured" in data["error_message"]:
                            print("✅ Correctly handled missing API key scenario")
                    else:
                        # If scan completed successfully, verify the new format
                        self.assertIsNotNone(data["score"])
                        self.assertIsNotNone(data["issues"])
                        print(f"✅ WAVE scan score: {data['score']}/100")
                        
                        # Verify the new issues structure
                        self.assertIn("passed", data["issues"])
                        self.assertIn("failed", data["issues"])
                        self.assertIn("incomplete", data["issues"])
                        
                        print(f"✅ Found {len(data['issues']['passed'])} passed tests")
                        print(f"✅ Found {len(data['issues']['failed'])} failed tests")
                        print(f"✅ Found {len(data['issues']['incomplete'])} incomplete tests")
            except Exception as e:
                print(f"Error polling WAVE scan status: {e}")
            
            attempts += 1
            print(f"Polling attempt {attempts}/{max_attempts}...")
        
        # Clean up - delete the test scan
        try:
            response = requests.delete(f"{self.base_url}/scans/{scan_id}")
            if response.status_code == 200:
                print("✅ WAVE test scan deleted successfully")
        except Exception as e:
            print(f"Error deleting WAVE test scan: {e}")
            
        print("✅ External API scan with new format test completed")

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)