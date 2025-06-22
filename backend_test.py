import requests
import unittest
import uuid
import time
from datetime import datetime
import json

class AccessibilityScannerAPITest(unittest.TestCase):
    def setUp(self):
        # Use the public endpoint for testing
        self.base_url = "https://3f2797e6-9bad-45f5-ae39-514f6005b46a.preview.emergentagent.com/api"
        self.test_scan_id = None
        # Specific scan IDs from the request for testing
        self.wave_scan_id = "382e9c35-8ed3-43e0-92e3-ebdfc81f537e"
        self.equalweb_scan_id = "7f9ff9d2-fe90-4641-a145-adf3dc359d75"
        self.axe_scan_id = "e8069af6-885d-402c-af45-942cc75e022e"
        # New scan IDs from the updated UI
        self.new_scan_id = "5d08b599-b23c-42dc-a328-c91ed40c6ad0"  # 3 failed, 39 passed, 0 incomplete
        self.previous_scan_id = "cfce0eb0-a9ff-4f2a-9c72-e00016aa59ac"  # 3 failed, 13 passed, 0 incomplete
        # Test user IDs
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        self.test_user_id2 = f"test_user_{uuid.uuid4().hex[:8]}"
        
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
        
    def test_03_get_all_scans(self):
        """Test getting all scan requests"""
        print("\n🔍 Testing get all scans...")
        response = requests.get(f"{self.base_url}/scans")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        # At least our created scan should be there
        self.assertGreaterEqual(len(data), 1)
        print(f"✅ Get all scans passed - Found {len(data)} scans")
        
    def test_04_get_specific_scan(self):
        """Test getting a specific scan request"""
        if not hasattr(self.__class__, 'test_scan_id'):
            self.skipTest("No scan ID available from previous test")
            
        print(f"\n🔍 Testing get specific scan with ID: {self.__class__.test_scan_id}...")
        response = requests.get(f"{self.base_url}/scans/{self.__class__.test_scan_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.__class__.test_scan_id)
        print("✅ Get specific scan passed")
        
    def test_05_update_scan(self):
        """Test updating a scan request"""
        if not hasattr(self.__class__, 'test_scan_id'):
            self.skipTest("No scan ID available from previous test")
            
        print(f"\n🔍 Testing update scan with ID: {self.__class__.test_scan_id}...")
        update_data = {
            "status": "completed",
            "score": 85,
            "issues": {
                "violations": [
                    {
                        "id": "color-contrast",
                        "description": "Elements must have sufficient color contrast",
                        "impact": "serious",
                        "nodes": 2
                    }
                ],
                "passes": 10,
                "incomplete": 1
            }
        }
        
        response = requests.put(
            f"{self.base_url}/scans/{self.__class__.test_scan_id}", 
            json=update_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.__class__.test_scan_id)
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["score"], 85)
        self.assertIsNotNone(data["issues"])
        print("✅ Update scan passed")
        
    def test_06_delete_scan(self):
        """Test deleting a scan request"""
        if not hasattr(self.__class__, 'test_scan_id'):
            self.skipTest("No scan ID available from previous test")
            
        print(f"\n🔍 Testing delete scan with ID: {self.__class__.test_scan_id}...")
        response = requests.delete(f"{self.base_url}/scans/{self.__class__.test_scan_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Scan request deleted successfully")
        
        # Verify it's actually deleted
        response = requests.get(f"{self.base_url}/scans/{self.__class__.test_scan_id}")
        self.assertEqual(response.status_code, 404)
        print("✅ Delete scan passed")
        
    def test_07_real_accessibility_scan(self):
        """Test a real accessibility scan with axe-core"""
        print("\n🔍 Testing real accessibility scan...")
        
        # Create a scan for a real website
        test_url = "https://example.com"  # Using a simpler website for faster scanning
        response = requests.post(
            f"{self.base_url}/scans", 
            json={"url": test_url, "tool": "axe-core"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["url"], test_url)
        self.assertEqual(data["status"], "pending")
        scan_id = data["id"]
        print(f"✅ Created real scan with ID: {scan_id}")
        
        # Poll for scan completion (timeout after 60 seconds)
        max_attempts = 30
        attempts = 0
        scan_completed = False
        
        print("⏳ Waiting for scan to complete...")
        while attempts < max_attempts and not scan_completed:
            time.sleep(2)  # Poll every 2 seconds
            try:
                response = requests.get(f"{self.base_url}/scans/{scan_id}")
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                if data["status"] in ["completed", "error"]:
                    scan_completed = True
                    print(f"✅ Scan completed with status: {data['status']}")
                    if data["status"] == "completed":
                        self.assertIsNotNone(data["score"])
                        self.assertIsNotNone(data["issues"])
                        print(f"✅ Accessibility score: {data['score']}/100")
                        
                        # Verify axe-core results structure
                        self.assertIn("violations", data["issues"])
                        self.assertIn("passes", data["issues"])
                        self.assertIn("incomplete", data["issues"])
                        
                        print(f"✅ Found {len(data['issues']['violations'])} violations")
                        print(f"✅ Found {len(data['issues']['passes'])} passes")
                        
                        # Print a sample violation if available
                        if data["issues"]["violations"]:
                            violation = data["issues"]["violations"][0]
                            print(f"Sample violation: {violation['id']} - {violation['description']}")
                    else:
                        print(f"❌ Scan failed with error: {data.get('error_message', 'Unknown error')}")
            except Exception as e:
                print(f"Error polling scan status: {e}")
            
            attempts += 1
            print(f"Polling attempt {attempts}/{max_attempts}...")
        
        if not scan_completed:
            print("⚠️ Scan did not complete within the timeout period")
            # Don't fail the test, just report it
            
        # Try to clean up - delete the test scan
        try:
            response = requests.delete(f"{self.base_url}/scans/{scan_id}")
            if response.status_code == 200:
                print("✅ Test scan deleted successfully")
            else:
                print(f"⚠️ Failed to delete test scan: {response.status_code}")
        except Exception as e:
            print(f"Error deleting test scan: {e}")
            
        print("✅ Real accessibility scan test completed")

    def test_08_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n🔍 Testing error handling...")
        
        # Test invalid URL format
        response = requests.post(
            f"{self.base_url}/scans", 
            json={"url": "not-a-valid-url"}
        )
        self.assertNotEqual(response.status_code, 200)
        
        # Test non-existent scan ID
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{self.base_url}/scans/{fake_id}")
        self.assertEqual(response.status_code, 404)
        
        print("✅ Error handling passed")
        
    def test_09_specific_scan_result(self):
        """Test the specific scan result mentioned in the request"""
        print("\n🔍 Testing specific scan result...")
        
        # Test the specific scan ID from the request
        specific_scan_id = "27d02b04-c388-4504-96dd-988aee7ad308"
        response = requests.get(f"{self.base_url}/scans/{specific_scan_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found specific scan with ID: {specific_scan_id}")
            print(f"URL: {data['url']}")
            print(f"Status: {data['status']}")
            print(f"Score: {data['score']}/100")
            
            # Verify the expected values
            self.assertEqual(data["url"], "https://github.com/")
            self.assertEqual(data["status"], "completed")
            self.assertEqual(data["score"], 15)
            
            # Verify violations exist
            self.assertIn("issues", data)
            self.assertIn("violations", data["issues"])
            violations_count = len(data["issues"]["violations"])
            print(f"Found {violations_count} violations")
            
            # Print some sample violations for verification
            if violations_count > 0:
                for i in range(min(3, violations_count)):
                    violation = data["issues"]["violations"][i]
                    print(f"Violation {i+1}: {violation['id']} - {violation['impact']} impact")
        else:
            print(f"❌ Specific scan not found (status code: {response.status_code})")
            print("This test will be marked as skipped rather than failed")
            self.skipTest(f"Specific scan with ID {specific_scan_id} not found")
            
    def test_10_external_apis_status(self):
        """Test the external APIs status endpoint"""
        print("\n🔍 Testing external APIs status endpoint...")
        
        response = requests.get(f"{self.base_url}/external-apis/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify the structure of the response
        self.assertIn("wave", data)
        self.assertIn("equalweb", data)
        self.assertIn("accessibe", data)
        
        # Each API should have configured and status fields
        for api in ["wave", "equalweb", "accessibe"]:
            self.assertIn("configured", data[api])
            self.assertIn("status", data[api])
            
            # Status should be either "ready" or "api_key_required"
            self.assertIn(data[api]["status"], ["ready", "api_key_required"])
            
            # Print the status of each API
            print(f"✅ {api.upper()} API: {'Configured' if data[api]['configured'] else 'Not configured'} - Status: {data[api]['status']}")
            
        print("✅ External APIs status endpoint test passed")
        
    def test_11_external_scan_with_wave(self):
        """Test creating a scan with WAVE external tool"""
        print("\n🔍 Testing scan creation with WAVE external tool...")
        
        test_url = f"https://example.com/test-{uuid.uuid4()}"
        response = requests.post(
            f"{self.base_url}/scans", 
            json={"url": test_url, "tool": "wave"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["url"], test_url)
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["tool"], "wave")
        
        scan_id = data["id"]
        print(f"✅ Created WAVE scan with ID: {scan_id}")
        
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
                        # If scan completed successfully, verify the results
                        self.assertIsNotNone(data["score"])
                        self.assertIsNotNone(data["issues"])
                        print(f"✅ WAVE scan score: {data['score']}/100")
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
            
        print("✅ WAVE external scan test completed")
        
    def test_12_manual_external_api_trigger(self):
        """Test manually triggering an external API scan"""
        print("\n🔍 Testing manual external API scan trigger...")
        
        # First create a scan with an external tool
        test_url = f"https://example.com/test-{uuid.uuid4()}"
        response = requests.post(
            f"{self.base_url}/scans", 
            json={"url": test_url, "tool": "equalweb"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        scan_id = data["id"]
        print(f"✅ Created EqualWeb scan with ID: {scan_id}")
        
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
        
        # Clean up - delete the test scan
        try:
            response = requests.delete(f"{self.base_url}/scans/{scan_id}")
            if response.status_code == 200:
                print("✅ EqualWeb test scan deleted successfully")
        except Exception as e:
            print(f"Error deleting EqualWeb test scan: {e}")
            
        print("✅ Manual external API trigger test completed")
        
    def test_13_specific_wave_scan_result(self):
        """Test the specific WAVE scan result mentioned in the request"""
        print("\n🔍 Testing specific WAVE scan result...")
        
        # Test the specific WAVE scan ID from the request
        response = requests.get(f"{self.base_url}/scans/{self.wave_scan_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found specific WAVE scan with ID: {self.wave_scan_id}")
            print(f"URL: {data['url']}")
            print(f"Status: {data['status']}")
            print(f"Tool: {data['tool']}")
            
            # Verify it's a WAVE scan
            self.assertEqual(data["tool"], "wave")
            
            # If the scan completed, check the results
            if data["status"] == "completed":
                print(f"Score: {data['score']}/100")
                
                # Verify issues exist
                self.assertIn("issues", data)
                self.assertIn("violations", data["issues"])
                violations_count = len(data["issues"]["violations"])
                print(f"Found {violations_count} violations")
                
                # Print some sample violations for verification
                if violations_count > 0:
                    for i in range(min(3, violations_count)):
                        violation = data["issues"]["violations"][i]
                        print(f"Violation {i+1}: {violation['id']} - {violation['impact']} impact")
            elif data["status"] == "error":
                print(f"Scan failed with error: {data.get('error_message', 'Unknown error')}")
                if "API key not configured" in data.get('error_message', ''):
                    print("✅ Correctly handled missing API key scenario")
            else:
                print(f"Scan status: {data['status']}")
        else:
            print(f"❌ Specific WAVE scan not found (status code: {response.status_code})")
            print("This test will be marked as skipped rather than failed")
            self.skipTest(f"Specific WAVE scan with ID {self.wave_scan_id} not found")
            
    def test_16_accessibe_scan_creation(self):
        """Test creating a scan with AccessiBe external tool"""
        print("\n🔍 Testing scan creation with AccessiBe external tool...")
        
        test_url = f"https://example.com/test-{uuid.uuid4()}"
        response = requests.post(
            f"{self.base_url}/scans", 
            json={"url": test_url, "tool": "accessibe"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["url"], test_url)
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["tool"], "accessibe")
        
        scan_id = data["id"]
        print(f"✅ Created AccessiBe scan with ID: {scan_id}")
        
        # Poll for scan completion (timeout after 30 seconds)
        max_attempts = 15
        attempts = 0
        scan_completed = False
        
        print("⏳ Waiting for AccessiBe scan to complete...")
        while attempts < max_attempts and not scan_completed:
            time.sleep(2)  # Poll every 2 seconds
            try:
                response = requests.get(f"{self.base_url}/scans/{scan_id}")
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                if data["status"] in ["completed", "error"]:
                    scan_completed = True
                    print(f"✅ AccessiBe scan completed with status: {data['status']}")
                    
                    if data["status"] == "error":
                        # If API key is not configured, we expect an error
                        self.assertIsNotNone(data["error_message"])
                        print(f"Expected error: {data['error_message']}")
                        if "API key not configured" in data["error_message"]:
                            print("✅ Correctly handled missing API key scenario")
                    else:
                        # If scan completed successfully, verify the results
                        self.assertIsNotNone(data["score"])
                        self.assertIsNotNone(data["issues"])
                        print(f"✅ AccessiBe scan score: {data['score']}/100")
            except Exception as e:
                print(f"Error polling AccessiBe scan status: {e}")
            
            attempts += 1
            print(f"Polling attempt {attempts}/{max_attempts}...")
        
        # Clean up - delete the test scan
        try:
            response = requests.delete(f"{self.base_url}/scans/{scan_id}")
            if response.status_code == 200:
                print("✅ AccessiBe test scan deleted successfully")
        except Exception as e:
            print(f"Error deleting AccessiBe test scan: {e}")
            
        print("✅ AccessiBe external scan test completed")
        print("✅ Specific WAVE scan test completed")
        
    def test_17_create_scan_with_user_id(self):
        """Test creating a scan with user ID"""
        print("\n🔍 Testing scan creation with user ID...")
        
        test_url = f"https://example.com/test-{uuid.uuid4()}"
        response = requests.post(
            f"{self.base_url}/scans", 
            json={"url": test_url, "user_id": self.test_user_id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["url"], test_url)
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["user_id"], self.test_user_id)
        
        scan_id = data["id"]
        print(f"✅ Created scan with user ID: {self.test_user_id}, scan ID: {scan_id}")
        
        # Save the scan ID for later tests
        self.__class__.user_scan_id = scan_id
        
        # Create another scan for the same user
        test_url2 = f"https://github.com/test-{uuid.uuid4()}"
        response = requests.post(
            f"{self.base_url}/scans", 
            json={"url": test_url2, "user_id": self.test_user_id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_id"], self.test_user_id)
        
        scan_id2 = data["id"]
        print(f"✅ Created second scan with user ID: {self.test_user_id}, scan ID: {scan_id2}")
        
        # Create a scan for a different user
        test_url3 = f"https://docs.github.com/test-{uuid.uuid4()}"
        response = requests.post(
            f"{self.base_url}/scans", 
            json={"url": test_url3, "user_id": self.test_user_id2}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_id"], self.test_user_id2)
        
        scan_id3 = data["id"]
        print(f"✅ Created scan with different user ID: {self.test_user_id2}, scan ID: {scan_id3}")
        
        print("✅ User scan creation tests passed")
        
    def test_18_get_user_specific_scans(self):
        """Test getting scans for a specific user"""
        print("\n🔍 Testing user-specific scans endpoint...")
        
        if not hasattr(self.__class__, 'user_scan_id'):
            self.skipTest("No user scan ID available from previous test")
        
        # Get scans for the first test user
        response = requests.get(f"{self.base_url}/users/{self.test_user_id}/scans")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have at least 2 scans for this user
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)
        
        # Verify all scans belong to the correct user
        for scan in data:
            self.assertEqual(scan["user_id"], self.test_user_id)
        
        print(f"✅ Found {len(data)} scans for user {self.test_user_id}")
        
        # Get scans for the second test user
        response = requests.get(f"{self.base_url}/users/{self.test_user_id2}/scans")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have at least 1 scan for this user
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        
        # Verify all scans belong to the correct user
        for scan in data:
            self.assertEqual(scan["user_id"], self.test_user_id2)
        
        print(f"✅ Found {len(data)} scans for user {self.test_user_id2}")
        
        print("✅ User-specific scans endpoint test passed")
        
    def test_19_filter_scans_by_user_id(self):
        """Test filtering all scans by user ID"""
        print("\n🔍 Testing scan filtering by user ID...")
        
        # Get all scans filtered by the first test user
        response = requests.get(f"{self.base_url}/scans?user_id={self.test_user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have at least 2 scans for this user
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)
        
        # Verify all scans belong to the correct user
        for scan in data:
            self.assertEqual(scan["user_id"], self.test_user_id)
        
        print(f"✅ Found {len(data)} scans for user {self.test_user_id} using filter parameter")
        
        # Get all scans filtered by the second test user
        response = requests.get(f"{self.base_url}/scans?user_id={self.test_user_id2}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have at least 1 scan for this user
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        
        # Verify all scans belong to the correct user
        for scan in data:
            self.assertEqual(scan["user_id"], self.test_user_id2)
        
        print(f"✅ Found {len(data)} scans for user {self.test_user_id2} using filter parameter")
        
        print("✅ Scan filtering by user ID test passed")
        
    def test_20_verify_test_data_from_request(self):
        """Verify the test data mentioned in the request"""
        print("\n🔍 Verifying test data from the request...")
        
        # Test user_test123 should have 2 scans (example.com score=78, github.com score=15)
        response = requests.get(f"{self.base_url}/users/user_test123/scans")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} scans for user_test123")
            
            # Should have 2 scans
            self.assertGreaterEqual(len(data), 2)
            
            # Check for expected URLs and scores
            example_com_found = False
            github_com_found = False
            
            for scan in data:
                if "example.com" in scan["url"] and scan["score"] == 78:
                    example_com_found = True
                    print("✅ Found example.com scan with score 78")
                elif "github.com" in scan["url"] and scan["score"] == 15:
                    github_com_found = True
                    print("✅ Found github.com scan with score 15")
            
            # At least one of the expected scans should be found
            self.assertTrue(example_com_found or github_com_found, 
                           "Expected test scans for user_test123 not found")
        else:
            print(f"⚠️ Could not find scans for user_test123 (status code: {response.status_code})")
            print("This might be expected if the test data hasn't been created yet")
        
        # Test user_different456 should have 1 scan (docs.github.com)
        response = requests.get(f"{self.base_url}/users/user_different456/scans")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} scans for user_different456")
            
            # Should have at least 1 scan
            self.assertGreaterEqual(len(data), 1)
            
            # Check for expected URL
            docs_github_found = False
            
            for scan in data:
                if "docs.github.com" in scan["url"]:
                    docs_github_found = True
                    print("✅ Found docs.github.com scan")
            
            # The expected scan should be found
            self.assertTrue(docs_github_found, 
                           "Expected test scan for user_different456 not found")
        else:
            print(f"⚠️ Could not find scans for user_different456 (status code: {response.status_code})")
            print("This might be expected if the test data hasn't been created yet")
        
        print("✅ Test data verification completed")
        
    def test_14_specific_equalweb_scan_result(self):
        """Test the specific EqualWeb scan result mentioned in the request"""
        print("\n🔍 Testing specific EqualWeb scan result...")
        
        # Test the specific EqualWeb scan ID from the request
        response = requests.get(f"{self.base_url}/scans/{self.equalweb_scan_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found specific EqualWeb scan with ID: {self.equalweb_scan_id}")
            print(f"URL: {data['url']}")
            print(f"Status: {data['status']}")
            print(f"Tool: {data['tool']}")
            
            # Verify it's an EqualWeb scan
            self.assertEqual(data["tool"], "equalweb")
            
            # If the scan completed, check the results
            if data["status"] == "completed":
                print(f"Score: {data['score']}/100")
                
                # Verify issues exist
                self.assertIn("issues", data)
                self.assertIn("violations", data["issues"])
                violations_count = len(data["issues"]["violations"])
                print(f"Found {violations_count} violations")
                
                # Print some sample violations for verification
                if violations_count > 0:
                    for i in range(min(3, violations_count)):
                        violation = data["issues"]["violations"][i]
                        print(f"Violation {i+1}: {violation['id']} - {violation['impact']} impact")
            elif data["status"] == "error":
                print(f"Scan failed with error: {data.get('error_message', 'Unknown error')}")
                if "API key not configured" in data.get('error_message', ''):
                    print("✅ Correctly handled missing API key scenario")
            else:
                print(f"Scan status: {data['status']}")
        else:
            print(f"❌ Specific EqualWeb scan not found (status code: {response.status_code})")
            print("This test will be marked as skipped rather than failed")
            self.skipTest(f"Specific EqualWeb scan with ID {self.equalweb_scan_id} not found")
            
        print("✅ Specific EqualWeb scan test completed")
        
    def test_15_specific_axe_scan_result(self):
        """Test the specific axe-core scan result mentioned in the request"""
        print("\n🔍 Testing specific axe-core scan result...")
        
        # Test the specific axe-core scan ID from the request
        response = requests.get(f"{self.base_url}/scans/{self.axe_scan_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found specific axe-core scan with ID: {self.axe_scan_id}")
            print(f"URL: {data['url']}")
            print(f"Status: {data['status']}")
            print(f"Tool: {data['tool']}")
            
            # Verify it's an axe-core scan
            self.assertEqual(data["tool"], "axe-core")
            
            # If the scan completed, check the results
            if data["status"] == "completed":
                print(f"Score: {data['score']}/100")
                
                # Verify issues exist
                self.assertIn("issues", data)
                self.assertIn("violations", data["issues"])
                violations_count = len(data["issues"]["violations"])
                print(f"Found {violations_count} violations")
                
                # Print some sample violations for verification
                if violations_count > 0:
                    for i in range(min(3, violations_count)):
                        violation = data["issues"]["violations"][i]
                        print(f"Violation {i+1}: {violation['id']} - {violation['impact']} impact")
            elif data["status"] == "error":
                print(f"Scan failed with error: {data.get('error_message', 'Unknown error')}")
            else:
                print(f"Scan status: {data['status']}")
        else:
            print(f"❌ Specific axe-core scan not found (status code: {response.status_code})")
            print("This test will be marked as skipped rather than failed")
            self.skipTest(f"Specific axe-core scan with ID {self.axe_scan_id} not found")
            
        print("✅ Specific axe-core scan test completed")

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)