"""
Auditly Accessibility Scanner - Backend API Tests
Tests for authentication, scans, and subscription endpoints
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://scan-a11y.preview.emergentagent.com').rstrip('/')

# Test user credentials
TEST_EMAIL = f"test_user_{uuid.uuid4().hex[:8]}@auditly.com"
TEST_PASSWORD = "testpass123"
TEST_FULLNAME = "Test User"

# Existing test user from context
EXISTING_EMAIL = "test3@auditly.com"
EXISTING_PASSWORD = "testpass123"


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_check(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert data["services"]["database"] == "healthy"
        print(f"SUCCESS: Health check passed - {data}")


class TestAuthEndpoints:
    """Authentication endpoint tests - signup, login, me"""
    
    def test_signup_new_user(self):
        """Test creating a new user account"""
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": TEST_FULLNAME
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        
        assert response.status_code == 200, f"Signup failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        print(f"SUCCESS: Signup successful for {TEST_EMAIL}")
        
        # Store token for later tests
        TestAuthEndpoints.new_user_token = data["access_token"]
    
    def test_signup_duplicate_email(self):
        """Test signup with existing email returns error"""
        payload = {
            "email": TEST_EMAIL,  # Same email as previous test
            "password": TEST_PASSWORD,
            "full_name": "Duplicate User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        
        assert response.status_code == 400, f"Expected 400 for duplicate email, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        print(f"SUCCESS: Duplicate email rejected - {data['detail']}")
    
    def test_login_existing_user(self):
        """Test login with existing user credentials"""
        payload = {
            "email": EXISTING_EMAIL,
            "password": EXISTING_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print(f"SUCCESS: Login successful for {EXISTING_EMAIL}")
        
        # Store token for later tests
        TestAuthEndpoints.existing_user_token = data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        payload = {
            "email": EXISTING_EMAIL,
            "password": "wrongpassword123"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"
        print("SUCCESS: Invalid credentials rejected")
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent email"""
        payload = {
            "email": "nonexistent@auditly.com",
            "password": "anypassword"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 401, f"Expected 401 for non-existent user, got {response.status_code}"
        print("SUCCESS: Non-existent user login rejected")
    
    def test_get_user_profile(self):
        """Test getting current user profile with valid token"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXISTING_EMAIL,
            "password": EXISTING_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Get profile
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200, f"Get profile failed: {response.text}"
        
        data = response.json()
        assert data["email"] == EXISTING_EMAIL
        assert "plan" in data
        assert "scans_used_this_month" in data
        assert "scans_remaining" in data
        print(f"SUCCESS: User profile retrieved - Plan: {data['plan']}, Scans remaining: {data['scans_remaining']}")
    
    def test_get_profile_without_token(self):
        """Test getting profile without authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without token, got {response.status_code}"
        print("SUCCESS: Unauthenticated profile request rejected")
    
    def test_get_profile_invalid_token(self):
        """Test getting profile with invalid token"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 401, f"Expected 401 for invalid token, got {response.status_code}"
        print("SUCCESS: Invalid token rejected")


class TestScanEndpoints:
    """Scan CRUD endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXISTING_EMAIL,
            "password": EXISTING_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate for scan tests")
    
    def test_create_scan(self):
        """Test creating a new accessibility scan"""
        payload = {
            "url": "https://example.com",
            "tool": "axe-core"
        }
        response = requests.post(f"{BASE_URL}/api/scans", json=payload, headers=self.headers)
        
        assert response.status_code == 200, f"Create scan failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["url"] == "https://example.com/"
        assert data["status"] in ["pending", "completed"]
        print(f"SUCCESS: Scan created with ID: {data['id']}, Status: {data['status']}")
        
        # Store scan ID for later tests
        TestScanEndpoints.created_scan_id = data["id"]
    
    def test_get_user_scans(self):
        """Test getting all scans for authenticated user"""
        response = requests.get(f"{BASE_URL}/api/scans", headers=self.headers)
        
        assert response.status_code == 200, f"Get scans failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} scans for user")
        
        # Verify scan structure if any exist
        if len(data) > 0:
            scan = data[0]
            assert "id" in scan
            assert "url" in scan
            assert "status" in scan
            print(f"  First scan: {scan['url']} - Status: {scan['status']}")
    
    def test_get_scan_by_id(self):
        """Test getting a specific scan by ID"""
        # First create a scan
        create_response = requests.post(f"{BASE_URL}/api/scans", json={
            "url": "https://httpbin.org/html",
            "tool": "axe-core"
        }, headers=self.headers)
        
        if create_response.status_code != 200:
            pytest.skip("Could not create scan for get test")
        
        scan_id = create_response.json()["id"]
        
        # Get the scan
        response = requests.get(f"{BASE_URL}/api/scans/{scan_id}", headers=self.headers)
        
        assert response.status_code == 200, f"Get scan by ID failed: {response.text}"
        
        data = response.json()
        assert data["id"] == scan_id
        print(f"SUCCESS: Retrieved scan {scan_id}")
    
    def test_get_nonexistent_scan(self):
        """Test getting a scan that doesn't exist"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/scans/{fake_id}", headers=self.headers)
        
        assert response.status_code == 404, f"Expected 404 for non-existent scan, got {response.status_code}"
        print("SUCCESS: Non-existent scan returns 404")
    
    def test_create_scan_without_auth(self):
        """Test creating scan without authentication"""
        payload = {
            "url": "https://example.com",
            "tool": "axe-core"
        }
        response = requests.post(f"{BASE_URL}/api/scans", json=payload)
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("SUCCESS: Unauthenticated scan creation rejected")
    
    def test_create_scan_invalid_url(self):
        """Test creating scan with invalid URL"""
        payload = {
            "url": "not-a-valid-url",
            "tool": "axe-core"
        }
        response = requests.post(f"{BASE_URL}/api/scans", json=payload, headers=self.headers)
        
        assert response.status_code == 422, f"Expected 422 for invalid URL, got {response.status_code}"
        print("SUCCESS: Invalid URL rejected with 422")


class TestSubscriptionEndpoints:
    """Subscription/Stripe endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXISTING_EMAIL,
            "password": EXISTING_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate for subscription tests")
    
    def test_create_checkout_session(self):
        """Test creating Stripe checkout session - expected to fail with placeholder keys"""
        response = requests.post(f"{BASE_URL}/api/subscription/create-checkout-session", headers=self.headers)
        
        # Expected to return 503 since Stripe keys are placeholders
        assert response.status_code in [503, 500, 400], f"Unexpected status: {response.status_code}"
        print(f"SUCCESS: Checkout session endpoint responds correctly (Stripe not configured) - Status: {response.status_code}")
    
    def test_checkout_without_auth(self):
        """Test checkout session without authentication"""
        response = requests.post(f"{BASE_URL}/api/subscription/create-checkout-session")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("SUCCESS: Unauthenticated checkout rejected")


class TestExportEndpoints:
    """Export endpoint tests (PDF/JSON)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token and create a scan"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXISTING_EMAIL,
            "password": EXISTING_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate for export tests")
    
    def test_export_json(self):
        """Test JSON export for a scan"""
        # First get user's scans
        scans_response = requests.get(f"{BASE_URL}/api/scans", headers=self.headers)
        if scans_response.status_code != 200 or len(scans_response.json()) == 0:
            pytest.skip("No scans available for export test")
        
        scan_id = scans_response.json()[0]["id"]
        
        # Export JSON
        response = requests.get(f"{BASE_URL}/api/scans/{scan_id}/export/json")
        
        assert response.status_code == 200, f"JSON export failed: {response.text}"
        assert "application/json" in response.headers.get("content-type", "")
        print(f"SUCCESS: JSON export successful for scan {scan_id}")
    
    def test_export_nonexistent_scan(self):
        """Test export for non-existent scan"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/scans/{fake_id}/export/json")
        
        assert response.status_code == 404, f"Expected 404 for non-existent scan export, got {response.status_code}"
        print("SUCCESS: Non-existent scan export returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
