# API Documentation & Integration Guide

## Overview

Your National Water Infrastructure Monitoring System provides a comprehensive REST API for managing water infrastructure monitoring, alerting, and reporting.

## Base URL

```
https://your-app.railway.app/api/v1
```

## Authentication

All endpoints (except `/auth/login` and `/devices/authenticate`) require a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Obtaining a Token

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## Error Response Format

All error responses follow this standard format:

```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "Human readable error message",
  "details": {},
  "request_id": "req_123456",
  "timestamp": "2026-02-22T10:30:00Z"
}
```

## Success Response Format

All success responses follow this standard format:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {},
  "request_id": "req_123456",
  "timestamp": "2026-02-22T10:30:00Z"
}
```

---

## Authentication Endpoints

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "expires_in": 1800
  }
}
```

---

## Device Management Endpoints

### Register Device

Register a new sensor device with authentication credentials.

```http
POST /api/v1/devices/register
Authorization: Bearer <token>
Content-Type: application/json

{
  "sensor_id": "sensor_001",
  "device_id": "device_001",
  "authentication_method": "api_key",
  "certificate_pem": null,
  "mqtt_password": null
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "device_id": "device_001",
    "api_key": "sk_water_...",
    "certificate_pem": null,
    "mqtt_username": null,
    "mqtt_password": null
  }
}
```

### Authenticate Device

Verify device credentials for data ingestion.

```http
POST /api/v1/devices/authenticate
Content-Type: application/json

{
  "device_id": "device_001",
  "authentication_type": "api_key",
  "credential": "sk_water_..."
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "authenticated": true,
    "device_id": "device_001",
    "expires_at": "2026-02-23T10:30:00Z"
  }
}
```

### List Devices

```http
GET /api/v1/devices?municipality_id=1&is_active=true
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "devices": [
      {
        "device_id": "device_001",
        "sensor_id": "sensor_001",
        "is_active": true,
        "last_authenticated": "2026-02-22T09:30:00Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 100
  }
}
```

### Get Device Info

```http
GET /api/v1/devices/{device_id}
Authorization: Bearer <token>
```

### Refresh API Key

```http
POST /api/v1/devices/{device_id}/refresh-api-key
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "device_id": "device_001",
    "api_key": "sk_water_...",
    "expires_at": "2026-02-24T10:30:00Z"
  }
}
```

### Generate Certificate

```http
POST /api/v1/devices/certificates/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "device_id": "device_001",
  "common_name": "sensor-001.water.local",
  "validity_days": 365
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "certificate_pem": "-----BEGIN CERTIFICATE-----...",
    "fingerprint": "SHA256:...",
    "expires_at": "2027-02-22T10:30:00Z"
  }
}
```

---

## Sensor Endpoints

### Get All Sensors

```http
GET /api/v1/sensors?municipality_id=1&sensor_type=pressure&is_active=true
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "sensors": [
      {
        "id": 1,
        "sensor_id": "sensor_001",
        "name": "Main Pressure Sensor",
        "location": "Downtown District",
        "sensor_type": "pressure",
        "measurement_unit": "bar",
        "municipality_id": 1,
        "is_active": true,
        "last_reading_at": "2026-02-22T10:25:00Z",
        "battery_level": 85.5,
        "signal_strength": -65
      }
    ],
    "total": 1
  }
}
```

### Create Sensor

```http
POST /api/v1/sensors
Authorization: Bearer <token>
Content-Type: application/json

{
  "sensor_id": "sensor_002",
  "name": "Flow Meter - Sector A",
  "location": "Water Plant A",
  "sensor_type": "flow",
  "measurement_unit": "L/min",
  "municipality_id": 1,
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

### Get Sensor Details

```http
GET /api/v1/sensors/{sensor_id}
Authorization: Bearer <token>
```

### Get Sensor Readings

```http
GET /api/v1/sensors/{sensor_id}/readings?start_time=2026-02-20T00:00:00Z&end_time=2026-02-22T23:59:59Z&limit=1000
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "readings": [
      {
        "id": 1,
        "value": 3.5,
        "timestamp": "2026-02-22T10:25:00Z",
        "metadata": {}
      }
    ],
    "total": 150
  }
}
```

---

## Data Ingestion Endpoint

### Ingest Sensor Data

```http
POST /api/v1/ingest
Authorization: Device <api_key>
Content-Type: application/json

