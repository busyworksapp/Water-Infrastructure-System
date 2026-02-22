# 📚 COMPLETE API DOCUMENTATION

## National Water Infrastructure Monitoring System API v2.0

**Base URL:** `http://localhost:8000/api/v1`

---

## 🔐 AUTHENTICATION

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Refresh Token
```http
POST /auth/refresh
Authorization: Bearer {refresh_token}

Response:
{
  "access_token": "new_token_here"
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer {access_token}
```

---

## 🌡️ SENSORS

### List All Sensors
```http
GET /sensors
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)
- is_active (optional)
- skip (default: 0)
- limit (default: 100)
```

### Get Sensor Details
```http
GET /sensors/{sensor_id}
Authorization: Bearer {token}
```

### Create Sensor
```http
POST /sensors
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Pressure Sensor 001",
  "device_id": "SENSOR_001",
  "sensor_type_id": 1,
  "municipality_id": 1,
  "latitude": -26.2041,
  "longitude": 28.0473,
  "is_active": true
}
```

### Update Sensor
```http
PUT /sensors/{sensor_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Name",
  "is_active": false
}
```

### Delete Sensor
```http
DELETE /sensors/{sensor_id}
Authorization: Bearer {token}
```

### Get Sensor Readings
```http
GET /sensors/{sensor_id}/readings
Authorization: Bearer {token}

Query Parameters:
- days (default: 7)
- limit (default: 1000)
```

### Get Sensor Statistics
```http
GET /sensors/{sensor_id}/stats
Authorization: Bearer {token}

Query Parameters:
- days (default: 7)
```

---

## 🚨 ALERTS

### List Alerts
```http
GET /alerts
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)
- severity (optional): critical, high, medium, low
- resolved (optional): true, false
- days (default: 7)
```

### Get Alert Details
```http
GET /alerts/{alert_id}
Authorization: Bearer {token}
```

### Resolve Alert
```http
POST /alerts/{alert_id}/resolve
Authorization: Bearer {token}
Content-Type: application/json

{
  "notes": "Issue fixed by replacing valve"
}
```

### Get Alert Statistics
```http
GET /alerts/stats
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)
- days (default: 30)
```

---

## 🗺️ GEOSPATIAL

### Find Nearby Sensors
```http
GET /geo/nearby
Authorization: Bearer {token}

Query Parameters:
- lat (required): -26.2041
- lon (required): 28.0473
- radius_km (default: 5)
```

### Get Pipeline Sensors
```http
GET /geo/pipelines/{pipeline_id}/sensors
Authorization: Bearer {token}

Query Parameters:
- buffer_meters (default: 100)
```

### Calculate Pipeline Length
```http
GET /geo/pipelines/{pipeline_id}/length
Authorization: Bearer {token}
```

### Get Municipality Bounds
```http
GET /geo/municipalities/{municipality_id}/bounds
Authorization: Bearer {token}
```

### Get Sensor Clusters
```http
GET /geo/clusters
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)
- grid_size (default: 1000)
```

---

## 📊 DASHBOARD

### System Overview
```http
GET /dashboard/overview
Authorization: Bearer {token}

Response:
{
  "total_sensors": 150,
  "active_sensors": 145,
  "inactive_sensors": 5,
  "total_municipalities": 10,
  "active_alerts": 12,
  "critical_alerts": 3,
  "system_health": 92.5
}
```

### Municipality Dashboard
```http
GET /dashboard/municipality/{municipality_id}
Authorization: Bearer {token}
```

### Sensor Health Summary
```http
GET /dashboard/sensor-health
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)

Response:
{
  "healthy": 120,
  "warning": 15,
  "critical": 5,
  "offline": 10
}
```

### Recent Activity
```http
GET /dashboard/activity
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)
- limit (default: 10)
```

### Alert Summary
```http
GET /dashboard/alerts/summary
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)
- days (default: 7)
```

### Sensor Uptime
```http
GET /dashboard/sensors/{sensor_id}/uptime
Authorization: Bearer {token}

Query Parameters:
- hours (default: 24)
```

---

## 📈 ANALYTICS

### Dashboard Analytics
```http
GET /analytics/dashboard
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)
- days (default: 7)
```

### Trends Analysis
```http
GET /analytics/trends
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)
- days (default: 30)
```

### Sensor Health Analysis
```http
GET /analytics/sensors/{sensor_id}/health
Authorization: Bearer {token}
```

### Top Alerts
```http
GET /analytics/top-alerts
Authorization: Bearer {token}

Query Parameters:
- limit (default: 10)
- days (default: 30)
```

### Predictive Maintenance
```http
GET /analytics/predictive-maintenance
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)
```

---

## 📄 REPORTS & EXPORT

### Export Sensor Readings
```http
GET /reports/sensors/{sensor_id}/export
Authorization: Bearer {token}

Query Parameters:
- days (default: 7)
- format: csv, json

Response: CSV or JSON file download
```

### Export Alerts
```http
GET /reports/alerts/export
Authorization: Bearer {token}

Query Parameters:
- days (default: 30)
- format: csv, json
- severity (optional)
```

### Municipality Report
```http
GET /reports/municipality/{municipality_id}
Authorization: Bearer {token}

Query Parameters:
- days (default: 30)
```

### System Summary Report
```http
GET /reports/system/summary
Authorization: Bearer {token}
```

---

## 📥 DATA INGESTION

### HTTP Sensor Data
```http
POST /ingest/sensors/{sensor_id}/readings
Authorization: Bearer {device_api_key}
Content-Type: application/json

{
  "timestamp": "2024-01-15T10:30:00Z",
  "value": 3.5,
  "unit": "bar",
  "quality": 0.98
}
```

