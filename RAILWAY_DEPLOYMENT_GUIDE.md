# Railway.app Deployment Guide

## National Water Infrastructure Monitoring System

This guide covers deploying the water monitoring system to Railway.app.

---

## Quick Start (5 minutes)

### 1. Prerequisites

- Railway.app account (free tier available)
- GitHub account for repo connection
- Docker-compatible environment
- Your credentials ready (provided in requirements)

### 2. Clone and Prepare Repository

```bash
# Clone repository
git clone <your-repo-url>
cd randwater

# Copy environment template
cp .env.example .env
```

### 3. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init
```

### 4. Set Up Services

```bash
# Create MySQL database service
railway add --service mysql

# Create PostgreSQL service (optional)
railway add --service postgres

# Create Redis service
railway add --service redis

# Create S3 storage (use Linode Object Storage)
railway add --service s3
```

### 5. Configure Environment Variables

```bash
# In Railway dashboard, set these variables:

# Database (MySQL from Railway)
DATABASE_MODE=mysql
DATABASE_URL=mysql+pymysql://root:PASSWORD@HOST:PORT/DATABASE

# Or PostgreSQL
# DATABASE_MODE=postgres
# DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE

# Redis (from Railway)
REDIS_URL=redis://default:PASSWORD@HOST:PORT

# S3 (Linode Object Storage)
S3_ENDPOINT=https://t3.storageapi.dev
S3_BUCKET=your-bucket-name
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key

# Application
ENVIRONMENT=production
SECRET_KEY=generate-random-string-min-32-chars
DEBUG=false
ENFORCE_HTTPS=true
```

### 6. Deploy

```bash
# Deploy from command line
railway up

# Or use Git push
git push heroku main
```

---

## Detailed Configuration

### Database Selection

#### Option A: MySQL (Recommended for existing data)

```env
DATABASE_MODE=mysql
DATABASE_URL=mysql+pymysql://root:PASSWORD@interchange.proxy.rlwy.net:20906/railway
```

**Get MySQL credentials from Railway:**
1. Go to Railway dashboard
2. Select MySQL service
3. Click "Connect"
4. Copy "Connection String (TypeScript)"
5. Extract credentials from URL

#### Option B: PostgreSQL with PostGIS

```env
DATABASE_MODE=postgres
DATABASE_URL=postgresql://postgres:PASSWORD@shinkansen.proxy.rlwy.net:29535/railway
ENABLE_POSTGIS_FEATURES=true
```

**Get PostgreSQL credentials from Railway:**
1. Go to Railway dashboard
2. Select PostgreSQL service
3. Click "Connect"
4. Copy URL and format as: `postgresql://USER:PASSWORD@HOST:PORT/DB`

### Redis Configuration

Railway provides Redis at:

```env
REDIS_URL=redis://default:PASSWORD@switchyard.proxy.rlwy.net:10457
```

**Features enabled:**
- ✅ Caching
- ✅ Pub/Sub
- ✅ Celery task queue
- ✅ Session storage

### S3 Object Storage

We recommend **Linode Object Storage** (S3-compatible):

```env
S3_ENDPOINT=https://t3.storageapi.dev
S3_REGION=auto
S3_BUCKET=recorded-wrap-krk8vsj4wzi
S3_ACCESS_KEY=tid_WKMBXeNExOmrEzIKww_gnbNlOuwwHhgggpTBpaEonVRDWVExNu
S3_SECRET_KEY=tsec_IIbuZ_nXbwG4Ij84tM_UNen4Cvd1cGzzKQ2kbSyosGpQkMIszQA8Hv2X010cd7EFpMkyz1
```

**Backup/restore features:**
- Daily automated backups
- S3 encryption (AES-256)
- Lifecycle policies (30-day retention)
- Point-in-time recovery

### MQTT Broker (Local or External)

For local development with Docker Compose:

```bash
# Start Mosquitto from docker-compose.yml
docker-compose up mosquitto
```

For production on Railway:

```env
MQTT_BROKER_HOST=mosquitto  # Docker service name
MQTT_BROKER_PORT=1883
MQTT_TLS_ENABLED=false  # Enable for production
MQTT_USERNAME=iot_user
MQTT_PASSWORD=secure_password_here
```

---

## Deployment Steps

### Step 1: Prepare Code

