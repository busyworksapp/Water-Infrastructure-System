# National Water Infrastructure Monitoring System

## ðŸŒŠ Production-Ready Multi-Tenant IoT Water Monitoring Platform

A comprehensive, scalable, secure system for monitoring national water infrastructure with real-time anomaly detection, GIS mapping, and multi-protocol IoT sensor integration.

---

## ðŸ—ï¸ SYSTEM ARCHITECTURE

### Technology Stack

**Backend:**
- Python 3.12+ with FastAPI (async)
- PostgreSQL/MySQL with PostGIS
- Redis (caching + pub/sub)
- MQTT (paho-mqtt)
- WebSockets
- Celery (background jobs)

**Frontend Control Room:**
- Electron + React (Desktop Application)
- SCADA-style industrial UI
- Real-time WebSocket updates
- Leaflet for GIS mapping

**Mobile App:**
- React Native (Expo)
- Cross-platform (iOS/Android)
- Push notifications
- Offline caching

**IoT Layer:**
- MQTT, HTTP/HTTPS, TCP
- LoRaWAN, NB-IoT, GSM support
- Edge gateway compatible

---

## ðŸ“ PROJECT STRUCTURE

```
randwater/
â”œâ”€â”€ backend/                    # FastAPI Backend
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ api/               # API routes
â”‚   â”‚   â”œâ”€â”€ core/              # Config, database, security
â”‚   â”‚   â”œâ”€â”€ models/            # SQLAlchemy models
â”‚   â”‚   â”œâ”€â”€ mqtt/              # MQTT client
â”‚   â”‚   â”œâ”€â”€ websocket/         # WebSocket manager
â”‚   â”‚   â”œâ”€â”€ services/          # Business logic
â”‚   â”‚   â””â”€â”€ main.py            # Application entry
â”‚   â”œâ”€â”€ requirements.txt
â”‚   â””â”€â”€ Dockerfile
â”‚
â”œâ”€â”€ frontend-control-room/      # Electron Desktop App
â”‚   â”œâ”€â”€ electron/
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”œâ”€â”€ App.js
â”‚   â”‚   â””â”€â”€ App.css
â”‚   â””â”€â”€ package.json
â”‚
â”œâ”€â”€ mobile-app/                 # React Native Mobile
â”‚   â”œâ”€â”€ screens/
â”‚   â”œâ”€â”€ App.js
â”‚   â””â”€â”€ package.json
â”‚
â”œâ”€â”€ iot-gateway/                # IoT Gateway (optional)
â”œâ”€â”€ docker-compose.yml
â””â”€â”€ README.md
```

---

## ðŸš€ QUICK START

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- MySQL/PostgreSQL with PostGIS

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="mysql+pymysql://root:password@host:port/database"
export REDIS_URL="redis://default:password@host:port"
export SECRET_KEY="your-secret-key"

# Run migrations (create tables)
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Control Room Desktop App

```bash
cd frontend-control-room

# Install dependencies
npm install

# Development mode
npm run electron-dev

# Build for production
npm run electron-build
```

### 3. Mobile App

```bash
cd mobile-app

# Install dependencies
npm install

# Start Expo
npm start

# Run on Android
npm run android

# Run on iOS
npm run ios
```

### 4. Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## ðŸ” SECURITY FEATURES

- **JWT Authentication** with refresh tokens
- **Role-Based Access Control (RBAC)**
- **Device Certificate Authentication**
- **TLS/SSL Encryption**
- **Rate Limiting & Throttling**
- **Audit Logging**
- **Zero-Trust Architecture**
- **Encrypted Secrets Storage**

---

## ðŸ“Š DATABASE SCHEMA

### Core Tables

1. **municipalities** - Multi-tenant isolation
2. **users** - User accounts with RBAC
3. **roles** & **permissions** - Access control
4. **pipelines** - PostGIS geometry for water pipelines
5. **sensor_types** - Dynamic sensor type definitions
6. **sensors** - IoT device registry
7. **sensor_readings** - Time-series sensor data
8. **alerts** - Real-time alert management
9. **incidents** - Incident tracking
10. **maintenance_logs** - Maintenance records
11. **device_authentication** - IoT device security
12. **audit_logs** - System audit trail
13. **dynamic_rules** - Configurable alert rules
14. **notification_channels** - Multi-channel notifications

---

## ðŸ”§ CONFIGURATION

### Environment Variables

```bash
# Database
DATABASE_URL=mysql+pymysql://user:pass@host:port/db

# Redis
REDIS_URL=redis://default:pass@host:port

# S3 Storage
S3_ENDPOINT=https://t3.storageapi.dev
S3_BUCKET=your-bucket
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=username
MQTT_PASSWORD=password
MQTT_TLS_ENABLED=true
```

---

## ðŸ“¡ IoT SENSOR INTEGRATION

