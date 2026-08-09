"""
Tests for scheduled scans and notifications API endpoints.
Uses verifytest@example.com (Free plan, email verified).
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://remediation-lab.preview.emergentagent.com").rstrip("/")
EMAIL = "verifytest@example.com"
PASSWORD = "testpassword123"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed {r.status_code}: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# --- Limits endpoint ---
def test_limits_info(headers):
    r = requests.get(f"{BASE_URL}/api/scheduled-scans/limits/info", headers=headers, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    for k in ("plan", "limit", "used", "remaining", "can_create"):
        assert k in data
    assert data["plan"] == "free"
    assert data["limit"] == 1
    assert isinstance(data["used"], int)


# --- List endpoint ---
def test_get_scheduled_scans(headers):
    r = requests.get(f"{BASE_URL}/api/scheduled-scans", headers=headers, timeout=15)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


# --- Create + duplicate + delete + recreate flows ---
def test_scheduled_scan_lifecycle(headers):
    # Ensure clean slate: fetch existing and delete all first
    existing = requests.get(f"{BASE_URL}/api/scheduled-scans", headers=headers, timeout=15).json()
    for s in existing:
        requests.delete(f"{BASE_URL}/api/scheduled-scans/{s['id']}", headers=headers, timeout=15)

    # Create one
    payload = {"url": "https://test-lifecycle.example.com", "interval_days": 7}
    r = requests.post(f"{BASE_URL}/api/scheduled-scans", headers=headers, json=payload, timeout=15)
    assert r.status_code == 200, r.text
    created = r.json()
    scan_id = created["id"]
    assert created["interval_days"] == 7
    assert created["enabled"] is True
    assert "next_run" in created

    # GET it back
    r = requests.get(f"{BASE_URL}/api/scheduled-scans/{scan_id}", headers=headers, timeout=15)
    assert r.status_code == 200
    assert r.json()["id"] == scan_id

    # Free user is now at their limit (1/1). Attempting to create another
    # (whether duplicate or distinct URL) must be blocked. For Free plan the
    # limit check runs before the duplicate check, so expect 403 "limit reached".
    r = requests.post(f"{BASE_URL}/api/scheduled-scans", headers=headers, json=payload, timeout=15)
    assert r.status_code == 403, r.text
    assert "limit" in r.json().get("detail", "").lower()

    r = requests.post(
        f"{BASE_URL}/api/scheduled-scans",
        headers=headers,
        json={"url": "https://second-url.example.com", "interval_days": 1},
        timeout=15,
    )
    assert r.status_code == 403, r.text

    # Toggle (pause)
    r = requests.post(f"{BASE_URL}/api/scheduled-scans/{scan_id}/toggle", headers=headers, timeout=15)
    assert r.status_code == 200
    assert r.json()["enabled"] is False

    # Toggle again (resume)
    r = requests.post(f"{BASE_URL}/api/scheduled-scans/{scan_id}/toggle", headers=headers, timeout=15)
    assert r.status_code == 200
    assert r.json()["enabled"] is True

    # Update interval
    r = requests.put(
        f"{BASE_URL}/api/scheduled-scans/{scan_id}",
        headers=headers,
        json={"interval_days": 14},
        timeout=15,
    )
    assert r.status_code == 200
    assert r.json()["interval_days"] == 14

    # Delete
    r = requests.delete(f"{BASE_URL}/api/scheduled-scans/{scan_id}", headers=headers, timeout=15)
    assert r.status_code == 200

    # Verify deleted
    r = requests.get(f"{BASE_URL}/api/scheduled-scans/{scan_id}", headers=headers, timeout=15)
    assert r.status_code == 404


# --- Notifications endpoints ---
def test_notifications_endpoints(headers):
    r = requests.get(f"{BASE_URL}/api/notifications", headers=headers, timeout=15)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=headers, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "count" in data and isinstance(data["count"], int)

    # mark all read (idempotent)
    r = requests.put(f"{BASE_URL}/api/notifications/read-all", headers=headers, timeout=15)
    assert r.status_code == 200


# --- Auth required ---
def test_scheduled_scans_requires_auth():
    r = requests.get(f"{BASE_URL}/api/scheduled-scans", timeout=15)
    assert r.status_code in (401, 403)


def test_notifications_requires_auth():
    r = requests.get(f"{BASE_URL}/api/notifications", timeout=15)
    assert r.status_code in (401, 403)