```bash
# Create Dockerfile (if not present)
cat > Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations and start
CMD ["python", "backend/scripts/init_db.py"] && \
    ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

### Step 2: Set Up Database Migrations

```bash
# Initialize database with existing schema
python backend/scripts/init_db.py

# Verify tables created
# For MySQL:
mysql -h HOST -u USER -p DATABASE -e "SHOW TABLES;"

# For PostgreSQL:
psql -h HOST -U USER -d DATABASE -c "\dt"
```

### Step 3: Configure Environment Variables

**Railway Dashboard Method:**
1. Go to Project Settings
2. Click "Environment"
3. Add variables from `.env.example`
4. Save and redeploy

**Command Line Method:**
```bash
railway env:set DATABASE_MODE=mysql
railway env:set DATABASE_URL="mysql+pymysql://..."
railway env:set REDIS_URL="redis://..."
railway env:set SECRET_KEY="$(openssl rand -base64 32)"
```

### Step 4: Build and Deploy

```bash
# Deploy
railway up

# Check logs
railway logs

# SSH into container (optional)
railway shell
```

### Step 5: Verify Deployment

```bash
# Check health endpoint
curl https://your-app-url.railway.app/monitoring/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "version": "2.0.0",
#   "environment": "production"
# }

# View API documentation
https://your-app-url.railway.app/docs
```

---

## Post-Deployment Configuration

### 1. Initialize Admin User

```bash
# SSH into running container
railway shell

# Create super admin
python -c "
from backend.app.core.security import get_password_hash
from backend.app.core.database import SessionLocal
from backend.app.models import User

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@example.com',
    password_hash=get_password_hash('change_me_password'),
    is_super_admin=True,
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created')
"
```

### 2. Create Default Municipality

```bash
railway shell

python -c "
from backend.app.core.database import SessionLocal
from backend.app.models import Municipality

db = SessionLocal()
municipality = Municipality(
    name='Main Municipality',
    code='main',
    is_active=True
)
db.add(municipality)
db.commit()
print('Municipality created')
"
```

### 3. Test MQTT Connection

```bash
# From your local machine or container:
mosquitto_sub -h MQTT_HOST -p 1883 -u iot_user -P PASSWORD -t "sensors/+/data"
```

---

## Monitoring and Maintenance

### Health Checks

```bash
# Database connectivity
curl https://your-app-url.railway.app/monitoring/health

# System status
curl https://your-app-url.railway.app/monitoring/system-status

# MQTT status
curl https://your-app-url.railway.app/monitoring/mqtt/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Full connectivity
curl https://your-app-url.railway.app/monitoring/system-connectivity \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### View Logs

```bash
# Real-time logs
railway logs -f

# Specific service logs
railway logs --service postgres
railway logs --service redis
```

### Backup and Recovery

```bash
# Automatic daily backup (2 AM UTC)
# Configure in environment:
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"
BACKUP_RETENTION_DAYS=30

# Manual backup
python backend/scripts/backup.sh

# List backups in S3
aws s3 ls s3://recorded-wrap-krk8vsj4wzi/backups/

# Restore from backup
python backend/scripts/restore.sh \
  --backup-file s3://recorded-wrap-krk8vsj4wzi/backups/backup-2024-01-15.sql.gz
```

---

## Troubleshooting

### Connection Issues

**Problem:** `Failed to connect to MQTT broker`

**Solution:**
```bash
# Check MQTT service status
railway logs --service mosquitto

# Verify credentials
MQTT_USERNAME=iot_user
MQTT_PASSWORD=check_in_env

# Test connection
mosquitto_sub -h $MQTT_BROKER_HOST -p $MQTT_BROKER_PORT \
  -u $MQTT_USERNAME -P $MQTT_PASSWORD -t "test/topic"
```

### Database Connection Errors

**Problem:** `OperationalError: Failed to establish database connection`

**Solution:**
```bash
# Verify credentials
echo $DATABASE_URL

# Test connection
# MySQL:
mysql -h HOST -u USER -p DATABASE -e "SELECT 1;"

# PostgreSQL:
psql -h HOST -U USER -d DATABASE -c "SELECT 1;"
```

### Out of Memory

**Problem:** `Container killed due to out-of-memory`

**Solution:**
```bash
# Increase Railway plan to allocate more RAM
# Or optimize database pool:
DB_POOL_SIZE=10  # Reduce from 20
DB_MAX_OVERFLOW=20  # Reduce from 40

# Check memory usage
railway logs | grep "Memory"
```