### MQTT Topics

```
sensors/{device_id}/data       # Sensor readings
sensors/{device_id}/status     # Device status updates
sensors/{device_id}/heartbeat  # Keep-alive messages
```

### Sample Sensor Data Payload

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

### HTTP Endpoint

```bash
POST /api/v1/sensors/{sensor_id}/readings
Authorization: Bearer {device_api_key}

{
  "timestamp": "2024-01-15T10:30:00Z",
  "value": 3.5,
  "unit": "bar"
}
```

---

## ðŸŽ¯ ANOMALY DETECTION

### Methods

1. **Statistical Detection** - Z-score based
2. **Rate of Change** - Sudden value changes
3. **Dynamic Rules** - Configurable thresholds
4. **Pattern Recognition** - Historical analysis

### Alert Types

- Water Leakage
- Pipeline Bursts
- Pressure Anomalies
- Flow Irregularities
- Infrastructure Damage
- Sensor Faults
- Communication Loss

---

## ðŸ—ºï¸ GIS MAPPING

- **PostGIS** spatial database
- **GeoJSON** pipeline representation
- **Interactive maps** with Leaflet
- **Sensor overlays**
- **Real-time heatmaps**
- **Layer toggling**
- **Time-based playback**

---

## ðŸ“± MOBILE APP FEATURES

- Secure JWT authentication
- Real-time alert feed
- Interactive map view
- Sensor detail monitoring
- Incident reporting
- Maintenance logging
- Push notifications
- Offline caching

---

## ðŸ–¥ï¸ CONTROL ROOM FEATURES

### Dashboard Panels
- Live sensor grid
- System health indicators
- Active alerts panel
- Incident management
- National heatmap
- Municipality filtering
- Analytics charts

### Design Style
- Dark industrial theme
- High contrast SCADA interface
- Large readable typography
- Status indicators (Green/Yellow/Red)
- Real-time updates

---

## ðŸ”„ REAL-TIME ENGINE

### Event Flow

1. Sensor sends data via MQTT/HTTP
2. Backend validates device authentication
3. Store reading in database
4. Run anomaly detection algorithms
5. Check dynamic rules
6. Generate alerts if needed
7. Broadcast via WebSocket to:
   - Control room dashboard
   - Mobile apps
   - External systems
8. Log audit trail

---

## ðŸŽ›ï¸ DYNAMIC ADMIN PANEL

Administrators can:
- Create new sensor types
- Modify alert rules
- Add municipalities
- Configure thresholds
- Manage roles & permissions
- Enable/disable protocols
- Create custom dashboards
- Configure notification channels

**No hardcoded values - fully dynamic configuration**

---

## ðŸ“ˆ MONITORING & OBSERVABILITY

- Prometheus-compatible metrics
- Grafana dashboards
- Structured logging
- Performance monitoring
- Error tracking
- Audit trails

---

## ðŸ§ª TESTING

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend-control-room
npm test

# Mobile tests
cd mobile-app
npm test
```

---

## ðŸš¢ DEPLOYMENT

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Kubernetes (Production)

```bash
kubectl apply -f kubernetes/
```

### CI/CD Pipeline

- Automated testing
- Docker image building
- Kubernetes deployment
- Database migrations
- Backup automation

---

## ðŸ“ž API DOCUMENTATION

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ðŸ”’ CREDENTIALS (PROVIDED)

### MySQL Database
```
Host: interchange.proxy.rlwy.net
Port: 20906
User: root
Password: <MYSQL_PASSWORD>
Database: railway
```

### Redis
```
URL: redis://default:<REDIS_PASSWORD>@switchyard.proxy.rlwy.net:10457
```

### S3 Storage
```
Endpoint: https://t3.storageapi.dev
Bucket: recorded-wrap-krk8vsj4wzi
Access Key: <S3_ACCESS_KEY>
Secret Key: <S3_SECRET_KEY>
```

---

## ðŸ› ï¸ TROUBLESHOOTING

### Backend won't start
- Check database connection
- Verify Redis is running
- Check environment variables

### MQTT not connecting
- Verify broker is running
- Check credentials
- Ensure firewall allows port 1883

### WebSocket disconnects
- Check CORS settings
- Verify authentication token
- Check network stability

---

## ðŸ“„ LICENSE

Proprietary - National Water Infrastructure Project

---

## ðŸ‘¥ SUPPORT

For technical support, contact the development team.

---

## ðŸŽ¯ ROADMAP

- [ ] Machine learning anomaly detection
- [ ] Predictive maintenance
- [ ] Advanced analytics dashboard
- [ ] Mobile offline mode enhancement
- [ ] Multi-language support
- [ ] Integration with SCADA systems
- [ ] Blockchain audit trail
- [ ] AI-powered incident prediction

---

**Built with â¤ï¸ for National Water Infrastructure**

