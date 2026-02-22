# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  Control Room    │  │   Mobile App     │  │  Web Portal   │ │
│  │  (Electron)      │  │  (React Native)  │  │  (Optional)   │ │
│  │  - Dashboard     │  │  - Alerts        │  │  - Reports    │ │
│  │  - GIS Maps      │  │  - Sensors       │  │  - Analytics  │ │
│  │  - Alerts        │  │  - Incidents     │  │               │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│           │                     │                     │          │
└───────────┼─────────────────────┼─────────────────────┼──────────┘
            │                     │                     │
            └─────────────────────┴─────────────────────┘
                                  │
                        ┌─────────▼──────────┐
                        │   Load Balancer    │
                        │   (Nginx/HAProxy)  │
                        └─────────┬──────────┘
                                  │
┌─────────────────────────────────▼─────────────────────────────────┐
│                      APPLICATION LAYER                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              FastAPI Backend (Python 3.12)                  │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐ │  │
│  │  │   API    │  │   MQTT   │  │WebSocket │  │  Celery   │ │  │
│  │  │  Routes  │  │  Client  │  │ Manager  │  │  Workers  │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └───────────┘ │  │
│  │                                                              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐ │  │
│  │  │ Anomaly  │  │  Alert   │  │   Auth   │  │   GIS     │ │  │
│  │  │ Detector │  │ Service  │  │ Service  │  │  Service  │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └───────────┘ │  │
│  │                                                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
┌───────────────────▼──┐  ┌───────▼──────┐  ┌──▼──────────────┐
│   MQTT Broker        │  │   Redis      │  │   Message Queue │
│   (Mosquitto)        │  │   Cache      │  │   (Celery)      │
│   - IoT Messages     │  │   - Sessions │  │   - Background  │
│   - Pub/Sub          │  │   - Pub/Sub  │  │   - Jobs        │
└──────────────────────┘  └──────────────┘  └─────────────────┘
            │
┌───────────▼────────────────────────────────────────────────────┐
│                      IoT DEVICE LAYER                           │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  MQTT    │  │  HTTP    │  │   TCP    │  │ LoRaWAN  │      │
│  │ Sensors  │  │ Sensors  │  │ Sensors  │  │ Gateway  │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │  NB-IoT  │  │   GSM    │  │   Edge   │                     │
│  │ Sensors  │  │ Sensors  │  │ Gateway  │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼─────────────────────────────────┐
│                      DATA LAYER                                    │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────┐  ┌────────────────────────┐          │
│  │   MySQL/PostgreSQL     │  │      S3 Storage        │          │
│  │   + PostGIS            │  │   - Attachments        │          │
│  │   - Users              │  │   - Reports            │          │
│  │   - Sensors            │  │   - Backups            │          │
│  │   - Readings           │  │                        │          │
│  │   - Alerts             │  │                        │          │
│  │   - Pipelines (GIS)    │  │                        │          │
│  └────────────────────────┘  └────────────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Sensor Reading Flow

```
IoT Sensor → MQTT Broker → Backend MQTT Client → Validate Device
                                                        ↓
                                                  Store Reading
                                                        ↓
                                              Anomaly Detection
                                                        ↓
                                              Check Dynamic Rules
                                                        ↓
                                            Generate Alert (if needed)
                                                        ↓
                                    ┌───────────────────┴───────────────────┐
                                    ↓                                       ↓
                            WebSocket Broadcast                      Notification Service
                                    ↓                                       ↓
                        ┌───────────┴───────────┐                   Email/SMS/Push
                        ↓                       ↓
                Control Room App          Mobile App
```

### 2. Alert Management Flow

```
Alert Created → Store in Database → Broadcast via WebSocket
                                              ↓
                                    ┌─────────┴─────────┐
                                    ↓                   ↓
                            Control Room          Mobile App
                                    ↓                   ↓
                            User Acknowledges    User Acknowledges
                                    ↓                   ↓
                            Update Status        Update Status
                                    ↓                   ↓
                            Investigate          Create Incident
                                    ↓                   ↓
                            Resolve Alert        Log Maintenance
```

### 3. Authentication Flow

