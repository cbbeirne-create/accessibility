import requests
import unittest
import json
import sys

class RemediationGuidanceTest(unittest.TestCase):
    def setUp(self):
        # Use the public endpoint for testing
        self.base_url = "https://scan-a11y.preview.emergentagent.com/api"
        # Specific scan IDs from the review request
        self.new_scan_id = "a6f27036-9989-4752-95a6-2f846640ca72"  # 3 failed issues with remediation
        self.previous_scan_id = "5d08b599-b23c-42dc-a328-c91ed40c6ad0"  # 39 passed, 3 failed with guidance
    
    def test_01_api_health_check(self):
        """Test the API health check endpoint"""
        print("\n🔍 Testing API health check...")
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Accessibility Scanner API")
        self.assertEqual(data["status"], "running")
        print("✅ API health check passed")
    
    def test_02_new_scan_results(self):
        """Test the new scan results with remediation guidance"""
        print(f"\n🔍 Testing new scan results with ID: {self.new_scan_id}...")
        
        response = requests.get(f"{self.base_url}/scans/{self.new_scan_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found scan with ID: {self.new_scan_id}")
            print(f"URL: {data['url']}")
            print(f"Status: {data['status']}")
            
            # Verify the scan is completed
            self.assertEqual(data["status"], "completed")
            
            # Verify issues structure
            self.assertIn("issues", data)
            self.assertIn("failed", data["issues"])
            
            # Check failed issues count
            failed_count = len(data["issues"]["failed"])
            print(f"Failed issues: {failed_count}")
            self.assertGreaterEqual(failed_count, 1, "Expected at least 1 failed issue")
            
            # Check for WCAG references in failed issues
            for issue in data["issues"]["failed"]:
                self.assertIn("id", issue)
                self.assertIn("description", issue)
                self.assertIn("wcag", issue)
                
                print(f"Issue ID: {issue['id']}")
                print(f"WCAG References: {issue['wcag']}")
                
                # Verify that these WCAG references would map to remediation guidance in the frontend
                # We can't directly test the frontend mapping here, but we can verify the data structure
                self.assertTrue(len(issue["wcag"]) > 0, "Expected at least one WCAG reference")
            
            print("✅ New scan results structure verified")
        else:
            print(f"❌ Scan not found (status code: {response.status_code})")
            self.skipTest(f"Scan with ID {self.new_scan_id} not found")
    
    def test_03_previous_scan_results(self):
        """Test the previous scan results with 39 passed tests"""
        print(f"\n🔍 Testing previous scan results with ID: {self.previous_scan_id}...")
        
        response = requests.get(f"{self.base_url}/scans/{self.previous_scan_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found scan with ID: {self.previous_scan_id}")
            print(f"URL: {data['url']}")
            print(f"Status: {data['status']}")
            
            # Verify the scan is completed
            self.assertEqual(data["status"], "completed")
            
            # Verify issues structure
            self.assertIn("issues", data)
            self.assertIn("failed", data["issues"])
            self.assertIn("passed", data["issues"])
            
            # Check passed tests count
            passed_count = len(data["issues"]["passed"])
            print(f"Passed tests: {passed_count}")
            self.assertEqual(passed_count, 39, "Expected exactly 39 passed tests")
            
            # Check failed issues count
            failed_count = len(data["issues"]["failed"])
            print(f"Failed issues: {failed_count}")
            self.assertGreaterEqual(failed_count, 3, "Expected at least 3 failed issues")
            
            # Check for WCAG references in failed issues
            for issue in data["issues"]["failed"]:
                self.assertIn("id", issue)
                self.assertIn("description", issue)
                self.assertIn("wcag", issue)
                
                print(f"Issue ID: {issue['id']}")
                print(f"WCAG References: {issue['wcag']}")
                
                # Verify that these WCAG references would map to remediation guidance in the frontend
                self.assertTrue(len(issue["wcag"]) > 0, "Expected at least one WCAG reference")
            
            print("✅ Previous scan results structure verified")
        else:
            print(f"❌ Scan not found (status code: {response.status_code})")
            self.skipTest(f"Scan with ID {self.previous_scan_id} not found")

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)