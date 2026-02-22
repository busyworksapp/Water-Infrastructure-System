# Developer Quick Reference Guide

## 🚀 National Water Infrastructure Monitoring System

---

## Quick Commands

### Backend Development
```bash
# Start backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Format code
black app/
isort app/

# Lint
flake8 app/
bandit -r app/
```

### Frontend Development
```bash
# Start control room
cd frontend-control-room
npm install
npm start  # Web dev
npm run electron-dev  # Electron dev
npm run electron-build  # Build executable
```

### Mobile Development
```bash
# Start mobile app
cd mobile-app
npm install
npm start  # Start Expo
npm run android  # Android
npm run ios  # iOS
```

### Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Rebuild
docker-compose build --no-cache

# Stop all
docker-compose down
```

---

## API Endpoints Quick Reference

### Authentication
```bash
# Login
POST /api/v1/auth/login
Body: username=admin&password=pass

# Refresh token
POST /api/v1/auth/refresh
Body: {"refresh_token": "..."}
```

### Sensors
```bash
# List sensors
GET /api/v1/sensors
Headers: Authorization: Bearer {token}

# Get sensor
GET /api/v1/sensors/{sensor_id}

# Create sensor
POST /api/v1/sensors
Body: {"name": "...", "sensor_type_id": "...", ...}

# Ingest reading
POST /api/v1/sensors/{sensor_id}/readings
Body: {"value": 3.5, "timestamp": "..."}
```

### Alerts
```bash
# List alerts
GET /api/v1/alerts?status=active&severity=high

# Acknowledge alert
POST /api/v1/alerts/{alert_id}/acknowledge

# Resolve alert
POST /api/v1/alerts/{alert_id}/resolve
```

### Municipalities
```bash
# List municipalities
GET /api/v1/municipalities

# Get stats
GET /api/v1/municipalities/{id}/stats
```

---

## Environment Variables

### Required
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/0
SECRET_KEY=your-secret-key-min-48-chars
```

### Optional
```bash
DEBUG=false
ENVIRONMENT=production
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
S3_BUCKET=your-bucket
PROMETHEUS_ENABLED=true
```

---

## Database Commands

### Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Initialize database
python backend/scripts/init_db.py
```

### Direct SQL
```bash
# PostgreSQL
psql -h host -U user -d database

# MySQL
mysql -h host -u user -p database
```

---

## Testing

### Unit Tests
```bash
pytest tests/test_unit.py -v
```

### Integration Tests
```bash
pytest tests/test_integration.py -v
```

### API Tests
```bash
pytest tests/test_api.py -v
```

### Load Tests
```bash
cd iot-gateway
locust -f load_test.py --host http://localhost:8000
```

### Sensor Simulation
```bash
# All protocols
python iot-gateway/multi_protocol_simulator.py --protocol mixed

# MQTT only
python iot-gateway/multi_protocol_simulator.py --protocol mqtt --sensor-id SENSOR_001

# HTTP only
python iot-gateway/multi_protocol_simulator.py --protocol http --count 100
```

---

## Celery Tasks

### Start Workers
```bash
# Worker
celery -A app.celery_app worker --loglevel=info

# Beat scheduler
celery -A app.celery_app beat --loglevel=info

# Both
celery -A app.celery_app worker --beat --loglevel=info
```

### Manual Task Execution
```python
from app.tasks import cleanup_old_readings, generate_daily_report

# Execute task
result = cleanup_old_readings.delay(days=90)

# Get result
print(result.get())
```

---

## Monitoring

### Prometheus Metrics
```bash
# View metrics
curl http://localhost:8000/metrics

# Key metrics
http_requests_total
sensor_readings_total
alerts_total
websocket_connections_active
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# Docker
docker-compose logs -f backend

# Kubernetes
kubectl logs -f deployment/backend -n water-monitoring

# Railway
railway logs
```

---

## WebSocket Testing

### Using wscat
```bash
npm install -g wscat

