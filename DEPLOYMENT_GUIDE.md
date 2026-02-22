# ðŸš€ COMPLETE DEPLOYMENT GUIDE

## National Water Infrastructure Monitoring System

---

## ðŸ“‹ PRE-DEPLOYMENT CHECKLIST

### Infrastructure Requirements
- [ ] MySQL/PostgreSQL with PostGIS extension
- [ ] Redis server (for caching and pub/sub)
- [ ] MQTT broker (Mosquitto recommended)
- [ ] S3-compatible storage
- [ ] SSL certificates for production
- [ ] Domain name configured

### System Requirements
- [ ] Python 3.12+
- [ ] Node.js 18+
- [ ] Docker & Docker Compose
- [ ] Kubernetes cluster (for production)
- [ ] 4GB+ RAM per service
- [ ] 50GB+ storage

---

## ðŸ”§ BACKEND DEPLOYMENT

### 1. Environment Configuration

Create `.env` file:
```bash
# Database
DATABASE_URL=mysql+pymysql://root:<MYSQL_PASSWORD>@interchange.proxy.rlwy.net:20906/railway

# Redis
REDIS_URL=redis://default:<REDIS_PASSWORD>@switchyard.proxy.rlwy.net:10457

# S3 Storage
S3_ENDPOINT=https://t3.storageapi.dev
S3_BUCKET=recorded-wrap-krk8vsj4wzi
S3_ACCESS_KEY=<S3_ACCESS_KEY>
S3_SECRET_KEY=<S3_SECRET_KEY>

# Security
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=admin
MQTT_PASSWORD=secure_password
MQTT_TLS_ENABLED=false

# Application
APP_NAME=National Water Infrastructure Monitoring
APP_VERSION=2.0.0
ENVIRONMENT=production
DEBUG=false

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# CORS
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

### 2. Database Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Create initial admin user
python scripts/create_admin.py
```

### 3. Start Backend Services

**Development:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Production with Gunicorn:**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. Start Background Workers

```bash
# Celery worker
celery -A app.celery_app worker --loglevel=info

# Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info
```

---

## ðŸ–¥ï¸ CONTROL ROOM DEPLOYMENT

### 1. Install Dependencies

```bash
cd frontend-control-room
npm install
```

### 2. Configure Environment

Create `.env`:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
```

### 3. Build & Run

**Development:**
```bash
npm run electron-dev
```

**Production Build:**
```bash
npm run electron-build

# Output in dist/ folder
# Installers for Windows, macOS, Linux
```

---

## ðŸ“± MOBILE APP DEPLOYMENT

### 1. Install Dependencies

```bash
cd mobile-app
npm install
```

### 2. Configure API

Update `config.js`:
```javascript
export const API_URL = 'https://api.yourdomain.com';
export const WS_URL = 'wss://api.yourdomain.com/ws';
```

### 3. Build & Deploy

**Android:**
```bash
npm run android
eas build --platform android
```

**iOS:**
```bash
npm run ios
eas build --platform ios
```

---

## ðŸ³ DOCKER DEPLOYMENT

### 1. Build Images

```bash
# Backend
docker build -t water-monitoring-backend:latest ./backend

# Control Room
docker build -t water-monitoring-frontend:latest ./frontend-control-room
```

### 2. Docker Compose

```bash
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Docker Compose Configuration

```yaml
version: '3.8'

services:
  backend:
    image: water-monitoring-backend:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
      - mqtt

  celery-worker:
    image: water-monitoring-backend:latest
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}

  celery-beat:
    image: water-monitoring-backend:latest
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  mqtt:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
```

---

## â˜¸ï¸ KUBERNETES DEPLOYMENT

### 1. Apply Configurations

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/ingress.yaml
kubectl apply -f kubernetes/hpa.yaml
```

### 2. Verify Deployment

```bash
kubectl get pods -n water-monitoring
kubectl get services -n water-monitoring
kubectl logs -f deployment/backend -n water-monitoring
```

### 3. Scale Services

```bash
kubectl scale deployment backend --replicas=5 -n water-monitoring
```

---

## ðŸ”’ SSL/TLS CONFIGURATION

### 1. Generate Certificates

```bash
# Using Let's Encrypt
certbot certonly --standalone -d api.yourdomain.com
```

### 2. Configure Nginx

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## ðŸ“Š MONITORING SETUP

### 1. Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:8000/api/v1/monitoring/metrics
```

### 2. Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'water-monitoring'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/monitoring/metrics'
```

### 3. Grafana Dashboard

Import dashboard from `monitoring/grafana-dashboard.json`

---

## ðŸ”„ CI/CD PIPELINE

### GitHub Actions Workflow

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker Image
        run: docker build -t water-monitoring:${{ github.sha }} .
      
      - name: Push to Registry
        run: docker push water-monitoring:${{ github.sha }}
      
      - name: Deploy to Kubernetes
        run: kubectl set image deployment/backend backend=water-monitoring:${{ github.sha }}
```

---

## ðŸ§ª POST-DEPLOYMENT TESTING

### 1. API Tests

```bash
# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Test sensor endpoint
curl http://localhost:8000/api/v1/sensors \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/v1/sensors

# Using k6
k6 run load-test.js
```

---

## ðŸ“ˆ PERFORMANCE OPTIMIZATION

### 1. Database Indexing

```sql
CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(timestamp);
CREATE INDEX idx_sensor_readings_sensor_id ON sensor_readings(sensor_id);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
```

### 2. Redis Caching

- Sensor statistics: 60s TTL
- Municipality data: 120s TTL
- Dashboard metrics: 60s TTL

### 3. Connection Pooling

```python
# SQLAlchemy pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

---

## ðŸ” SECURITY HARDENING

### 1. Firewall Rules

```bash
# Allow only necessary ports
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw enable
```

### 2. Rate Limiting

- API: 60 requests/minute per IP
- WebSocket: 100 messages/minute
- MQTT: 1000 messages/minute

### 3. Authentication

- JWT tokens with 30-minute expiry
- Refresh tokens with 7-day expiry
- RBAC with role-based permissions

---

## ðŸ“ MAINTENANCE TASKS

### Daily
- [ ] Check system health
- [ ] Review error logs
- [ ] Monitor disk space

### Weekly
- [ ] Database backup
- [ ] Review performance metrics
- [ ] Update security patches

### Monthly
- [ ] Full system backup
- [ ] Cleanup old data (>90 days)
- [ ] Review and optimize queries

---

## ðŸ†˜ TROUBLESHOOTING

### Backend Won't Start
```bash
# Check logs
tail -f logs/app.log

# Verify database connection
python -c "from app.core.database import engine; engine.connect()"
```

### MQTT Not Connecting
```bash
# Test MQTT broker
mosquitto_sub -h localhost -t "sensors/#" -v
```

### High Memory Usage
```bash
# Check processes
docker stats
kubectl top pods
```

---

## ðŸ“ž SUPPORT

For deployment issues:
- Check logs: `/var/log/water-monitoring/`
- Review documentation: `/docs/`
- Contact: support@watermonitoring.com

---

**Deployment Status: âœ… PRODUCTION-READY**

**Last Updated:** 2024-01-15

