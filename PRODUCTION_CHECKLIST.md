# Production Deployment Checklist

## 🚀 National Water Infrastructure Monitoring System

---

## Pre-Deployment Checklist

### 1. Security ✅
- [ ] All credentials removed from source code
- [ ] `.env.production` configured with real credentials
- [ ] SECRET_KEY is strong (48+ characters)
- [ ] Database passwords are complex
- [ ] API keys generated and secured
- [ ] TLS/SSL certificates obtained
- [ ] HTTPS enforcement enabled
- [ ] CORS origins restricted to production domains
- [ ] Rate limiting configured
- [ ] Security headers enabled
- [ ] Firewall rules configured
- [ ] VPN access for admin configured

### 2. Database ✅
- [ ] PostgreSQL/MySQL instance provisioned
- [ ] PostGIS extension installed (if using PostgreSQL)
- [ ] Database user created with limited privileges
- [ ] Connection pooling configured
- [ ] SSL connections enabled
- [ ] Backup strategy implemented
- [ ] Migration scripts tested
- [ ] Indexes created
- [ ] Performance tuning applied

### 3. Redis ✅
- [ ] Redis instance provisioned
- [ ] Password authentication enabled
- [ ] Persistence configured
- [ ] Memory limits set
- [ ] Connection pooling configured

### 4. S3 Storage ✅
- [ ] S3 bucket created
- [ ] Access keys generated
- [ ] Bucket policy configured
- [ ] Versioning enabled
- [ ] Lifecycle policies set
- [ ] Backup retention configured

### 5. MQTT Broker ✅
- [ ] Mosquitto/EMQX deployed
- [ ] TLS certificates installed
- [ ] Authentication configured
- [ ] ACL rules defined
- [ ] Port 8883 opened
- [ ] Client certificates generated

### 6. Application Configuration ✅
- [ ] Environment variables set
- [ ] DEBUG=false
- [ ] ENVIRONMENT=production
- [ ] Logging level configured
- [ ] Monitoring enabled
- [ ] Metrics collection enabled
- [ ] Error tracking configured

### 7. Monitoring & Observability ✅
- [ ] Prometheus configured
- [ ] Grafana dashboards created
- [ ] Alert rules defined
- [ ] Log aggregation setup
- [ ] Uptime monitoring configured
- [ ] Performance monitoring enabled
- [ ] Error tracking (Sentry) configured

### 8. Backup & Recovery ✅
- [ ] Automated backups scheduled
- [ ] Backup retention policy set
- [ ] Backup encryption enabled
- [ ] Recovery procedures documented
- [ ] Backup restoration tested
- [ ] Disaster recovery plan created

### 9. Testing ✅
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] API tests passing
- [ ] Load tests completed
- [ ] Security tests passed
- [ ] End-to-end tests completed

### 10. Documentation ✅
- [ ] API documentation updated
- [ ] Deployment guide created
- [ ] Security guide reviewed
- [ ] ER diagram documented
- [ ] Architecture diagram created
- [ ] Runbooks created
- [ ] Incident response plan documented

---

## Deployment Steps

### Step 1: Infrastructure Setup

```bash
# 1. Provision database
# Railway: Add PostgreSQL service
# Or use existing: interchange.proxy.rlwy.net:20906

# 2. Provision Redis
# Railway: Add Redis service
# Or use existing: switchyard.proxy.rlwy.net:10457

# 3. Configure S3
# Use existing: t3.storageapi.dev
```

### Step 2: Environment Configuration

```bash
# Copy production environment template
cp backend/.env.production backend/.env

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"

# Update .env with generated key and credentials
```

### Step 3: Deploy Application

#### Option A: Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
python scripts/deploy_production.py
```

#### Option B: Docker Deployment
```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

#### Option C: Kubernetes Deployment
```bash
# Apply configurations
kubectl apply -f kubernetes/production-deployment.yaml

# Verify deployment
kubectl get pods -n water-monitoring
```

### Step 4: Database Initialization

```bash
# Run migrations
railway run python backend/scripts/init_db.py

# Or with Docker
docker-compose exec backend python scripts/init_db.py

# Or with Kubernetes
kubectl exec -it deployment/backend -n water-monitoring -- python scripts/init_db.py
```

### Step 5: Create Admin User

```bash
# Connect to backend
railway run python

# Or
docker-compose exec backend python

# Create admin
from app.core.database import SessionLocal
from app.models.user import User
from app.models.municipality import Municipality
from app.core.security import get_password_hash

db = SessionLocal()

# Create municipality
muni = Municipality(
    id="national-admin",
    name="National Administration",
    code="NAT001",
    region="National"
)
db.add(muni)

# Create admin user
admin = User(
    id="admin-001",
    username="admin",
    email="admin@water-monitoring.gov",
    hashed_password=get_password_hash("ChangeThisPassword123!"),
    full_name="System Administrator",
    municipality_id=muni.id,
    is_super_admin=True,
    is_active=True
)
db.add(admin)
db.commit()
```

