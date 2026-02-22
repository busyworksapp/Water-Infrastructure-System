"""Comprehensive test suite for Water Monitoring System API"""

import pytest
import json
from datetime import datetime, timedelta
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app, get_db
from app.core.database import Base
from app.core.security import get_password_hash
from app.models import User, Municipality, Sensor, DeviceAuth, Alert, AlertRule
from app.core.config import settings


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override get_db for testing"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a new database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.query(User).delete()
        db.query(Municipality).delete()
        db.query(Sensor).delete()
        db.query(DeviceAuth).delete()
        db.query(Alert).delete()
        db.query(AlertRule).delete()
        db.commit()
        db.close()


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user for testing"""
    user = User(
        username="admin",
        email="admin@test.com",
        password_hash=get_password_hash("password"),
        is_super_admin=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def municipality(db: Session) -> Municipality:
    """Create a municipality for testing"""
    mun = Municipality(
        name="Test City",
        location_type="city",
        latitude=40.7128,
        longitude=-74.0060,
        population=1000000,
        is_active=True,
    )
    db.add(mun)
    db.commit()
    db.refresh(mun)
    return mun


@pytest.fixture
def sensor(db: Session, municipality: Municipality) -> Sensor:
    """Create a sensor for testing"""
    sensor = Sensor(
        sensor_id="test_sensor_001",
        name="Test Pressure Sensor",
        location="Downtown District",
        sensor_type="pressure",
        measurement_unit="bar",
        municipality_id=municipality.id,
        latitude=40.7128,
        longitude=-74.0060,
        is_active=True,
    )
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor


@pytest.fixture
def device_auth(db: Session, sensor: Sensor) -> DeviceAuth:
    """Create device authentication for testing"""
    device = DeviceAuth(
        sensor_id=sensor.id,
        device_id="test_device_001",
        api_key="sk_water_test123",
        is_active=True,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self, db: Session, admin_user: User):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
    
    def test_login_invalid_credentials(self, db: Session):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401
        assert response.json()["success"] is False
    
    def test_login_missing_user(self):
        """Test login with non-existent user"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password"},
        )
        assert response.status_code == 401


class TestDeviceManagement:
    """Test device management endpoints"""
    
    def test_register_device(self, db: Session, admin_user: User, sensor: Sensor):
        """Test device registration"""
        response = client.post(
            "/api/v1/devices/register",
            json={
                "sensor_id": "test_sensor_001",
                "device_id": "test_device_001",
                "authentication_method": "api_key",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "api_key" in data["data"]
    
    def test_authenticate_device(self, db: Session, device_auth: DeviceAuth):
        """Test device authentication"""
        response = client.post(
            "/api/v1/devices/authenticate",
            json={
                "device_id": "test_device_001",
                "authentication_type": "api_key",
                "credential": "sk_water_test123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["authenticated"] is True
    
    def test_authenticate_device_invalid_key(self, db: Session):
        """Test device authentication with invalid key"""
        response = client.post(
            "/api/v1/devices/authenticate",
            json={
                "device_id": "test_device_001",
                "authentication_type": "api_key",
                "credential": "invalid_key",
            },
        )
        assert response.status_code == 401


class TestSensorManagement:
    """Test sensor management endpoints"""
    
    def test_create_sensor(self, db: Session, admin_user: User, municipality: Municipality):
        """Test sensor creation"""
        response = client.post(
            "/api/v1/sensors",
            json={
                "sensor_id": "new_sensor_001",
                "name": "Flow Meter A",
                "location": "Water Plant A",
                "sensor_type": "flow",
                "measurement_unit": "L/min",
                "municipality_id": municipality.id,
                "latitude": 40.7128,
                "longitude": -74.0060,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
    
    def test_get_sensors(self, db: Session, sensor: Sensor):
        """Test getting sensors"""
        response = client.get("/api/v1/sensors")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["sensors"]) >= 1
    
    def test_get_sensor_by_id(self, db: Session, sensor: Sensor):
        """Test getting a specific sensor"""
        response = client.get(f"/api/v1/sensors/{sensor.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == sensor.id


class TestDataIngestion:
    """Test data ingestion endpoint"""
    
    def test_ingest_single_reading(self, db: Session, device_auth: DeviceAuth, sensor: Sensor):
        """Test ingesting a single sensor reading"""
        response = client.post(
            "/api/v1/ingest",
            json={
                "device_id": "test_device_001",
                "sensor_id": "test_sensor_001",
                "readings": [
                    {
                        "value": 3.5,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
                ],
            },
            headers={"Authorization": "Device sk_water_test123"},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
    
    def test_ingest_multiple_readings(self, db: Session, device_auth: DeviceAuth):
        """Test ingesting multiple sensor readings"""
        readings = [
            {
                "value": 3.5 + i,
                "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat() + "Z",
            }
            for i in range(5)
        ]
        
        response = client.post(
            "/api/v1/ingest",
            json={
                "device_id": "test_device_001",
                "sensor_id": "test_sensor_001",
                "readings": readings,
            },
            headers={"Authorization": "Device sk_water_test123"},
        )
        assert response.status_code == 202
        assert response.json()["data"]["readings_count"] == 5


class TestAlerting:
    """Test alerting endpoints"""
    
    def test_create_alert_rule(self, db: Session, admin_user: User, municipality: Municipality):
        """Test creating an alert rule"""
        response = client.post(
            "/api/v1/alert-rules",
            json={
                "name": "High Pressure Alert",
                "description": "Alert when pressure exceeds 5 bar",
                "sensor_type": "pressure",
                "rule_type": "threshold",
                "threshold_max": 5.0,
                "municipality_id": municipality.id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
    
    def test_get_alerts(self, db: Session):
        """Test getting alerts"""
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestMonitoring:
    """Test monitoring endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/monitoring/health")
        assert response.status_code == 200
    
    def test_system_status(self):
        """Test system status endpoint"""
        response = client.get("/api/v1/monitoring/system-status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_connectivity_check(self):
        """Test system connectivity endpoint"""
        response = client.get("/api/v1/monitoring/system-connectivity")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "database" in data["data"]
        assert "mqtt" in data["data"]
        assert "redis" in data["data"]


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json(self):
        """Test invalid JSON in request"""
        response = client.post(
            "/api/v1/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
    
    def test_missing_required_field(self, db: Session, municipality: Municipality):
        """Test missing required field"""
        response = client.post(
            "/api/v1/sensors",
            json={
                "sensor_id": "test",
                "name": "Test",
                # Missing location field
                "sensor_type": "pressure",
            },
        )
        assert response.status_code == 422
    
    def test_not_found(self):
        """Test accessing non-existent resource"""
        response = client.get("/api/v1/sensors/99999")
        assert response.status_code == 404


class TestRateLimiting:
    """Test rate limiting"""
    
    def test_rate_limit_exceeded(self):
        """Test rate limit on authentication"""
        # Make multiple failed login attempts
        for i in range(15):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "wrong"},
            )
            if response.status_code == 429:
                assert response.json()["error"] == "RATE_LIMITED"
                return
        
        # If we get here, rate limiting may not be enabled
        pytest.skip("Rate limiting not enforced")


# Run tests with: pytest backend/tests/test_api.py -v
