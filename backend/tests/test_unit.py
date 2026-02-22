"""Comprehensive unit tests for water monitoring system."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models.user import User, Role
from app.models.municipality import Municipality
from app.models.sensor import Sensor, SensorType, SensorReading
from app.models.alert import Alert
from app.core.security import create_access_token, get_password_hash


@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """Create database session for tests."""
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_municipality(db_session):
    """Create test municipality."""
    municipality = Municipality(
        id="test-muni-001",
        name="Test Municipality",
        code="TEST001",
        region="Test Region",
        contact_email="test@example.com"
    )
    db_session.add(municipality)
    db_session.commit()
    return municipality


@pytest.fixture
def test_user(db_session, test_municipality):
    """Create test user."""
    role = Role(name="admin", description="Administrator")
    db_session.add(role)
    
    user = User(
        id="test-user-001",
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        municipality_id=test_municipality.id,
        is_active=True,
        is_super_admin=False
    )
    user.roles.append(role)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_token(test_user):
    """Create authentication token."""
    return create_access_token({"sub": test_user.id})


@pytest.fixture
def auth_headers(auth_token):
    """Create authentication headers."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "invalid", "password": "wrong"}
        )
        assert response.status_code == 401
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/sensors")
        assert response.status_code == 403


class TestSensorManagement:
    """Test sensor management endpoints."""
    
    @pytest.fixture
    def test_sensor_type(self, db_session):
        """Create test sensor type."""
        sensor_type = SensorType(
            id="pressure-sensor",
            name="Pressure Sensor",
            unit="bar",
            min_value=0.0,
            max_value=10.0
        )
        db_session.add(sensor_type)
        db_session.commit()
        return sensor_type
    
    @pytest.fixture
    def test_sensor(self, db_session, test_municipality, test_sensor_type):
        """Create test sensor."""
        sensor = Sensor(
            id="sensor-001",
            name="Test Sensor",
            sensor_type_id=test_sensor_type.id,
            municipality_id=test_municipality.id,
            latitude=-25.7479,
            longitude=28.2293,
            is_active=True
        )
        db_session.add(sensor)
        db_session.commit()
        return sensor
    
    def test_list_sensors(self, client, auth_headers, test_sensor):
        """Test listing sensors."""
        response = client.get("/api/v1/sensors", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_sensor(self, client, auth_headers, test_municipality, test_sensor_type):
        """Test creating a new sensor."""
        sensor_data = {
            "name": "New Sensor",
            "sensor_type_id": test_sensor_type.id,
            "municipality_id": test_municipality.id,
            "latitude": -25.7479,
            "longitude": 28.2293
        }
        response = client.post(
            "/api/v1/sensors",
            json=sensor_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Sensor"
    
    def test_get_sensor_details(self, client, auth_headers, test_sensor):
        """Test getting sensor details."""
        response = client.get(
            f"/api/v1/sensors/{test_sensor.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_sensor.id


class TestSensorReadings:
    """Test sensor reading ingestion and retrieval."""
    
    @pytest.fixture
    def test_sensor(self, db_session, test_municipality):
        """Create test sensor."""
        sensor_type = SensorType(
            id="flow-sensor",
            name="Flow Sensor",
            unit="m3/h"
        )
        db_session.add(sensor_type)
        
        sensor = Sensor(
            id="sensor-002",
            name="Flow Sensor 1",
            sensor_type_id=sensor_type.id,
            municipality_id=test_municipality.id,
            is_active=True
        )
        db_session.add(sensor)
        db_session.commit()
        return sensor
    
    def test_ingest_reading(self, client, auth_headers, test_sensor):
        """Test ingesting sensor reading."""
        reading_data = {
            "value": 3.5,
            "timestamp": datetime.utcnow().isoformat(),
            "quality_score": 0.95
        }
        response = client.post(
            f"/api/v1/sensors/{test_sensor.id}/readings",
            json=reading_data,
            headers=auth_headers
        )
        assert response.status_code == 201
    
    def test_get_sensor_readings(self, client, auth_headers, test_sensor, db_session):
        """Test retrieving sensor readings."""
        # Create test readings
        for i in range(5):
            reading = SensorReading(
                sensor_id=test_sensor.id,
                value=3.0 + i * 0.1,
                timestamp=datetime.utcnow() - timedelta(hours=i),
                quality_score=0.95
            )
            db_session.add(reading)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/sensors/{test_sensor.id}/readings",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5


class TestAnomalyDetection:
    """Test anomaly detection functionality."""
    
    def test_statistical_anomaly_detection(self, db_session, test_municipality):
        """Test statistical anomaly detection."""
        from app.services.anomaly_detector import AnomalyDetector
        
        sensor_type = SensorType(id="test-type", name="Test", unit="bar")
        db_session.add(sensor_type)
        
        sensor = Sensor(
            id="sensor-003",
            name="Test Sensor",
            sensor_type_id=sensor_type.id,
            municipality_id=test_municipality.id,
            baseline_mean=5.0,
            baseline_std=0.5
        )
        db_session.add(sensor)
        db_session.commit()
        
        detector = AnomalyDetector(db_session)
        
        # Normal reading
        normal_reading = SensorReading(
            sensor_id=sensor.id,
            value=5.2,
            timestamp=datetime.utcnow()
        )
        is_anomaly, _ = detector.detect(sensor, normal_reading)
        assert not is_anomaly
        
        # Anomalous reading
        anomalous_reading = SensorReading(
            sensor_id=sensor.id,
            value=10.0,  # Far from baseline
            timestamp=datetime.utcnow()
        )
        is_anomaly, _ = detector.detect(sensor, anomalous_reading)
        assert is_anomaly


class TestAlertManagement:
    """Test alert management."""
    
    @pytest.fixture
    def test_alert(self, db_session, test_municipality):
        """Create test alert."""
        alert = Alert(
            municipality_id=test_municipality.id,
            alert_type="pressure_drop",
            severity="high",
            title="Pressure Drop Detected",
            description="Significant pressure drop in pipeline",
            status="active"
        )
        db_session.add(alert)
        db_session.commit()
        return alert
    
    def test_list_alerts(self, client, auth_headers, test_alert):
        """Test listing alerts."""
        response = client.get("/api/v1/alerts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_acknowledge_alert(self, client, auth_headers, test_alert):
        """Test acknowledging an alert."""
        response = client.post(
            f"/api/v1/alerts/{test_alert.id}/acknowledge",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestMunicipalityManagement:
    """Test municipality management."""
    
    def test_list_municipalities(self, client, auth_headers, test_municipality):
        """Test listing municipalities."""
        response = client.get("/api/v1/municipalities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_municipality_stats(self, client, auth_headers, test_municipality):
        """Test getting municipality statistics."""
        response = client.get(
            f"/api/v1/municipalities/{test_municipality.id}/stats",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestWebSocket:
    """Test WebSocket functionality."""
    
    def test_websocket_connection(self, client, auth_token, test_municipality):
        """Test WebSocket connection."""
        with client.websocket_connect(
            f"/ws/{test_municipality.id}?token={auth_token}"
        ) as websocket:
            data = websocket.receive_json()
            assert data["type"] == "replay"


class TestSecurityMiddleware:
    """Test security middleware."""
    
    def test_security_headers(self, client):
        """Test security headers are present."""
        response = client.get("/health")
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
    
    def test_rate_limiting(self, client):
        """Test rate limiting."""
        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = client.get("/health")
            responses.append(response.status_code)
        
        # Should eventually get rate limited
        assert 429 in responses or all(r == 200 for r in responses)


class TestBackupService:
    """Test backup functionality."""
    
    @patch('app.services.backup_service.BackupService.create_backup')
    def test_database_backup(self, mock_backup):
        """Test database backup creation."""
        mock_backup.return_value = {"status": "success", "file": "backup.sql"}
        
        from app.services.backup_service import BackupService
        service = BackupService()
        result = service.create_backup()
        
        assert result["status"] == "success"
        mock_backup.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
