# 🚀 Quick Reference Guide
## National Water Infrastructure Monitoring System

---

## 📋 Common Commands

### Backend Development
```bash
# Start backend server
cd backend
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_api.py::test_login -v

# Database migrations
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "description"

# Start Celery worker
celery -A app.celery_app worker --loglevel=info

# Start Celery beat
celery -A app.celery_app beat --loglevel=info

# Initialize database
python scripts/init_db.py
```

### Frontend Development
```bash
# Control Room
cd frontend-control-room
npm install
npm run electron-dev
npm run electron-build

# Mobile App
cd mobile-app
npm install
npm start
npm run android
npm run ios
```

### Docker Commands
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up -d --build
```

---

## 🔑 API Endpoints Quick Reference

### Authentication
```
POST   /api/v1/auth/register          - Register new user
POST   /api/v1/auth/login             - Login
POST   /api/v1/auth/refresh           - Refresh token
POST   /api/v1/auth/logout            - Logout
GET    /api/v1/auth/me                - Get current user
```

### Sensors
```
GET    /api/v1/sensors                - List all sensors
POST   /api/v1/sensors                - Create sensor
GET    /api/v1/sensors/{id}           - Get sensor details
PUT    /api/v1/sensors/{id}           - Update sensor
DELETE /api/v1/sensors/{id}           - Delete sensor
GET    /api/v1/sensors/{id}/readings  - Get sensor readings
```

### Alerts
```
GET    /api/v1/alerts                 - List alerts
POST   /api/v1/alerts                 - Create alert
GET    /api/v1/alerts/{id}            - Get alert details
PUT    /api/v1/alerts/{id}/resolve    - Resolve alert
DELETE /api/v1/alerts/{id}            - Delete alert
```

### Analytics
```
GET    /api/v1/analytics/summary      - System summary
GET    /api/v1/analytics/trends       - Trend analysis
GET    /api/v1/analytics/municipality/{id} - Municipality stats
```

### Advanced Analytics
```
GET    /api/v1/advanced/geospatial/leak-detection/{pipeline_id}
GET    /api/v1/advanced/geospatial/sensors-near
GET    /api/v1/advanced/geospatial/pipeline-health/{pipeline_id}
GET    /api/v1/advanced/geospatial/pressure-heatmap
GET    /api/v1/advanced/correlation/active-patterns
GET    /api/v1/advanced/predictive/sensor-failure-risk/{sensor_id}
GET    /api/v1/advanced/predictive/maintenance-schedule
```

### System Utilities
```
GET    /api/v1/system/health/comprehensive
GET    /api/v1/system/performance/endpoints
GET    /api/v1/system/performance/slow-endpoints
GET    /api/v1/system/export/sensor-readings/{sensor_id}
GET    /api/v1/system/export/alerts
GET    /api/v1/system/export/compliance-report
POST   /api/v1/system/webhooks
GET    /api/v1/system/webhooks
DELETE /api/v1/system/webhooks/{id}
```

### Municipalities
```
GET    /api/v1/municipalities         - List municipalities
POST   /api/v1/municipalities         - Create municipality
GET    /api/v1/municipalities/{id}    - Get details
PUT    /api/v1/municipalities/{id}    - Update
DELETE /api/v1/municipalities/{id}    - Delete
```

### Incidents
```
GET    /api/v1/incidents              - List incidents
POST   /api/v1/incidents              - Create incident
GET    /api/v1/incidents/{id}         - Get details
PUT    /api/v1/incidents/{id}         - Update
DELETE /api/v1/incidents/{id}         - Delete
```

### Maintenance
```
GET    /api/v1/maintenance            - List maintenance logs
POST   /api/v1/maintenance            - Create log
GET    /api/v1/maintenance/{id}       - Get details
PUT    /api/v1/maintenance/{id}       - Update
DELETE /api/v1/maintenance/{id}       - Delete
```

---

## 🔌 IoT Integration

### MQTT Topics
```
sensors/{device_id}/data              - Sensor readings
sensors/{device_id}/status            - Device status
sensors/{device_id}/heartbeat         - Keep-alive
```

### MQTT Payload Example
```json
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