### Redis Connection Issues

**Problem:** `ConnectionError: Failed to connect to Redis`

**Solution:**
```bash
# Verify Redis is running
redis-cli -u redis://default:PASSWORD@HOST:PORT ping
# Should return: PONG

# Check connection URL
echo $REDIS_URL

# Monitor Redis
redis-cli -u redis://default:PASSWORD@HOST:PORT MONITOR
```

---

## Security Best Practices

### 1. Environment Variables

```bash
# ✅ DO: Use Railway secrets manager
railway env:set SECRET_KEY="$(openssl rand -base64 48)"

# ❌ DON'T: Commit .env to Git
echo ".env" >> .gitignore

# ❌ DON'T: Share credentials publicly
```

### 2. Database Access

```bash
# ✅ Use strong passwords
DATABASE_PASSWORD=$(openssl rand -base64 16)

# ✅ Enable SSL for database connections
DATABASE_URL="postgresql+psycopg://USER:PASS@HOST:PORT/DB?sslmode=require"

# ✅ Use VPC/private networks when available
```

### 3. API Security

```env
# Enforce HTTPS in production
ENFORCE_HTTPS=true

# Set secure CORS
CORS_ORIGINS=["https://your-domain.com"]

# Enable rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_USER=100

# Use API keys for devices
# Device API Key example: sk_water_xxx...
```

### 4. Backup Security

```bash
# Enable encryption
BACKUP_ENCRYPTION_KEY="$(openssl rand -base64 32)"

# Store backups in S3 with server-side encryption
S3_STORAGE_CLASS=STANDARD_IA

# Automate cleanup
BACKUP_RETENTION_DAYS=30
```

---

## Performance Optimization

### Database Optimization

```env
# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30

# For large datasets, use read replicas
# Example: Enable RDS read replica in AWS/Railway
```

### Caching Strategy

```env
# Redis caching
REDIS_URL=redis://...

# Cache sensor readings (5 minutes)
CACHE_SENSOR_READINGS=300

# Cache alert statistics (15 minutes)
CACHE_ALERT_STATS=900
```

### Monitoring and Metrics

```env
# Enable Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Set up Grafana dashboard
# Visit: https://grafana.com
```

---

## Scaling Considerations

### Vertical Scaling (Increase Resources)

```bash
# In Railway dashboard:
# 1. Select project
# 2. Click service (Backend)
# 3. Settings → Plan
# 4. Choose higher tier
```

### Horizontal Scaling (Multiple Instances)

```bash
# Configure auto-scaling in Railway:
# 1. Project Settings
# 2. Deploy → Scale
# 3. Set replica count

# Use load balancer (Railway provides)
```

### Database Scaling

```bash
# For high load:
# 1. Enable RDS read replicas
# 2. Implement connection pooling
# 3. Use database caching
# 4. Optimize queries with indexes
```

---

## Next Steps

1. **Monitor the deployment**: Check logs and health endpoints
2. **Set up alerts**: Configure email notifications for failures
3. **Configure backups**: Verify daily backups to S3
4. **Test IoT sensors**: Connect test sensors and verify data flow
5. **Set up CI/CD**: Use GitHub Actions for automated deployments
6. **Scale as needed**: Monitor performance and scale appropriately

---

## Support and Documentation

- **Railway Docs**: https://docs.railway.app
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **PostgreSQL Docs**: https://www.postgresql.org/docs
- **MQTT Docs**: https://mqtt.org
- **S3 API**: https://docs.aws.amazon.com/s3

---

## Appendix: Quick Reference

### Essential Commands

```bash
# Deploy
railway up

# View logs
railway logs -f

# Set env variable
railway env:set KEY=VALUE

# SSH into container
railway shell

# Run migration
railway shell
python backend/scripts/init_db.py

# Create backup
railway shell
python backend/scripts/backup.sh
```

### Health Check URLs

```
Health:         https://app.railway.app/monitoring/health
API Docs:       https://app.railway.app/docs
System Status:  https://app.railway.app/monitoring/system-status
Metrics:        https://app.railway.app/monitoring/metrics
```

### Important URLs

- **API Endpoint**: `https://your-app-url.railway.app`
- **WebSocket**: `wss://your-app-url.railway.app/ws`
- **MQTT Broker**: `your-mqtt-broker:1883`

---

Last Updated: 2024-02-22
Version: 2.0.0
