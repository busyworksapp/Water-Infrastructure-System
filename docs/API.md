# API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

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
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "admin",
    "email": "admin@example.com",
    "is_super_admin": true,
    "municipality_id": null
  }
}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer {access_token}
```

---

## Sensors

### List All Sensors
```http
GET /sensors
Authorization: Bearer {access_token}
Query Parameters:
  - municipality_id (optional)
  - status (optional): active, inactive, maintenance, faulty

Response:
[
  {
    "id": "uuid",
    "device_id": "SENSOR_001",
    "name": "Pressure Sensor 1",
    "status": "active",
    "protocol": "mqtt",
    "sensor_type": "Pressure Sensor",
    "municipality_id": "uuid",
    "pipeline_id": "uuid",
    "location": {
      "type": "Point",
      "coordinates": [28.0473, -26.2041]
    },
    "battery_level": 85,
    "signal_strength": 92,
    "last_reading_at": "2024-01-15T10:30:00Z"
  }
]
```

### Get Sensor Details
```http
GET /sensors/{sensor_id}
Authorization: Bearer {access_token}
```

### Get Sensor Readings
```http
GET /sensors/{sensor_id}/readings
Authorization: Bearer {access_token}
Query Parameters:
  - hours (default: 24, max: 168)
  - limit (default: 1000, max: 10000)

Response:
[
  {
    "id": "uuid",
    "timestamp": "2024-01-15T10:30:00Z",
    "value": 3.5,
    "unit": "bar",
    "is_anomaly": false,
    "quality_score": 0.98
  }
]
```

### Get Latest Reading
```http
GET /sensors/{sensor_id}/latest
Authorization: Bearer {access_token}
```

---

## Alerts

### List Alerts
```http
GET /alerts
Authorization: Bearer {access_token}
Query Parameters:
  - municipality_id (optional)
  - status (optional): open, acknowledged, in_progress, resolved, closed
  - severity (optional): info, low, medium, high, critical
  - limit (default: 100, max: 1000)

Response:
[
  {
    "id": "uuid",
    "alert_type": "pressure_anomaly",
    "severity": "high",
    "status": "open",
    "title": "Pressure Anomaly detected on Sensor 1",
    "description": "Anomalous reading detected: 6.5 bar",
    "sensor_id": "uuid",
    "pipeline_id": "uuid",
    "municipality_id": "uuid",
    "location": {
      "type": "Point",
      "coordinates": [28.0473, -26.2041]
    },
    "triggered_value": {"value": 6.5, "unit": "bar"},
    "created_at": "2024-01-15T10:30:00Z",
    "acknowledged_at": null,
    "resolved_at": null
  }
]
```

### Get Alert Details
```http
GET /alerts/{alert_id}
Authorization: Bearer {access_token}
```

### Acknowledge Alert
```http
POST /alerts/{alert_id}/acknowledge
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "notes": "Investigating the issue"
}

Response:
{
  "message": "Alert acknowledged successfully"
}
```

### Resolve Alert
```http
POST /alerts/{alert_id}/resolve
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "resolution_notes": "Pressure valve adjusted. System back to normal."
}

Response:
{
  "message": "Alert resolved successfully"
}
```

### Get Alert Statistics
```http
GET /alerts/statistics/summary
Authorization: Bearer {access_token}
Query Parameters:
  - municipality_id (optional)

Response:
{
  "total": 150,
  "open": 12,
  "critical": 3,
  "high": 5
}
```

---

## WebSocket Connection

### Connect to Real-Time Updates
```javascript
const socket = io('ws://localhost:8000/ws/{municipality_id}', {
  transports: ['websocket']
});

// Listen for sensor readings
socket.on('sensor_reading', (data) => {
  console.log('New reading:', data);
  // {
  //   sensor_id: "uuid",
  //   device_id: "SENSOR_001",
  //   value: 3.5,
  //   timestamp: "2024-01-15T10:30:00Z",
  //   is_anomaly: false
  // }
});

// Listen for alerts
socket.on('alert', (data) => {
  console.log('New alert:', data);
  // {
  //   id: "uuid",
  //   type: "pressure_anomaly",
  //   severity: "high",
  //   title: "Pressure Anomaly detected",
  //   sensor_id: "uuid",
  //   timestamp: "2024-01-15T10:30:00Z"
  // }
});

// Listen for incidents
socket.on('incident', (data) => {
  console.log('New incident:', data);
});
```

---

## IoT Device Integration

### MQTT Topics

#### Publish Sensor Data
```
Topic: sensors/{device_id}/data
Payload:
{
  "device_id": "SENSOR_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "value": 3.5,
  "unit": "bar",
  "quality": 0.98,
  "battery_level": 85,
  "signal_strength": 92
}
```

#### Publish Device Status
```
Topic: sensors/{device_id}/status
Payload:
{
  "device_id": "SENSOR_001",
  "battery_level": 85,
  "signal_strength": 92,
  "firmware_version": "1.2.3"
}
```

#### Publish Heartbeat
```
Topic: sensors/{device_id}/heartbeat
Payload:
{
  "device_id": "SENSOR_001",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### HTTP Endpoint for Sensor Data
```http
POST /sensors/{sensor_id}/readings
Authorization: Bearer {device_api_key}
Content-Type: application/json

{
  "timestamp": "2024-01-15T10:30:00Z",
  "value": 3.5,
  "unit": "bar",
  "quality": 0.98
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

All API endpoints are rate-limited to 60 requests per minute per IP address.

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248000
```

---

## Pagination

For endpoints that return lists, use these query parameters:
- `limit`: Number of items per page (default: 100)
- `offset`: Number of items to skip (default: 0)

Response includes pagination metadata:
```json
{
  "items": [...],
  "total": 500,
  "limit": 100,
  "offset": 0
}
```