{
  "device_id": "device_001",
  "sensor_id": "sensor_001",
  "readings": [
    {
      "value": 3.5,
      "timestamp": "2026-02-22T10:25:00Z",
      "metadata": {
        "battery": 85,
        "signal": -65
      }
    }
  ]
}
```

**Response (202):**
```json
{
  "success": true,
  "message": "Readings accepted for processing",
  "data": {
    "readings_count": 1,
    "alerts_triggered": 0
  }
}
```

---

## Alert & Incident Endpoints

### Get Alerts

```http
GET /api/v1/alerts?municipality_id=1&severity=high&is_resolved=false
Authorization: Bearer <token>
```

### Create Alert Rule

```http
POST /api/v1/alert-rules
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "High Pressure Alert",
  "description": "Alert when pressure exceeds 5 bar",
  "sensor_type": "pressure",
  "rule_type": "threshold",
  "threshold_max": 5.0,
  "municipality_id": 1
}
```

### Get Incidents

```http
GET /api/v1/incidents?municipality_id=1&status=open
Authorization: Bearer <token>
```

### Create Incident

```http
POST /api/v1/incidents
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Water Outage - Downtown",
  "description": "Complete water loss in downtown area",
  "municipality_id": 1,
  "severity": "critical"
}
```

### Update Incident

```http
PUT /api/v1/incidents/{incident_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "closed",
  "resolution_notes": "Issue resolved. Main line repaired."
}
```

---

## Monitoring Endpoints

### System Health

```http
GET /api/v1/monitoring/health
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2026-02-22T10:30:00Z"
  }
}
```

### System Status

```http
GET /api/v1/monitoring/system-status
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "uptime": 86400,
    "sensors_online": 145,
    "sensors_offline": 3,
    "alerts_active": 5,
    "incidents_open": 2
  }
}
```

### System Connectivity

```http
GET /api/v1/monitoring/system-connectivity
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "database": {
      "status": "connected",
      "type": "postgresql"
    },
    "mqtt": {
      "status": "connected",
      "broker": "mosquitto:1883",
      "subscriptions": 148
    },
    "redis": {
      "status": "connected",
      "memory_used": "256MB"
    },
    "s3": {
      "status": "configured",
      "bucket": "water-backups"
    },
    "overall_status": "healthy"
  }
}
```

### Metrics (Prometheus Format)

```http
GET /api/v1/monitoring/metrics
Authorization: Bearer <token>
```

---

## Admin Endpoints

### Create Municipality

```http
POST /api/v1/municipalities
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "City of New York",
  "location_type": "city",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "population": 8000000
}
```

### Create User

```http
POST /api/v1/users
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "username": "john.doe",
  "email": "john@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe",
  "role": "operator",
  "municipality_id": 1
}
```

### Get Audit Log

```http
GET /api/v1/audit-logs?user_id=1&action=create&days_back=7
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": 1,
        "user_id": 1,
        "action": "create",
        "resource_type": "sensor",
        "resource_id": "sensor_001",
        "ip_address": "192.168.1.1",
        "status": "success",
        "created_at": "2026-02-22T10:25:00Z"
      }
    ],
    "total": 5
  }
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| INVALID_CREDENTIALS | Authentication failed |
| INVALID_TOKEN | JWT token invalid or expired |
| UNAUTHORIZED | User lacks required permissions |
| NOT_FOUND | Resource not found |
| VALIDATION_ERROR | Input validation failed |
| DEVICE_AUTH_FAILED | Device authentication failed |
| RATE_LIMITED | Too many requests |
| INTERNAL_ERROR | Server error |

---

## Rate Limiting

- Standard endpoints: 100 requests/minute per IP
- Authentication endpoints: 10 requests/minute per IP
- Data ingestion: 1000 requests/minute per device

Rate limit status is returned in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1645521600
```

---

## Integration Examples

### Python

```python
import requests

# Login
response = requests.post(
    "https://your-app.railway.app/api/v1/auth/login",
    json={"username": "admin", "password": "password"}
)
token = response.json()["data"]["access_token"]

# Get sensors
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "https://your-app.railway.app/api/v1/sensors",
    headers=headers
)
sensors = response.json()["data"]["sensors"]

# Ingest data
response = requests.post(
    "https://your-app.railway.app/api/v1/ingest",
    headers={"Authorization": f"Device {api_key}"},
    json={
        "device_id": "device_001",
        "sensor_id": "sensor_001",
        "readings": [
            {
                "value": 3.5,
                "timestamp": "2026-02-22T10:25:00Z"
            }
        ]
    }
)
```

### cURL

```bash
# Login
curl -X POST https://your-app.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Get sensors
curl https://your-app.railway.app/api/v1/sensors \
  -H "Authorization: Bearer $TOKEN"

# Ingest data
curl -X POST https://your-app.railway.app/api/v1/ingest \
  -H "Authorization: Device $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id":"device_001",
    "sensor_id":"sensor_001",
    "readings":[{"value":3.5,"timestamp":"2026-02-22T10:25:00Z"}]
  }'
```

---

## WebSocket Real-Time Updates

Connect to receive real-time sensor data and alerts:

```
ws://your-app.railway.app/ws?token=<access_token>&municipality_id=1
```

**Messages:**
```json
{
  "type": "sensor_reading",
  "sensor_id": "sensor_001",
  "value": 3.5,
  "timestamp": "2026-02-22T10:25:00Z"
}
```

```json
{
  "type": "alert",
  "alert_id": 123,
  "severity": "high",
  "message": "Pressure exceeds threshold"
}
```

---

## Support & Documentation

- API Swagger: https://your-app.railway.app/docs
- API ReDoc: https://your-app.railway.app/redoc
- Deployment Guide: See RAILWAY_DEPLOYMENT_GUIDE.md
- System Architecture: See ARCHITECTURE.md

---

**Version**: 2.0.1  
**Last Updated**: February 22, 2026
