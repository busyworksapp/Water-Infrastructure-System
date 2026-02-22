# Security Best Practices & Hardening Guide

## 🔒 Production Security Checklist

### 1. Environment Variables & Secrets Management

#### ✅ DO:
- Store all credentials in environment variables or secrets manager
- Use Railway's environment variables for production
- Generate strong random SECRET_KEY (minimum 48 characters)
- Rotate secrets regularly (every 90 days)
- Use different credentials for each environment

#### ❌ DON'T:
- Never commit `.env` files with real credentials
- Never hardcode credentials in source code
- Never share production credentials via email/chat
- Never use default/example passwords

#### Generate Secure Keys:
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"

# Generate API Key
python backend/app/utils/secrets_manager.py generate-api-key

# Validate secrets
python backend/app/utils/secrets_manager.py validate
```

---

### 2. Database Security

#### PostgreSQL/MySQL Hardening:
```sql
-- Create dedicated user with limited privileges
CREATE USER water_monitoring WITH PASSWORD 'strong_random_password';
GRANT CONNECT ON DATABASE water_monitoring TO water_monitoring;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO water_monitoring;

-- Revoke unnecessary privileges
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Enable SSL connections
ALTER SYSTEM SET ssl = on;
```

#### Connection Security:
- Always use SSL/TLS for database connections
- Use connection pooling with limits
- Implement query timeouts
- Enable audit logging

---

### 3. API Security

#### Authentication:
- JWT tokens with short expiration (30 minutes)
- Refresh tokens with longer expiration (7 days)
- Token blacklisting for logout
- Multi-factor authentication for admin users

#### Authorization:
- Role-Based Access Control (RBAC)
- Municipality-level data isolation
- Permission checks on every endpoint
- Audit logging for all actions

#### Rate Limiting:
```python
# Per-user limits
RATE_LIMIT_PER_USER = 100  # requests per minute

# Per-IP limits
RATE_LIMIT_PER_MINUTE = 60

