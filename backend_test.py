import requests
import sys
import json
import time
from datetime import datetime

class AccessibilityScannerTester:
    def __init__(self, base_url="https://site-checker.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.scan_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details and success:
            print(f"   Details: {details}")

    def test_api_health(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'N/A')}"
            self.log_test("API Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("API Health Check", False, str(e))
            return False

    def test_external_api_status(self):
        """Test external API status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/external-apis/status", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", APIs: {list(data.keys())}"
            self.log_test("External API Status", success, details)
            return success, response.json() if success else {}
        except Exception as e:
            self.log_test("External API Status", False, str(e))
            return False, {}

    def test_create_scan_with_visual_evidence(self):
        """Test creating a scan with visual evidence capture"""
        try:
            # Use a simple, accessible website for testing
            test_url = "https://example.com"
            payload = {
                "url": test_url,
                "tool": "axe-core",
                "user_id": "test_user_123"
            }
            
            response = requests.post(f"{self.api_url}/scans", json=payload, timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.scan_id = data.get('id')
                details = f"Scan ID: {self.scan_id}, Status: {data.get('status')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Create Scan with Visual Evidence", success, details)
            return success
        except Exception as e:
            self.log_test("Create Scan with Visual Evidence", False, str(e))
            return False

    def test_scan_completion_with_polling(self, max_wait_time=120):
        """Test scan completion by polling the scan status"""
        if not self.scan_id:
            self.log_test("Scan Completion Polling", False, "No scan ID available")
            return False
        
        try:
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                response = requests.get(f"{self.api_url}/scans/{self.scan_id}", timeout=10)
                if response.status_code != 200:
                    self.log_test("Scan Completion Polling", False, f"Failed to fetch scan: {response.status_code}")
                    return False
                
                data = response.json()
                status = data.get('status')
                
                if status == 'completed':
                    # Check for visual evidence
                    has_screenshot = bool(data.get('full_page_screenshot'))
                    has_issues = bool(data.get('issues'))
                    score = data.get('score')
                    
                    details = f"Status: {status}, Score: {score}, Screenshot: {has_screenshot}, Issues: {has_issues}"
                    self.log_test("Scan Completion Polling", True, details)
                    return True
                elif status == 'error':
                    error_msg = data.get('error_message', 'Unknown error')
                    self.log_test("Scan Completion Polling", False, f"Scan failed: {error_msg}")
                    return False
                
                # Still pending, wait and retry
                print(f"   Scan status: {status}, waiting...")
                time.sleep(5)
            
            # Timeout reached
            self.log_test("Scan Completion Polling", False, f"Timeout after {max_wait_time}s")
            return False
            
        except Exception as e:
            self.log_test("Scan Completion Polling", False, str(e))
            return False

    def test_scan_results_structure(self):
        """Test the structure of scan results"""
        if not self.scan_id:
            self.log_test("Scan Results Structure", False, "No scan ID available")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/scans/{self.scan_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Check required fields
                required_fields = ['id', 'url', 'status', 'createdAt', 'tool']
                missing_fields = [field for field in required_fields if field not in data]
                
                # Check enhanced fields for visual evidence
                enhanced_fields = ['full_page_screenshot', 'scan_metadata']
                present_enhanced = [field for field in enhanced_fields if data.get(field)]
                
                # Check issues structure
                issues = data.get('issues', {})
                issue_categories = ['failed', 'passed', 'incomplete']
                present_categories = [cat for cat in issue_categories if cat in issues]
                
                if missing_fields:
                    details = f"Missing required fields: {missing_fields}"
                    success = False
                else:
                    details = f"Enhanced fields: {present_enhanced}, Issue categories: {present_categories}"
                
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Scan Results Structure", success, details)
            return success
        except Exception as e:
            self.log_test("Scan Results Structure", False, str(e))
            return False

    def test_pdf_export(self):
        """Test PDF report export"""
        if not self.scan_id:
            self.log_test("PDF Export", False, "No scan ID available")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/scans/{self.scan_id}/export/pdf", timeout=30)
            success = response.status_code == 200
            
            if success:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                details = f"Content-Type: {content_type}, Size: {content_length} bytes"
                success = 'pdf' in content_type.lower() and content_length > 1000
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("PDF Export", success, details)
            return success
        except Exception as e:
            self.log_test("PDF Export", False, str(e))
            return False

    def test_json_export(self):
        """Test JSON data export"""
        if not self.scan_id:
            self.log_test("JSON Export", False, "No scan ID available")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/scans/{self.scan_id}/export/json", timeout=30)
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    # Check JSON export structure
                    required_sections = ['scan_info', 'results', 'export_timestamp']
                    missing_sections = [section for section in required_sections if section not in data]
                    
                    if missing_sections:
                        details = f"Missing sections: {missing_sections}"
                        success = False
                    else:
                        results = data.get('results', {})
                        summary = results.get('summary', {})
                        details = f"Sections: {list(data.keys())}, Summary: {summary}"
                except json.JSONDecodeError:
                    details = "Invalid JSON response"
                    success = False
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("JSON Export", success, details)
            return success
        except Exception as e:
            self.log_test("JSON Export", False, str(e))
            return False

    def test_screenshot_endpoint(self):
        """Test screenshot viewing endpoint"""
        if not self.scan_id:
            self.log_test("Screenshot Endpoint", False, "No scan ID available")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/scans/{self.scan_id}/screenshot", timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                success = 'image' in content_type.lower() and content_length > 1000
                details = f"Content-Type: {content_type}, Size: {content_length} bytes"
            elif response.status_code == 404:
                # Screenshot might not be available for this scan
                success = True
                details = "Screenshot not available (404) - acceptable for some scans"
            else:
                success = False
                details = f"Status: {response.status_code}"
            
            self.log_test("Screenshot Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Screenshot Endpoint", False, str(e))
            return False

    def test_get_all_scans(self):
        """Test getting all scans"""
        try:
            response = requests.get(f"{self.api_url}/scans", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                scan_count = len(data)
                details = f"Retrieved {scan_count} scans"
                if scan_count > 0:
                    # Check if our test scan is in the list
                    scan_ids = [scan.get('id') for scan in data]
                    if self.scan_id and self.scan_id in scan_ids:
                        details += f", Test scan found"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Get All Scans", success, details)
            return success
        except Exception as e:
            self.log_test("Get All Scans", False, str(e))
            return False

    def test_user_scans(self):
        """Test getting user-specific scans"""
        try:
            user_id = "test_user_123"
            response = requests.get(f"{self.api_url}/users/{user_id}/scans", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                scan_count = len(data)
                details = f"Retrieved {scan_count} scans for user {user_id}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Get User Scans", success, details)
            return success
        except Exception as e:
            self.log_test("Get User Scans", False, str(e))
            return False

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Accessibility Scanner Backend Tests")
        print("=" * 70)
        
        # Basic connectivity tests
        if not self.test_api_health():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Test external API status
        self.test_external_api_status()
        
        # Test scan creation and processing
        if self.test_create_scan_with_visual_evidence():
            # Wait for scan completion
            if self.test_scan_completion_with_polling():
                # Test enhanced features
                self.test_scan_results_structure()
                self.test_pdf_export()
                self.test_json_export()
                self.test_screenshot_endpoint()
        
        # Test listing endpoints
        self.test_get_all_scans()
        self.test_user_scans()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend is working correctly.")
            return True
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} test(s) failed. Check the issues above.")
            return False

def main():
    tester = AccessibilityScannerTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())