### Step 6: Configure MQTT Broker

```bash
# Generate passwords
mosquitto_passwd -c /etc/mosquitto/passwd mqtt_user

# Configure TLS
# Copy certificates to /etc/mosquitto/certs/

# Restart broker
systemctl restart mosquitto
```

### Step 7: Verify Deployment

```bash
# Check health endpoint
curl https://your-domain.com/health

# Check API docs
curl https://your-domain.com/docs

# Check metrics
curl https://your-domain.com/metrics

# Test authentication
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=ChangeThisPassword123!"
```

---

## Post-Deployment Verification

### 1. System Health ✅
```bash
# Check all services
curl https://your-domain.com/health

# Expected: {"status": "healthy"}
```

### 2. Database Connectivity ✅
```bash
# Test database connection
railway run python -c "from app.core.database import engine; print(engine.connect())"
```

### 3. Redis Connectivity ✅
```bash
# Test Redis
railway run python -c "import redis; r=redis.from_url('$REDIS_URL'); print(r.ping())"
```

### 4. MQTT Connectivity ✅
```bash
# Test MQTT
mosquitto_sub -h your-mqtt-broker -p 8883 -t "sensors/#" --cafile ca.crt -u mqtt_user -P password
```

### 5. WebSocket Connectivity ✅
```bash
# Test WebSocket
wscat -c "wss://your-domain.com/ws/global?token=YOUR_TOKEN"
```

### 6. Sensor Ingestion ✅
```bash
# Test HTTP ingestion
curl -X POST https://your-domain.com/api/v1/sensors/TEST_001/readings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"value": 3.5, "timestamp": "2024-01-15T10:00:00Z"}'
```

### 7. Alert Generation ✅
```bash
# Trigger anomaly
curl -X POST https://your-domain.com/api/v1/sensors/TEST_001/readings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"value": 15.0, "timestamp": "2024-01-15T10:01:00Z"}'

# Check alerts
curl https://your-domain.com/api/v1/alerts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 8. Monitoring ✅
```bash
# Check Prometheus metrics
curl https://your-domain.com/metrics

# Verify metrics are being collected
# Look for: http_requests_total, sensor_readings_total, etc.
```

### 9. Backup System ✅
```bash
# Trigger manual backup
railway run python -c "from app.services.backup_service import BackupService; BackupService().create_backup()"

# Verify backup in S3
aws s3 ls s3://your-bucket/backups/
```

### 10. Performance ✅
```bash
# Run load test
cd iot-gateway
locust -f load_test.py --headless -u 100 -r 10 -t 60s --host https://your-domain.com
```

---

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'water-monitoring'
    static_configs:
      - targets: ['your-domain.com:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboards

1. **System Overview**
   - HTTP request rate
   - Response times
   - Error rates
   - Active connections

2. **Sensor Metrics**
   - Readings per second
   - Anomaly detection rate
   - Sensor health status
   - Protocol distribution

3. **Alert Metrics**
   - Active alerts by severity
   - Alert generation rate
   - Resolution time
   - Alert types distribution

4. **Infrastructure**
   - Database connections
   - Redis memory usage
   - MQTT message rate
   - WebSocket connections

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Revert to previous version
railway rollback

# Or with Docker
docker-compose down
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# Or with Kubernetes
kubectl rollout undo deployment/backend -n water-monitoring

# 2. Restore database from backup
railway run python scripts/restore.sh backup-2024-01-15.sql

# 3. Verify rollback
curl https://your-domain.com/health

# 4. Notify team
# Send notification to team about rollback
```

---

## Maintenance Windows

### Scheduled Maintenance
- **Weekly**: Sunday 02:00-04:00 UTC
- **Monthly**: First Sunday 02:00-06:00 UTC

### Maintenance Tasks
- Database optimization
- Index rebuilding
- Log rotation
- Certificate renewal
- Security updates
- Dependency updates

---

## Support Contacts

### Emergency Contacts
- **On-Call Engineer**: +27-XXX-XXXX
- **Database Admin**: +27-XXX-XXXX
- **Security Team**: security@water-monitoring.gov
- **DevOps Team**: devops@water-monitoring.gov

### Escalation Path
1. On-Call Engineer (Response: 15 min)
2. Team Lead (Response: 30 min)
3. CTO (Response: 1 hour)

---

## Success Criteria

Deployment is successful when:

- [ ] All health checks passing
- [ ] API responding within 200ms (p95)
- [ ] Database queries < 100ms (p95)
- [ ] WebSocket connections stable
- [ ] MQTT messages processing
- [ ] Alerts generating correctly
- [ ] Monitoring dashboards showing data
- [ ] Backups running successfully
- [ ] No critical errors in logs
- [ ] Load test passing (100 concurrent users)

---

## Sign-Off

**Deployment Date**: _______________

**Deployed By**: _______________

**Verified By**: _______________

**Approved By**: _______________

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Next Review**: 2024-02-15
