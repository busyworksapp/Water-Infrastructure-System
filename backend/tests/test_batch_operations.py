"""Test batch operations."""
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TOKEN = None

def login():
    """Login and get token."""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    if response.status_code == 200:
        global TOKEN
        TOKEN = response.json()["access_token"]
        print("✅ Login successful")
        return True
    print("❌ Login failed")
    return False

def test_bulk_readings():
    """Test bulk reading insertion."""
    readings = [
        {"sensor_id": "SENSOR_001", "value": 3.5, "unit": "bar"},
        {"sensor_id": "SENSOR_002", "value": 4.2, "unit": "bar"},
        {"sensor_id": "SENSOR_003", "value": 2.8, "unit": "bar"}
    ]
    
    response = requests.post(
        f"{BASE_URL}/api/v1/batch/readings",
        json=readings,
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    
    print(f"\n📊 Bulk Readings: {response.status_code}")
    if response.status_code == 200:
        print(f"   Result: {response.json()}")
        return True
    return False

def test_cache_warming():
    """Test cache warming."""
    response = requests.post(
        f"{BASE_URL}/api/v1/batch/cache/warm",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    
    print(f"\n🔥 Cache Warming: {response.status_code}")
    if response.status_code == 200:
        print(f"   Result: {response.json()}")
        return True
    return False

if __name__ == "__main__":
    print("=" * 50)
    print("BATCH OPERATIONS TEST")
    print("=" * 50)
    
    if login():
        test_bulk_readings()
        test_cache_warming()