# API key limits
RATE_LIMIT_PER_API_KEY = 1000
```

---

### 4. HTTPS/TLS Configuration

#### Production Requirements:
- Force HTTPS redirect
- HSTS enabled (max-age=31536000)
- TLS 1.2+ only
- Strong cipher suites
- Valid SSL certificate (Let's Encrypt)

#### Nginx Configuration:
```nginx
server {
    listen 443 ssl http2;
    server_name api.water-monitoring.com;
    
    ssl_certificate /etc/letsencrypt/live/api.water-monitoring.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.water-monitoring.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

---

### 5. MQTT Security

#### Broker Configuration:
```conf
# mosquitto.conf
listener 8883
protocol mqtt
cafile /etc/mosquitto/ca_certificates/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
require_certificate true

# Authentication
allow_anonymous false
password_file /etc/mosquitto/passwd

# ACL
acl_file /etc/mosquitto/acl
```

#### Client Authentication:
- TLS client certificates for devices
- Username/password authentication
- Topic-based ACL
- Device certificate fingerprint validation

---

### 6. Input Validation & Sanitization

#### SQL Injection Prevention:
- Use SQLAlchemy ORM (parameterized queries)
- Never concatenate user input in queries
- Validate all input types
- Implement SQL injection detection middleware

#### XSS Prevention:
- Escape all user-generated content
- Content Security Policy (CSP)
- Sanitize HTML input
- Use secure templating

#### Command Injection Prevention:
- Never execute shell commands with user input
- Use subprocess with argument lists
- Validate file paths
- Restrict file uploads

---

### 7. Network Security

#### Firewall Rules:
```bash
# Allow only necessary ports
ufw allow 443/tcp   # HTTPS
ufw allow 8883/tcp  # MQTT over TLS
ufw deny 8000/tcp   # Block direct backend access
ufw enable
```

#### Network Segmentation:
- Backend in private subnet
- Database in isolated subnet
- Load balancer in public subnet
- VPN for admin access

---

### 8. Monitoring & Alerting

#### Security Monitoring:
- Failed authentication attempts
- Unusual API access patterns
- Database query anomalies
- Certificate expiration warnings
- Unauthorized access attempts

#### Prometheus Alerts:
```yaml
groups:
- name: security
  rules:
  - alert: HighFailedAuthRate
    expr: rate(http_requests_total{status="401"}[5m]) > 10
    annotations:
      summary: "High rate of failed authentication attempts"
  
  - alert: UnauthorizedAccess
    expr: rate(http_requests_total{status="403"}[5m]) > 5
    annotations:
      summary: "Multiple unauthorized access attempts detected"
```

---

### 9. Backup & Disaster Recovery

#### Automated Backups:
```bash
# Daily database backup
0 2 * * * /app/scripts/backup.sh

# Backup retention: 30 days
# Backup encryption: AES-256
# Backup location: S3 with versioning
```

#### Recovery Testing:
- Test backups monthly
- Document recovery procedures
- Maintain offline backups
- Verify backup integrity

---

### 10. Compliance & Auditing

#### Audit Logging:
- Log all authentication events
- Log all data modifications
- Log all admin actions
- Log all API access
- Retain logs for 1 year

#### GDPR Compliance:
- Data encryption at rest and in transit
- Right to erasure implementation
- Data portability support
- Privacy policy enforcement
- Consent management

---

### 11. IoT Device Security

#### Device Authentication:
- Unique device certificates
- Certificate rotation every 90 days
- Device fingerprint validation
- API key per device

#### Device Management:
- Device registration workflow
- Certificate revocation list
- Device health monitoring
- Automatic device deactivation

---

### 12. Incident Response

#### Security Incident Procedure:
1. **Detect**: Monitor alerts and logs
2. **Contain**: Isolate affected systems
3. **Investigate**: Analyze attack vectors
4. **Remediate**: Patch vulnerabilities
5. **Document**: Record incident details
6. **Review**: Update security measures

#### Emergency Contacts:
- Security Team: security@water-monitoring.com
- On-Call Engineer: +27-XXX-XXXX
- Incident Hotline: Available 24/7

---

### 13. Security Testing

#### Regular Security Audits:
- Quarterly penetration testing
- Monthly vulnerability scans
- Weekly dependency updates
- Daily security monitoring

#### Tools:
```bash
# Dependency vulnerability scanning
pip-audit

# Static code analysis
bandit -r backend/

# Container scanning
trivy image water-monitoring-backend:latest

# API security testing
zap-cli quick-scan http://api.water-monitoring.com
```

---

### 14. Production Deployment Checklist

Before deploying to production:

- [ ] All secrets stored in environment variables
- [ ] SECRET_KEY is strong and unique
- [ ] HTTPS enforced with valid certificate
- [ ] Database uses SSL connections
- [ ] MQTT uses TLS encryption
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] CORS properly restricted
- [ ] Audit logging enabled
- [ ] Monitoring and alerting configured
- [ ] Backups automated and tested
- [ ] Firewall rules configured
- [ ] Security testing completed
- [ ] Incident response plan documented
- [ ] Team trained on security procedures

---

### 15. Security Contacts & Resources

#### Report Security Issues:
- Email: security@water-monitoring.com
- PGP Key: Available on request
- Response Time: Within 24 hours

#### Security Resources:
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CWE Top 25: https://cwe.mitre.org/top25/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework

---

## 🚨 Emergency Procedures

### Suspected Breach:
1. Immediately rotate all credentials
2. Review audit logs for unauthorized access
3. Isolate affected systems
4. Notify security team
5. Document all findings
6. Implement additional security measures

### Certificate Expiration:
1. Monitor certificate expiration (30 days warning)
2. Renew certificates before expiration
3. Test new certificates in staging
4. Deploy to production during maintenance window
5. Verify all services operational

---

**Last Updated**: 2024-01-15  
**Next Review**: 2024-04-15  
**Document Owner**: Security Team
