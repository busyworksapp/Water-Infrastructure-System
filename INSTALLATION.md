# Installation & Testing Guide

## ðŸš€ Quick Start (Windows)

### Option 1: Automated Launcher (Recommended)
```cmd
# Double-click launcher.bat
# Or run from command line:
launcher.bat
```

The launcher provides:
1. Start Backend API
2. Start Control Room Desktop App
3. Start Mobile App
4. Start Sensor Simulator
5. Start Docker Services
6. Initialize Database
7. View System Status

---

## ðŸ“‹ Prerequisites

### Required Software
- **Python 3.12+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Docker Desktop** (optional) - [Download](https://www.docker.com/products/docker-desktop/)

### Verify Installation
```cmd
python --version
node --version
npm --version
docker --version
```

---

## ðŸ”§ Manual Installation

### Step 1: Backend Setup

```cmd
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts\init_db.py

# Start server
uvicorn app.main:app --reload
```

**Backend will be available at:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Step 2: Control Room Setup

```cmd
cd frontend-control-room

# Install dependencies
npm install

# Start development
npm run electron-dev

# Or build for production
npm run electron-build
```

### Step 3: Mobile App Setup

```cmd
cd mobile-app

# Install dependencies
npm install

# Start Expo
npm start

# Run on Android
npm run android

# Run on iOS (Mac only)
npm run ios
```

### Step 4: Sensor Simulator

```cmd
cd iot-gateway

# Run simulator
python sensor_simulator.py
```

---

## ðŸ³ Docker Installation

### Start All Services
```cmd
docker-compose up -d
```

### Services Included
- Backend API (port 8000)
- MQTT Broker (port 1883)
- Celery Worker
- Celery Beat

### View Logs
```cmd
docker-compose logs -f backend
```

### Stop Services
```cmd
docker-compose down
```

---

## ðŸ§ª Testing the System

### 1. Test Backend API

```cmd
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

### 2. Test Control Room

1. Launch application
2. Login with: `admin` / `admin123`
3. Verify dashboard loads
4. Check real-time updates

### 3. Test Sensor Simulator

1. Start simulator: `python sensor_simulator.py`
2. Observe MQTT messages
3. Check dashboard for live readings
4. Verify anomaly detection

### 4. Test Mobile App

1. Start Expo: `npm start`
2. Scan QR code with Expo Go app
3. Login with credentials
4. Navigate through screens

---

## ðŸ” Default Credentials

### Super Administrator
```
Username: admin
Password: admin123
```

### Municipality Administrator
```
Username: jhb_admin
Password: jhb123
Municipality: City of Johannesburg
```

---

## ðŸ“Š Database Configuration

### Provided MySQL Database
```
Host: interchange.proxy.rlwy.net
Port: 20906
User: root
Password: <MYSQL_PASSWORD>
Database: railway
```

### Provided Redis
```
URL: redis://default:<REDIS_PASSWORD>@switchyard.proxy.rlwy.net:10457
```

### Initialize Database
```cmd
cd backend
python scripts\init_db.py
```

This creates:
- All tables
- Default roles and permissions
- Sample municipality
- Admin users
- Sensor types
- System settings

---

## ðŸ§© Component Testing

### Backend API Endpoints

```bash
# Get sensors
curl http://localhost:8000/api/v1/sensors \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get alerts
curl http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get pipelines
curl http://localhost:8000/api/v1/pipelines \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### WebSocket Connection

```javascript
const socket = io('ws://localhost:8000/ws/MUNICIPALITY_ID');

socket.on('sensor_reading', (data) => {
  console.log('New reading:', data);
});

socket.on('alert', (data) => {
  console.log('New alert:', data);
});
```

### MQTT Testing

```bash
# Subscribe to all sensor topics
mosquitto_sub -h localhost -p 1883 -t "sensors/#" -v

# Publish test message
mosquitto_pub -h localhost -p 1883 \
  -t "sensors/TEST_001/data" \
  -m '{"device_id":"TEST_001","value":3.5,"unit":"bar"}'
```

---

## ðŸ” Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```cmd
# Find process
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F
```

**Database connection failed:**
- Check DATABASE_URL in .env
- Verify network connectivity
- Check credentials

**Module not found:**
```cmd
pip install -r requirements.txt
```

### Frontend Issues

**npm install fails:**
```cmd
# Clear cache
npm cache clean --force

# Delete node_modules
rmdir /s /q node_modules

# Reinstall
npm install
```

**Electron won't start:**
```cmd
# Rebuild electron
npm rebuild electron
```

### Docker Issues

**Services won't start:**
```cmd
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Rebuild
docker-compose up -d --build
```

---

## ðŸ“ˆ Performance Testing

### Load Testing Backend

```bash
# Install Apache Bench
# Test API endpoint
ab -n 1000 -c 10 http://localhost:8000/health
```

### Sensor Throughput

```python
# Modify sensor_simulator.py
# Increase sensor count
# Reduce sleep interval
```

---

## ðŸ”’ Security Checklist

Before production deployment:

- [ ] Change SECRET_KEY in .env
- [ ] Update default passwords
- [ ] Configure TLS/SSL
- [ ] Set up firewall rules
- [ ] Enable MQTT authentication
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Configure backup strategy
- [ ] Test disaster recovery

---

## ðŸ“± Mobile App Testing

### iOS (Mac only)
```cmd
cd mobile-app
npm run ios
```

### Android
```cmd
cd mobile-app
npm run android
```

### Expo Go
1. Install Expo Go on phone
2. Run `npm start`
3. Scan QR code
4. Test on device

---

## ðŸŽ¯ Verification Checklist

### Backend
- [ ] API responds at http://localhost:8000
- [ ] Swagger docs accessible at /docs
- [ ] Health check returns 200
- [ ] Login endpoint works
- [ ] Database tables created
- [ ] MQTT client connects

### Control Room
- [ ] Application launches
- [ ] Login screen appears
- [ ] Dashboard loads after login
- [ ] Real-time updates work
- [ ] Map view displays
- [ ] Alerts panel functional

### Mobile App
- [ ] App builds successfully
- [ ] Login works
- [ ] Dashboard displays stats
- [ ] Alerts screen loads
- [ ] Map view shows markers
- [ ] Incident report submits

### IoT Integration
- [ ] Sensor simulator connects
- [ ] MQTT messages received
- [ ] Readings stored in database
- [ ] Anomalies detected
- [ ] Alerts generated
- [ ] WebSocket broadcasts work

---

## ðŸ“ž Support Resources

### Documentation
- Main README: `/README.md`
- API Docs: `/docs/API.md`
- Architecture: `/docs/ARCHITECTURE.md`
- Deployment: `/docs/DEPLOYMENT.md`

### Online Resources
- FastAPI Docs: https://fastapi.tiangolo.com
- React Docs: https://react.dev
- Electron Docs: https://electronjs.org
- React Native Docs: https://reactnative.dev

---

## ðŸŽ“ Next Steps

1. **Explore the System**
   - Login to control room
   - Start sensor simulator
   - Watch real-time updates
   - Create test alerts

2. **Customize Configuration**
   - Add new sensor types
   - Configure alert rules
   - Set up municipalities
   - Create user accounts

3. **Deploy to Production**
   - Follow DEPLOYMENT.md
   - Configure production settings
   - Set up monitoring
   - Enable backups

4. **Integrate Real Sensors**
   - Configure MQTT credentials
   - Register devices
   - Set up authentication
   - Test connectivity

---

## âœ… Installation Complete!

Your National Water Infrastructure Monitoring System is ready to use.

**Quick Test:**
1. Run `launcher.bat`
2. Select option 6 (Initialize Database)
3. Select option 1 (Start Backend)
4. Select option 2 (Start Control Room)
5. Select option 4 (Start Simulator)
6. Login and monitor!

---

**For issues or questions, refer to the comprehensive documentation in the `/docs` folder.**

