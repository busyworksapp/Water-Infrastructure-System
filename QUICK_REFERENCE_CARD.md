# 🚀 QUICK REFERENCE CARD

## National Water Infrastructure Monitoring System v2.0.0

---

## ⚡ QUICK START

```batch
# Windows - One Command Start
quick_start.bat

# Manual Start
docker-compose up -d
python backend/scripts/init_db.py
```

---

## 🔧 COMMON COMMANDS

### System Control

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
```

### Database Operations

```bash
# Initialize database
cd backend
python scripts/init_db.py

# Connect to MySQL
mysql -h interchange.proxy.rlwy.net -u root -p -P 20906 railway

# Connect to PostgreSQL
PGPASSWORD=egnQHcmNTcNzmTUBfHcUxewgARJEzhBt psql -h shinkansen.proxy.rlwy.net -U postgres -p 29535 -d railway

# Backup database
./backend/scripts/backup.sh

# Restore database
./backend/scripts/restore.sh backup.sql.gz
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/metrics

# API documentation
open http://localhost:8000/docs

# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'
```

### Frontend Applications

```bash
# Control Room (Desktop)
cd frontend-control-room
npm install
npm run electron-dev

# Mobile App
cd mobile-app
npm install
npm start
```

### IoT Testing

```bash
# Sensor simulator
cd iot-gateway
python sensor_simulator.py

# Multi-protocol test
python multi_protocol_simulator.py

# Load testing
python load_test.py
```

---

## 🔍 MONITORING

### Health Checks

```bash
# System health
curl http://localhost:8000/api/v1/monitoring/health

# Component status
curl http://localhost:8000/api/v1/monitoring/status

# Metrics
curl http://localhost:8000/metrics
```

### Service Status

```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose ps backend

# Resource usage
docker stats
```

---

## 🐛 TROUBLESHOOTING

### Backend Issues

```bash
# Check logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Check environment
cd backend
python -c "from app.core.config import settings; print(vars(settings))"

# Test database connection
python -c "from app.core.database import engine; engine.connect()"
```

### Database Issues

```bash
# Check connection
mysql -h interchange.proxy.rlwy.net -u root -p -P 20906 railway -e "SELECT 1"

# Check tables
mysql -h interchange.proxy.rlwy.net -u root -p -P 20906 railway -e "SHOW TABLES"

# Reinitialize
python backend/scripts/init_db.py
```

### MQTT Issues

```bash
# Check MQTT broker
docker-compose logs mqtt-broker

# Test MQTT connection
mosquitto_sub -h localhost -p 1883 -t "test"

# Publish test message
mosquitto_pub -h localhost -p 1883 -t "test" -m "hello"
```

### Redis Issues

```bash
# Check Redis
docker-compose logs redis

# Connect to Redis
redis-cli -u redis://default:VatkHEDGSLJbgKZlgTiVamRJggKcFqOy@switchyard.proxy.rlwy.net:10457

# Test Redis
redis-cli -u redis://default:VatkHEDGSLJbgKZlgTiVamRJggKcFqOy@switchyard.proxy.rlwy.net:10457 PING
```

---

## 📊 KEY ENDPOINTS

### Authentication

```
POST   /api/v1/auth/register     - Register new user
POST   /api/v1/auth/login        - Login
POST   /api/v1/auth/refresh      - Refresh token
POST   /api/v1/auth/logout       - Logout
```

### Sensors

```
GET    /api/v1/sensors           - List sensors
POST   /api/v1/sensors           - Create sensor
GET    /api/v1/sensors/{id}      - Get sensor
PUT    /api/v1/sensors/{id}      - Update sensor
DELETE /api/v1/sensors/{id}      - Delete sensor
```

### Alerts

```
GET    /api/v1/alerts            - List alerts
GET    /api/v1/alerts/{id}       - Get alert
PUT    /api/v1/alerts/{id}       - Update alert
POST   /api/v1/alerts/{id}/resolve - Resolve alert
```

### Data Ingestion

```
POST   /api/v1/ingest/sensor-reading  - Submit sensor reading
POST   /api/v1/ingest/batch           - Batch readings
```

### Monitoring

```
GET    /health                   - Health check
GET    /metrics                  - Prometheus metrics
GET    /api/v1/monitoring/health - Detailed health
GET    /api/v1/monitoring/status - System status
```

---

## 🔐 CREDENTIALS

### Railway Services

```
MySQL:
  Host: interchange.proxy.rlwy.net
  Port: 20906
  User: root
  Pass: nYiLHEQsRMUsmXTUowmrlvNSJcutDxYg
  DB:   railway

PostgreSQL:
  Host: shinkansen.proxy.rlwy.net
  Port: 29535
  User: postgres
  Pass: egnQHcmNTcNzmTUBfHcUxewgARJEzhBt
  DB:   railway

Redis:
  URL: redis://default:VatkHEDGSLJbgKZlgTiVamRJggKcFqOy@switchyard.proxy.rlwy.net:10457

S3:
  Endpoint: https://t3.storageapi.dev
  Bucket:   recorded-wrap-krk8vsj4wzi
  Access:   tid_WKMBXeNExOmrEzIKww_gnbNlOuwwHhgggpTBpaEonVRDWVExNu
  Secret:   tsec_IIbuZ_nXbwG4Ij84tM_UNen4Cvd1cGzzKQ2kbSyosGpQkMIszQA8Hv2X010cd7EFpMkyz1
```

### Local Services

```
Backend:      http://localhost:8000
API Docs:     http://localhost:8000/docs
MQTT:         localhost:1883
Redis:        localhost:6379
MySQL:        localhost:3306
PostgreSQL:   localhost:5432
```

---

## 📁 IMPORTANT FILES

```
Configuration:
  backend/.env                    - Environment variables
  docker-compose.yml              - Docker services
  backend/requirements.txt        - Python dependencies

Documentation:
  README.md                       - Main documentation
  SECURITY_AND_CODE_FIXES_APPLIED.md
  PRODUCTION_DEPLOYMENT_CHECKLIST_COMPLETE.md
  FINAL_SYSTEM_STATUS_AND_FIXES.md

Scripts:
  quick_start.bat                 - Quick start
  verify_system.py                - System verification
  backend/scripts/init_db.py      - Database initialization
  backend/scripts/backup.sh       - Database backup
```

---

## 🎯 VERIFICATION

```bash
# Run full system verification
python verify_system.py

# Check system health
curl http://localhost:8000/api/v1/monitoring/health

# Test all services
docker-compose ps
```

---

## 📞 SUPPORT

### Documentation
- API Docs: http://localhost:8000/docs
- Architecture: docs/ARCHITECTURE.md
- Security: docs/SECURITY.md
- Deployment: docs/DEPLOYMENT.md

### Quick Help
```bash
# View this reference
cat QUICK_REFERENCE_CARD.md

# View deployment checklist
cat PRODUCTION_DEPLOYMENT_CHECKLIST_COMPLETE.md

# View fixes applied
cat SECURITY_AND_CODE_FIXES_APPLIED.md
```

---

## ✅ STATUS

- **System Version**: 2.0.0
- **Status**: PRODUCTION READY ✅
- **Last Updated**: 2024-01-15

---

**Keep this card handy for quick reference!** 📌
