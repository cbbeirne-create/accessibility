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
        
    def test_07_error_handling(self):
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

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)