"""Comprehensive API testing script."""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
        self.municipality_id = None
        self.sensor_id = None
    
    def test_health(self):
        """Test health endpoint."""
        print("\n=== Testing Health Endpoint ===")
        response = requests.get(f"{self.base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    
    def test_login(self, email: str = "admin@example.com", password: str = "admin123"):
        """Test login and get token."""
        print("\n=== Testing Login ===")
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            print("Login successful, token obtained")
            return True
        else:
            print(f"Login failed: {response.text}")
            return False
    
    def get_headers(self):
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_municipalities(self):
        """Test municipalities endpoint."""
        print("\n=== Testing Municipalities ===")
        response = requests.get(
            f"{self.base_url}/api/v1/municipalities",
            headers=self.get_headers()
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} municipalities")
            if data:
                self.municipality_id = data[0]["id"]
                print(f"Using municipality: {data[0]['name']}")
            return True
        return False
    
    def test_sensors(self):
        """Test sensors endpoint."""
        print("\n=== Testing Sensors ===")
        response = requests.get(
            f"{self.base_url}/api/v1/sensors",
            headers=self.get_headers()
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} sensors")
            if data:
                self.sensor_id = data[0]["id"]
                print(f"Using sensor: {data[0]['name']}")
            return True
        return False
    
    def test_alerts(self):
        """Test alerts endpoint."""
        print("\n=== Testing Alerts ===")
        response = requests.get(
            f"{self.base_url}/api/v1/alerts",
            headers=self.get_headers()
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} alerts")
            return True
        return False
    
    def test_analytics(self):
        """Test analytics endpoint."""
        print("\n=== Testing Analytics ===")
        response = requests.get(
            f"{self.base_url}/api/v1/analytics/summary",
            headers=self.get_headers()
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Analytics data retrieved successfully")
            return True
        return False
    
    def test_system_health(self):
        """Test system health monitoring."""
        print("\n=== Testing System Health ===")
        response = requests.get(
            f"{self.base_url}/api/v1/system/health/comprehensive",
            headers=self.get_headers()
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Overall Status: {data.get('overall_status')}")
            print(f"Components: {list(data.get('components', {}).keys())}")
            return True
        return False
    
    def test_performance_monitoring(self):
        """Test performance monitoring."""
        print("\n=== Testing Performance Monitoring ===")
        response = requests.get(
            f"{self.base_url}/api/v1/system/performance/slow-endpoints",
            headers=self.get_headers()
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data.get('total', 0)} slow endpoints")
            return True
        return False
    
    def test_advanced_analytics(self):
        """Test advanced analytics endpoints."""
        print("\n=== Testing Advanced Analytics ===")
        if not self.municipality_id:
            print("Skipping: No municipality ID available")
            return False
        
        response = requests.get(
            f"{self.base_url}/api/v1/advanced/geospatial/pressure-heatmap",
            params={"municipality_id": self.municipality_id},
            headers=self.get_headers()
        )
        print(f"Status: {response.status_code}")
        return response.status_code in [200, 404]  # 404 if no data
    
    def test_data_export(self):
        """Test data export functionality."""
        print("\n=== Testing Data Export ===")
        if not self.sensor_id:
            print("Skipping: No sensor ID available")
            return False
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        response = requests.get(
            f"{self.base_url}/api/v1/system/export/sensor-readings/{self.sensor_id}",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": "csv"
            },
            headers=self.get_headers()
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Export size: {len(response.content)} bytes")
            return True
        return False
    
    def run_all_tests(self):
        """Run all API tests."""
        print("=" * 60)
        print("COMPREHENSIVE API TEST SUITE")
        print("=" * 60)
        
        results = {}
        
        # Basic tests
        results["Health Check"] = self.test_health()
        results["Login"] = self.test_login()
        
        if not self.token:
            print("\n❌ Cannot continue without authentication token")
            return results
        
        # Core functionality tests
        results["Municipalities"] = self.test_municipalities()
        results["Sensors"] = self.test_sensors()
        results["Alerts"] = self.test_alerts()
        results["Analytics"] = self.test_analytics()
        
        # Advanced features tests
        results["System Health"] = self.test_system_health()
        results["Performance Monitoring"] = self.test_performance_monitoring()
        results["Advanced Analytics"] = self.test_advanced_analytics()
        results["Data Export"] = self.test_data_export()
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test:.<40} {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        return results


if __name__ == "__main__":
    tester = APITester(BASE_URL)
    tester.run_all_tests()