```
User Login → API Request → Validate Credentials → Generate JWT
                                                        ↓
                                                  Return Tokens
                                                        ↓
                                            Store in Local Storage
                                                        ↓
                                        Subsequent Requests with Token
                                                        ↓
                                            Validate JWT Middleware
                                                        ↓
                                            Check Permissions (RBAC)
                                                        ↓
                                            Process Request
```

## Multi-Tenant Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Super Admin Level                         │
│  - Manage all municipalities                                 │
│  - System-wide analytics                                     │
│  - Global configuration                                      │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌──────▼─────────┐
│ Municipality A │  │ Municipality B │  │Municipality C  │
│  - Own Users   │  │  - Own Users   │  │  - Own Users   │
│  - Own Sensors │  │  - Own Sensors │  │  - Own Sensors │
│  - Own Alerts  │  │  - Own Alerts  │  │  - Own Alerts  │
│  - Own Data    │  │  - Own Data    │  │  - Own Data    │
└────────────────┘  └────────────────┘  └────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Layer 1: Network Security                                   │
│  ├─ Firewall Rules                                          │
│  ├─ DDoS Protection                                         │
│  └─ VPN Access                                              │
│                                                               │
│  Layer 2: Transport Security                                 │
│  ├─ TLS/SSL Encryption                                      │
│  ├─ Certificate Pinning                                     │
│  └─ Secure WebSocket (WSS)                                  │
│                                                               │
│  Layer 3: Application Security                               │
│  ├─ JWT Authentication                                      │
│  ├─ Role-Based Access Control                              │
│  ├─ Rate Limiting                                           │
│  └─ Input Validation                                        │
│                                                               │
│  Layer 4: Data Security                                      │
│  ├─ Encrypted at Rest                                       │
│  ├─ Encrypted in Transit                                    │
│  ├─ Data Masking                                            │
│  └─ Audit Logging                                           │
│                                                               │
│  Layer 5: Device Security                                    │
│  ├─ Device Certificates                                     │
│  ├─ API Key Authentication                                  │
│  └─ Device Whitelisting                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Scalability Strategy

### Horizontal Scaling

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                             │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌──────▼─────────┐
│  Backend Pod 1 │  │  Backend Pod 2 │  │  Backend Pod N │
└────────────────┘  └────────────────┘  └────────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼────────┐      ┌──────▼─────────┐
        │  Database      │      │  Redis Cluster │
        │  (Read Replica)│      │                │
        └────────────────┘      └────────────────┘
```

### Auto-Scaling Rules

- CPU > 70% → Scale up
- Memory > 80% → Scale up
- Request queue > 100 → Scale up
- CPU < 30% for 5 min → Scale down

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Metrics                       │
│  - Request Rate                                              │
│  - Response Time                                             │
│  - Error Rate                                                │
│  - Active Connections                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Prometheus                                │
│  - Scrape Metrics                                            │
│  - Store Time Series                                         │
│  - Alert Rules                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼────────┐      ┌──────▼─────────┐
        │    Grafana     │      │  AlertManager  │
        │  - Dashboards  │      │  - Notifications│
        │  - Visualization│      │  - Escalation  │
        └────────────────┘      └────────────────┘
```

## Disaster Recovery

```
┌─────────────────────────────────────────────────────────────┐
│                    Primary Region                            │
│  - Active Services                                           │
│  - Real-time Processing                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                    Continuous Replication
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Secondary Region                          │
│  - Standby Services                                          │
│  - Replicated Data                                           │
│  - Ready for Failover                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                    Automated Failover
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backup Storage                            │
│  - Daily Snapshots                                           │
│  - Point-in-Time Recovery                                    │
│  - 90-day Retention                                          │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Electron + React | Desktop Control Room |
| Mobile | React Native | Mobile Application |
| Backend | FastAPI (Python 3.12) | API Server |
| Database | MySQL/PostgreSQL + PostGIS | Data Storage |
| Cache | Redis | Caching & Pub/Sub |
| Message Queue | Celery + Redis | Background Jobs |
| IoT Protocol | MQTT (Mosquitto) | Sensor Communication |
| Real-time | WebSocket | Live Updates |
| Storage | S3-Compatible | File Storage |
| Monitoring | Prometheus + Grafana | Observability |
| Container | Docker | Containerization |
| Orchestration | Kubernetes | Container Orchestration |
| CI/CD | GitHub Actions | Automation |