# Connect
wscat -c "ws://localhost:8000/ws/global?token=YOUR_TOKEN"

# Send ping
{"type": "ping"}
```

### Using Python
```python
import websockets
import asyncio

async def test_ws():
    uri = "ws://localhost:8000/ws/global?token=YOUR_TOKEN"
    async with websockets.connect(uri) as ws:
        await ws.send('{"type": "ping"}')
        response = await ws.recv()
        print(response)

asyncio.run(test_ws())
```

---

## MQTT Testing

### Publish
```bash
mosquitto_pub -h localhost -p 1883 \
  -t "sensors/SENSOR_001/data" \
  -m '{"value": 3.5, "timestamp": "2024-01-15T10:00:00Z"}'
```

### Subscribe
```bash
mosquitto_sub -h localhost -p 1883 -t "sensors/#"
```

---

## Common Issues & Solutions

### Database Connection Failed
```bash
# Check connection
python -c "from app.core.database import engine; print(engine.connect())"

# Verify credentials
echo $DATABASE_URL
```

### Redis Connection Failed
```bash
# Test Redis
redis-cli -u $REDIS_URL ping

# Check if running
docker ps | grep redis
```

### MQTT Not Connecting
```bash
# Check broker
mosquitto -v

# Test connection
mosquitto_pub -h localhost -p 1883 -t test -m "hello"
```

### WebSocket Disconnecting
```bash
# Check token validity
# Increase timeout in config
# Check CORS settings
```

---

## Deployment

### Railway
```bash
# Login
railway login

# Deploy
railway up

# Set variables
railway variables set KEY=value

# View logs
railway logs
```

### Docker
```bash
# Build
docker build -t water-monitoring-backend backend/

# Run
docker run -p 8000:8000 --env-file .env water-monitoring-backend
```

### Kubernetes
```bash
# Apply
kubectl apply -f kubernetes/production-deployment.yaml

# Check status
kubectl get pods -n water-monitoring

# View logs
kubectl logs -f deployment/backend -n water-monitoring
```

---

## Security

### Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Generate API Key
```bash
python backend/app/utils/secrets_manager.py generate-api-key
```

### Validate Secrets
```bash
python backend/app/utils/secrets_manager.py validate
```

---

## Performance Optimization

### Database Indexes
```sql
-- Add index
CREATE INDEX idx_sensor_readings_timestamp 
ON sensor_readings(sensor_id, timestamp DESC);

-- Analyze query
EXPLAIN ANALYZE SELECT * FROM sensor_readings 
WHERE sensor_id = 'SENSOR_001' 
ORDER BY timestamp DESC LIMIT 100;
```

### Redis Caching
```python
from app.services.cache_service import cache_service

# Cache data
cache_service.set("key", data, ttl=3600)

# Get cached data
data = cache_service.get("key")
```

---

## Useful SQL Queries

### Active Sensors
```sql
SELECT COUNT(*) FROM sensors WHERE is_active = true;
```

### Recent Readings
```sql
SELECT * FROM sensor_readings 
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

### Active Alerts
```sql
SELECT severity, COUNT(*) 
FROM alerts 
WHERE status = 'active' 
GROUP BY severity;
```

### Anomalies Today
```sql
SELECT COUNT(*) FROM sensor_readings 
WHERE is_anomaly = true 
AND timestamp::date = CURRENT_DATE;
```

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push
git push origin feature/new-feature

# Create PR on GitHub
```

---

## Documentation

### API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Code Docs
```bash
# Generate docs
pdoc --html app -o docs/

# View
open docs/app/index.html
```

---

## Support

### Get Help
- Documentation: `/docs` folder
- API Docs: http://localhost:8000/docs
- Issues: GitHub Issues
- Email: support@water-monitoring.gov

---

**Last Updated**: 2024-01-15  
**Version**: 2.0.0
