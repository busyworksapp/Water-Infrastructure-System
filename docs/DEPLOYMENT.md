# Deployment Guide

## Production Deployment Checklist

### Pre-Deployment

- [ ] Update all credentials and secrets
- [ ] Configure production database
- [ ] Set up Redis cluster
- [ ] Configure S3 storage
- [ ] Set up MQTT broker with TLS
- [ ] Configure domain and SSL certificates
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Test disaster recovery procedures

---

## Docker Deployment

### 1. Build Images

```bash
# Backend
cd backend
docker build -t water-monitoring-backend:latest .

# Control Room (optional)
cd ../frontend-control-room
docker build -t water-monitoring-frontend:latest .
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env

# Update these critical values:
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - DATABASE_URL
# - REDIS_URL
# - MQTT credentials
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps
```

### 4. Initialize Database

```bash
# Run initialization script
docker-compose exec backend python scripts/init_db.py
```

### 5. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Check MQTT broker
mosquitto_sub -h localhost -p 1883 -t 'sensors/#' -v
```

---

## Kubernetes Deployment

### 1. Prerequisites

```bash
# Install kubectl
# Install helm (optional)
# Configure kubectl to connect to your cluster
kubectl cluster-info
```

### 2. Create Namespace

```bash
kubectl create namespace water-monitoring
```

### 3. Configure Secrets

```bash
# Create secret for sensitive data
kubectl create secret generic water-monitoring-secrets \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=S3_ACCESS_KEY='your-access-key' \
  --from-literal=S3_SECRET_KEY='your-secret-key' \
  -n water-monitoring
```

### 4. Deploy Application

```bash
# Apply all configurations
kubectl apply -f kubernetes/

# Check deployment status
kubectl get pods -n water-monitoring
kubectl get services -n water-monitoring

# View logs
kubectl logs -f deployment/backend -n water-monitoring
```

### 5. Scale Application

```bash
# Manual scaling
kubectl scale deployment backend --replicas=5 -n water-monitoring

# Auto-scaling is configured via HPA in deployment.yaml
kubectl get hpa -n water-monitoring
```

### 6. Update Application

```bash
# Update image
kubectl set image deployment/backend backend=water-monitoring-backend:v2 -n water-monitoring

# Rollback if needed
kubectl rollout undo deployment/backend -n water-monitoring

# Check rollout status
kubectl rollout status deployment/backend -n water-monitoring
```

---

## Database Setup

### MySQL/PostgreSQL

```sql
-- Create database
CREATE DATABASE water_monitoring;

-- Create user
CREATE USER 'water_user'@'%' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON water_monitoring.* TO 'water_user'@'%';
FLUSH PRIVILEGES;

-- Enable PostGIS (PostgreSQL only)
CREATE EXTENSION postgis;
```

### Initialize Schema

```bash
# Using Python script
cd backend
python scripts/init_db.py

# Or using Alembic migrations
alembic upgrade head
```

---

## Redis Setup

### Standalone Redis

```bash
# Install Redis
apt-get install redis-server

# Configure Redis
nano /etc/redis/redis.conf

# Set password
requirepass your_secure_password

# Restart Redis
systemctl restart redis
```

### Redis Cluster (Production)

```bash
# Use managed Redis service (AWS ElastiCache, Azure Cache, etc.)
# Or deploy Redis Cluster with Kubernetes
```

---

## MQTT Broker Setup

### Mosquitto with TLS

```bash
# Generate certificates
openssl req -new -x509 -days 365 -extensions v3_ca \
  -keyout ca.key -out ca.crt

openssl genrsa -out server.key 2048
openssl req -new -out server.csr -key server.key
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 365

# Configure Mosquitto
listener 8883
protocol mqtt
cafile /mosquitto/config/ca.crt
certfile /mosquitto/config/server.crt
keyfile /mosquitto/config/server.key
require_certificate false

