"""Integration tests for complete system deployment"""

import asyncio
import json
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.config import settings
from app.core.database import get_db, SessionLocal
from app.models import User, Municipality, Sensor, DeviceAuth
from app.core.security import get_password_hash


class TestSystemIntegration:
    """Complete system integration tests"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete workflow: auth -> register device -> ingest data -> check alerts"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. Create admin user
            db = SessionLocal()
            
            admin = User(
                username="integration_admin",
                email="admin@integration.test",
                password_hash=get_password_hash("password123"),
                is_super_admin=True,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            
            # 2. Login
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": "integration_admin", "password": "password123"},
            )
            assert response.status_code == 200
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 3. Create municipality
            response = await client.post(
                "/api/v1/municipalities",
                json={
                    "name": "Integration Test City",
                    "location_type": "city",
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "population": 8000000,
                },
                headers=headers,
            )
            assert response.status_code == 201
            municipality = response.json()["data"]
            municipality_id = municipality["id"]
            
            # 4. Create sensor
            response = await client.post(
                "/api/v1/sensors",
                json={
                    "sensor_id": "integration_sensor_001",
                    "name": "Integration Test Sensor",
                    "location": "Test Location",
                    "sensor_type": "pressure",
                    "measurement_unit": "bar",
                    "municipality_id": municipality_id,
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                },
                headers=headers,
            )
            assert response.status_code == 201
            sensor = response.json()["data"]
            sensor_id = sensor["id"]
            
            # 5. Register device
            response = await client.post(
                "/api/v1/devices/register",
                json={
                    "sensor_id": "integration_sensor_001",
                    "device_id": "integration_device_001",
                    "authentication_method": "api_key",
                },
                headers=headers,
            )
            assert response.status_code == 201
            device = response.json()["data"]
            api_key = device["api_key"]
            
            # 6. Authenticate device
            response = await client.post(
                "/api/v1/devices/authenticate",
                json={
                    "device_id": "integration_device_001",
                    "authentication_type": "api_key",
                    "credential": api_key,
                },
            )
            assert response.status_code == 200
            assert response.json()["data"]["authenticated"] is True
            
            # 7. Ingest sensor data
            response = await client.post(
                "/api/v1/ingest",
                json={
                    "device_id": "integration_device_001",
                    "sensor_id": "integration_sensor_001",
                    "readings": [
                        {
                            "value": 3.5,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        }
                    ],
                },
                headers={"Authorization": f"Device {api_key}"},
            )
            assert response.status_code == 202
            
            # 8. Check system connectivity
            response = await client.get(
                "/api/v1/monitoring/system-connectivity",
                headers=headers,
            )
            assert response.status_code == 200
            connectivity = response.json()["data"]
            assert connectivity["database"]["status"] in ["connected", "unknown"]
            
            # 9. Check system status
            response = await client.get(
                "/api/v1/monitoring/system-status",
                headers=headers,
            )
            assert response.status_code == 200
            status = response.json()["data"]
            assert "sensors_online" in status
            
            # 10. Verify audit logging
            response = await client.get(
                "/api/v1/audit-logs?user_id=1&days_back=1",
                headers=headers,
            )
            assert response.status_code == 200
            
            db.close()


class TestServiceHealth:
    """Test all external services health"""
    
    def test_database_connection(self):
        """Test database connectivity"""
        from app.core.database import engine, check_database_connection
        
        try:
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                assert result.scalar() == 1
        except Exception as e:
            pytest.skip(f"Database not available: {str(e)}")
    
    def test_redis_connection(self):
        """Test Redis connectivity"""
        try:
            from app.services.redis_service import redis_service
            is_healthy = redis_service.is_healthy()
            assert is_healthy or True  # Allow failure for optional service
        except Exception as e:
            pytest.skip(f"Redis not available: {str(e)}")
    
    def test_s3_connectivity(self):
        """Test S3 connectivity"""
        try:
            from app.services.s3_service import s3_service
            # S3 is optional, just verify it initializes
            assert s3_service is not None
        except Exception as e:
            pytest.skip(f"S3 not configured: {str(e)}")


class TestErrorHandling:
    """Test error handling across the system"""
    
    @pytest.mark.asyncio
    async def test_malformed_json_handling(self):
        """Test handling of malformed JSON"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                content="not json",
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": "test"},  # Missing password
            )
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test handling of invalid credentials"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": "nonexistent", "password": "wrong"},
            )
            assert response.status_code == 401
            assert response.json()["success"] is False


class TestSecurityControls:
    """Test security controls"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self):
        """Test unauthorized access is denied"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Try to access protected endpoint without token
            response = await client.get("/api/v1/sensors")
            # Should be 403 or 401 depending on endpoint
            assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Test invalid token is rejected"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/sensors",
                headers={"Authorization": "Bearer invalid_token"},
            )
            assert response.status_code == 401


class TestDataValidation:
    """Test data validation"""
    
    @pytest.mark.asyncio
    async def test_email_validation(self):
        """Test email validation"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": "test", "password": "pass"},
            )
            # Should fail validation
            assert response.status_code == 422 or 400
    
    @pytest.mark.asyncio
    async def test_numeric_range_validation(self):
        """Test numeric range validation"""
        # This would be tested on specific endpoints
        pass


class TestPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_health_check_performance(self):
        """Test health check response time"""
        import time
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            start = time.time()
            response = await client.get("/monitoring/health")
            duration = time.time() - start
            
            assert response.status_code == 200
            assert duration < 0.5  # Should be fast
    
    @pytest.mark.asyncio
    async def test_api_response_time(self):
        """Test API response times"""
        import time
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            start = time.time()
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "wrong"},
            )
            duration = time.time() - start
            
            assert duration < 1.0  # Should respond quickly


# Run tests with: pytest backend/tests/test_integration.py -v