### Batch Readings
```http
POST /ingest/sensors/{sensor_id}/readings/batch
Authorization: Bearer {device_api_key}
Content-Type: application/json

{
  "readings": [
    {"timestamp": "2024-01-15T10:30:00Z", "value": 3.5},
    {"timestamp": "2024-01-15T10:35:00Z", "value": 3.6}
  ]
}
```

---

## 🌐 IOT PROTOCOLS

### LoRaWAN Uplink
```http
POST /iot/lorawan/uplink
Content-Type: application/json

{
  "device_eui": "0004A30B001A2B3C",
  "payload": "0167FFD70268FF9C",
  "rssi": -85,
  "snr": 7.5,
  "frequency": 868.1
}
```

### NB-IoT Message
```http
POST /iot/nbiot/message
Content-Type: application/json

{
  "imei": "860123456789012",
  "value": 3.5,
  "signal_strength": 85,
  "battery_level": 92
}
```

### List Protocols
```http
GET /iot/protocols

Response:
{
  "protocols": [
    {"name": "MQTT", "status": "active", "port": 1883},
    {"name": "HTTP/HTTPS", "status": "active"},
    {"name": "TCP", "status": "active", "port": 9999},
    {"name": "LoRaWAN", "status": "active"},
    {"name": "NB-IoT", "status": "active"}
  ]
}
```

---

## 🎛️ ADMIN

### Create Sensor Type
```http
POST /admin/sensor-types
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "name": "Flow Meter",
  "unit": "L/min",
  "min_value": 0,
  "max_value": 1000,
  "description": "Water flow measurement"
}
```

### Create Dynamic Rule
```http
POST /admin/rules
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "name": "High Pressure Alert",
  "sensor_type_id": 1,
  "condition": "value > threshold",
  "threshold": 8.0,
  "severity": "high",
  "enabled": true
}
```

### System Statistics
```http
GET /admin/stats
Authorization: Bearer {admin_token}
```

### Audit Logs
```http
GET /admin/audit-logs
Authorization: Bearer {admin_token}

Query Parameters:
- days (default: 7)
- limit (default: 100)
```

---

## 🔧 MONITORING

### Health Check
```http
GET /monitoring/health

Response:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "mqtt": "connected"
}
```

### System Metrics
```http
GET /monitoring/metrics
Authorization: Bearer {token}

Response:
{
  "cpu_percent": 45.2,
  "memory_percent": 62.8,
  "disk_percent": 38.5,
  "active_connections": 127
}
```

### System Status
```http
GET /monitoring/status
Authorization: Bearer {token}
```

---

## ⚙️ USER PREFERENCES

### Get Preferences
```http
GET /preferences
Authorization: Bearer {token}
```

### Update Preferences
```http
PUT /preferences
Authorization: Bearer {token}
Content-Type: application/json

{
  "email_notifications": true,
  "sms_notifications": false,
  "push_notifications": true,
  "alert_severity_filter": ["critical", "high"],
  "dashboard_refresh_interval": 30,
  "theme": "dark"
}
```

### Reset Preferences
```http
POST /preferences/reset
Authorization: Bearer {token}
```

---

## 🚰 PIPELINES

### List Pipelines
```http
GET /pipelines
Authorization: Bearer {token}

Query Parameters:
- municipality_id (optional)
```

### Create Pipeline
```http
POST /pipelines
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Main Supply Line A",
  "municipality_id": 1,
  "material": "Steel",
  "diameter_mm": 600,
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [28.0473, -26.2041],
      [28.0500, -26.2100]
    ]
  }
}
```

---

## 🏢 MUNICIPALITIES

### List Municipalities
```http
GET /municipalities
Authorization: Bearer {token}
```

### Create Municipality
```http
POST /municipalities
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Johannesburg",
  "code": "JHB",
  "contact_email": "water@jhb.gov.za",
  "contact_phone": "+27123456789"
}
```

---

## 📝 INCIDENTS

### List Incidents
```http
GET /incidents
Authorization: Bearer {token}

Query Parameters:
- status (optional): open, in_progress, resolved, closed
- days (default: 30)
```

### Create Incident
```http
POST /incidents
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Pipeline Burst",
  "description": "Major leak detected on Main Line A",
  "sensor_id": 15,
  "severity": "critical",
  "location": "Corner of Main St and 5th Ave"
}
```

### Update Incident
```http
PUT /incidents/{incident_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "in_progress",
  "notes": "Repair crew dispatched"
}
```

---

## 📊 RESPONSE CODES

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error

---

## 🔒 AUTHENTICATION

All endpoints (except `/auth/login` and `/health`) require JWT authentication:

```http
Authorization: Bearer {your_access_token}
```

---

## ⚡ RATE LIMITING

- **Default:** 60 requests per minute per IP
- **Headers:**
  - `X-RateLimit-Limit`: Maximum requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

---

## 🌐 WEBSOCKET

### Connect
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{municipality_id}?token={jwt_token}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Message Types
- `sensor_reading` - New sensor data
- `alert` - New alert created
- `alert_resolved` - Alert resolved
- `sensor_status` - Sensor status change

---

## 📡 MQTT TOPICS

### Subscribe to Sensor Data
```
sensors/{device_id}/data
sensors/{device_id}/status
sensors/{device_id}/heartbeat
```

### Publish Sensor Reading
```json
Topic: sensors/SENSOR_001/data

Payload:
{
  "device_id": "SENSOR_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "value": 3.5,
  "unit": "bar",
  "quality": 0.98
}
```

---

**Total Endpoints:** 80+  
**API Version:** 2.0  
**Last Updated:** 2024-01-15

**Interactive Documentation:** http://localhost:8000/docs