# Create password file
mosquitto_passwd -c /mosquitto/config/passwd username

# Restart Mosquitto
docker-compose restart mqtt-broker
```

---

## Monitoring Setup

### Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'water-monitoring'
    static_configs:
      - targets: ['backend:8000']
```

### Grafana Dashboards

1. Import dashboard for FastAPI metrics
2. Create custom dashboards for:
   - Sensor readings
   - Alert statistics
   - System health
   - API performance

---

## Backup Strategy

### Database Backup

```bash
# MySQL backup
mysqldump -h host -u user -p database > backup_$(date +%Y%m%d).sql

# Automated daily backup
0 2 * * * /usr/local/bin/backup_database.sh
```

### Redis Backup

```bash
# Redis RDB backup
redis-cli BGSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backup/redis_$(date +%Y%m%d).rdb
```

### S3 Backup

```bash
# Backup to S3
aws s3 sync /backup s3://water-monitoring-backups/
```

---

## SSL/TLS Configuration

### Using Let's Encrypt

```bash
# Install certbot
apt-get install certbot

# Generate certificate
certbot certonly --standalone -d api.watermonitoring.gov.za

# Configure nginx
server {
    listen 443 ssl;
    server_name api.watermonitoring.gov.za;
    
    ssl_certificate /etc/letsencrypt/live/api.watermonitoring.gov.za/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.watermonitoring.gov.za/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Performance Tuning

### Backend

```python
# Increase worker processes
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

# Configure connection pooling
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=40
```

### Database

```sql
-- Add indexes
CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(timestamp);
CREATE INDEX idx_sensor_readings_sensor_timestamp ON sensor_readings(sensor_id, timestamp);

-- Partition large tables
ALTER TABLE sensor_readings PARTITION BY RANGE (YEAR(timestamp));
```

### Redis

```conf
# Increase max memory
maxmemory 2gb
maxmemory-policy allkeys-lru
```

---

## Security Hardening

### Firewall Rules

```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8883/tcp  # MQTT TLS
ufw enable
```

### Application Security

```bash
# Set secure environment variables
export SECRET_KEY=$(openssl rand -hex 32)

# Disable debug mode
export DEBUG=false

# Configure CORS properly
export CORS_ORIGINS='["https://app.watermonitoring.gov.za"]'
```

---

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Database connection failed: Check DATABASE_URL
# - Redis connection failed: Check REDIS_URL
# - Port already in use: Change port in docker-compose.yml
```

### MQTT connection issues

```bash
# Test MQTT connection
mosquitto_sub -h localhost -p 1883 -t 'test' -u username -P password

# Check broker logs
docker-compose logs mqtt-broker
```

### High memory usage

```bash
# Check container stats
docker stats

# Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
```

---

## Maintenance

### Update Dependencies

```bash
# Backend
pip install --upgrade -r requirements.txt

# Frontend
npm update
```

### Database Maintenance

```sql
-- Optimize tables
OPTIMIZE TABLE sensor_readings;

-- Clean old data
DELETE FROM sensor_readings WHERE timestamp < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

### Log Rotation

```bash
# Configure logrotate
/var/log/water-monitoring/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

---

## Disaster Recovery

### Restore from Backup

```bash
# Restore database
mysql -h host -u user -p database < backup_20240115.sql

# Restore Redis
redis-cli SHUTDOWN
cp backup_redis.rdb /var/lib/redis/dump.rdb
systemctl start redis

# Restore S3 data
aws s3 sync s3://water-monitoring-backups/ /restore/
```

### Failover Procedure

1. Detect primary failure
2. Promote secondary to primary
3. Update DNS records
4. Verify all services operational
5. Investigate primary failure
6. Restore primary as secondary

---

## Support Contacts

- Technical Support: support@watermonitoring.gov.za
- Emergency Hotline: +27 11 XXX XXXX
- Documentation: https://docs.watermonitoring.gov.za