### HTTP Ingestion
```bash
POST /api/v1/ingest/sensor-reading
Authorization: Bearer {device_api_key}

{
  "sensor_id": "SENSOR_001",
  "timestamp": "2024-01-15T10:30:00Z",
  "value": 3.5,
  "unit": "bar"
}
```

### TCP Socket
```
Connect to: localhost:9999
Format: JSON\n
```

---

## 🔐 Authentication

### Get Access Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

### Use Token
```bash
curl -X GET http://localhost:8000/api/v1/sensors \
  -H "Authorization: Bearer {access_token}"
```

---

## 🗄️ Database

### Connection Strings
```bash
# PostgreSQL
postgresql://user:pass@host:port/database

# MySQL
mysql+pymysql://user:pass@host:port/database

# Redis
redis://default:pass@host:port
```

### Common Queries
```sql
-- Count sensors
SELECT COUNT(*) FROM sensors;

-- Active alerts
SELECT * FROM alerts WHERE status = 'active';

-- Recent readings
SELECT * FROM sensor_readings 
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;

-- Sensor health
SELECT s.name, s.last_reading_at, s.battery_level
FROM sensors s
WHERE s.is_active = true
ORDER BY s.last_reading_at DESC;
```

---

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Comprehensive Health
```bash
curl http://localhost:8000/api/v1/system/health/comprehensive \
  -H "Authorization: Bearer {token}"
```

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

---

## 🐛 Debugging

### View Logs
```bash
# Application logs
tail -f logs/app.log

# Celery logs
tail -f logs/celery.log

# Docker logs
docker-compose logs -f backend
```

### Python Debugger
```python
import pdb; pdb.set_trace()
```

### Test Single Endpoint
```bash
pytest tests/test_api.py::test_get_sensors -v -s
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=your-secret-key

# Optional
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

### Load Environment
```bash
export $(cat .env.production | xargs)
```

---

## 📦 Dependencies

### Install Backend
```bash
pip install -r requirements.txt
```

### Key Packages
- fastapi - Web framework
- sqlalchemy - ORM
- paho-mqtt - MQTT client
- celery - Background tasks
- redis - Caching
- psycopg2 - PostgreSQL driver
- pymysql - MySQL driver

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

### Load Testing
```bash
cd iot-gateway
python load_test.py
```

---

## 🚀 Deployment

### Railway
```bash
python scripts/deploy_production.py
```

### Docker
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f kubernetes/production-deployment.yaml
```

---

## 📱 Mobile App

### Start Development
```bash
cd mobile-app
npm start
```

### Build APK (Android)
```bash
eas build --platform android
```

### Build IPA (iOS)
```bash
eas build --platform ios
```

---

## 🎨 Control Room

### Development
```bash
cd frontend-control-room
npm run electron-dev
```

### Build
```bash
npm run electron-build
```

### Output
- Windows: `dist/win-unpacked/`
- macOS: `dist/mac/`
- Linux: `dist/linux-unpacked/`

---

## 🔄 Common Workflows

### Add New Sensor Type
1. Add to `sensor_types` table
2. Update validation in `schemas/sensor.py`
3. Update anomaly detection rules
4. Test with simulator

### Create New Alert Rule
1. Add to `dynamic_rules` table
2. Configure thresholds
3. Set notification channels
4. Test with sample data

### Add New Municipality
1. POST to `/api/v1/municipalities`
2. Create admin user for municipality
3. Configure sensors
4. Set up pipelines

---

## 📞 Support

### Documentation
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- README: /README.md

### Logs
- Application: `logs/app.log`
- Celery: `logs/celery.log`
- Audit: `logs/audit.log`

---

## ⚡ Performance Tips

1. Use Redis caching for frequent queries
2. Index database columns used in WHERE clauses
3. Batch sensor readings for bulk insert
4. Use WebSocket for real-time updates
5. Enable connection pooling
6. Use async endpoints where possible
7. Compress large responses
8. Implement pagination for large datasets

---

## 🔒 Security Checklist

- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS in production
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Review audit logs regularly
- [ ] Keep dependencies updated
- [ ] Use environment variables for secrets

---

**Quick Start**: `docker-compose up -d` → Visit http://localhost:8000/docs

**Need Help?** Check `/docs` folder for detailed documentation
