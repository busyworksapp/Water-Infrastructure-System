# Production Deployment Checklist

## Pre-Deployment Verification

### 1. Environment Configuration ✓
- [ ] All environment variables set in `.env.production`
- [ ] Database credentials verified (MySQL/PostgreSQL)
- [ ] Redis connection tested
- [ ] S3 storage credentials configured
- [ ] MQTT broker accessible
- [ ] Secret keys generated (min 32 characters)
- [ ] CORS origins configured for production domains
- [ ] TLS/SSL certificates installed

### 2. Database Setup ✓
- [ ] Database created and accessible
- [ ] PostGIS extension enabled (for PostgreSQL)
- [ ] All migrations applied: `alembic upgrade head`
- [ ] Initial data seeded (municipalities, roles, admin user)
- [ ] Database backups configured
- [ ] Connection pooling optimized

### 3. Security Hardening ✓
- [ ] All hardcoded credentials removed
- [ ] `.env.production` added to `.gitignore`
- [ ] Security middleware enabled (8 layers)
- [ ] Rate limiting configured
- [ ] HTTPS redirect enabled
- [ ] Security headers set
- [ ] SQL injection protection active
- [ ] DDoS protection configured
- [ ] Audit logging enabled

### 4. Service Dependencies ✓
- [ ] Redis server running
- [ ] MQTT broker (Mosquitto) running
- [ ] Celery workers started
- [ ] TCP server configured (port 9999)
- [ ] WebSocket connections tested

### 5. Code Quality ✓
- [ ] All tests passing: `pytest tests/`
- [ ] No placeholder code remaining
- [ ] Linting passed: `flake8` or `pylint`
- [ ] Type checking passed: `mypy` (if used)
- [ ] Code coverage > 80%

### 6. Performance Optimization ✓
- [ ] Database indexes created
- [ ] Query optimization completed
- [ ] Caching strategy implemented (Redis)
- [ ] Connection pooling configured
- [ ] Static file compression enabled
- [ ] CDN configured (if applicable)

### 7. Monitoring & Observability ✓
- [ ] Prometheus metrics enabled
- [ ] Grafana dashboards configured
- [ ] Log aggregation setup (ELK/CloudWatch)
- [ ] Error tracking configured (Sentry)
- [ ] Uptime monitoring active
- [ ] Alert notifications configured

### 8. Backup & Recovery ✓
- [ ] Automated database backups scheduled
- [ ] Backup restoration tested
- [ ] S3 backup retention policy set
- [ ] Disaster recovery plan documented
- [ ] Backup monitoring alerts configured

### 9. API Documentation ✓
- [ ] Swagger UI accessible at `/docs`
- [ ] ReDoc accessible at `/redoc`
- [ ] API versioning implemented
- [ ] Authentication documented
- [ ] Rate limits documented
- [ ] Error codes documented

### 10. Mobile & Frontend ✓
- [ ] Control room app built: `npm run electron-build`
- [ ] Mobile app built for iOS/Android
- [ ] API endpoints configured in apps
- [ ] Push notifications tested
- [ ] Offline mode tested
- [ ] WebSocket connections verified

---

## Deployment Steps

### Step 1: Prepare Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
cp .env.example .env.production
# Edit .env.production with production credentials
export $(cat .env.production | xargs)
```

### Step 3: Database Migration
```bash
alembic upgrade head
python scripts/init_db.py
```

### Step 4: Start Services
```bash
# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Start Celery workers
celery -A app.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info
```

### Step 5: Verify Deployment
```bash
# Test health endpoint
curl http://localhost:8000/health

# Run comprehensive tests
python tests/test_api_comprehensive.py
```

### Step 6: Monitor Logs
```bash
# View application logs
tail -f logs/app.log

# View Celery logs
tail -f logs/celery.log
```

---

## Docker Deployment

### Using Docker Compose
```bash
docker-compose up -d
docker-compose logs -f
```

### Using Kubernetes
```bash
kubectl apply -f kubernetes/production-deployment.yaml
kubectl get pods
kubectl logs -f <pod-name>
```

---

## Railway Deployment

### Automated Deployment
```bash
python scripts/deploy_production.py
```

### Manual Deployment
1. Push code to GitHub
2. Connect Railway to repository
3. Set environment variables in Railway dashboard
4. Deploy from main branch

---

## Post-Deployment Verification

### 1. Functional Testing
- [ ] User login works
- [ ] Sensor data ingestion working
- [ ] Alerts generating correctly
- [ ] WebSocket real-time updates working
- [ ] MQTT messages received
- [ ] Email notifications sent
- [ ] SMS notifications sent (if configured)
- [ ] Push notifications working

### 2. Performance Testing
- [ ] API response times < 200ms (p95)
- [ ] Database query times acceptable
- [ ] WebSocket latency < 100ms
- [ ] Memory usage stable
- [ ] CPU usage < 70% under load
- [ ] No memory leaks detected

### 3. Security Testing
- [ ] Authentication required for protected endpoints
- [ ] RBAC working correctly
- [ ] Rate limiting active
- [ ] SQL injection attempts blocked
- [ ] XSS protection working
- [ ] CSRF protection enabled

### 4. Integration Testing
- [ ] IoT sensors connecting successfully
- [ ] External webhooks delivering
- [ ] Email service working
- [ ] SMS service working
- [ ] S3 uploads working
- [ ] Redis caching working

### 5. Monitoring Verification
- [ ] Metrics appearing in Prometheus
- [ ] Grafana dashboards showing data
- [ ] Logs appearing in aggregation system
- [ ] Alerts triggering correctly
- [ ] Health checks passing

---

## Rollback Plan

### If Deployment Fails:

1. **Immediate Rollback**
   ```bash
   # Docker
   docker-compose down
   docker-compose up -d --build <previous-version>
   
   # Kubernetes
   kubectl rollout undo deployment/backend
   ```

2. **Database Rollback**
   ```bash
   alembic downgrade -1
   ```

3. **Restore from Backup**
   ```bash
   python scripts/restore_backup.py --backup-id <backup-id>
   ```

---

## Production Maintenance

### Daily Tasks
- Monitor system health dashboard
- Check error logs
- Verify backup completion
- Review alert statistics

### Weekly Tasks
- Review performance metrics
- Analyze slow queries
- Check disk space
- Update dependencies (security patches)

### Monthly Tasks
- Full system audit
- Capacity planning review
- Security vulnerability scan
- Disaster recovery drill

---

## Support Contacts

- **Technical Lead**: [Contact Info]
- **DevOps Team**: [Contact Info]
- **Database Admin**: [Contact Info]
- **Security Team**: [Contact Info]

---

## Emergency Procedures

### System Down
1. Check health endpoint
2. Review error logs
3. Verify database connectivity
4. Check Redis connection
5. Restart services if needed

### Database Issues
1. Check connection pool
2. Review slow query log
3. Check disk space
4. Verify backup integrity

### Security Incident
1. Isolate affected systems
2. Review audit logs
3. Notify security team
4. Document incident
5. Apply patches/fixes

---

**Deployment Date**: _________________

**Deployed By**: _________________

**Sign-off**: _________________

---

✅ **System Ready for Production**
