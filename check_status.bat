@echo off
title System Status Check

echo ========================================
echo  WATER MONITORING SYSTEM STATUS
echo ========================================
echo.

echo [1/7] Checking Python...
python --version 2>nul
if errorlevel 1 (
    echo ❌ Python not found
) else (
    echo ✅ Python installed
)
echo.

echo [2/7] Checking Node.js...
node --version 2>nul
if errorlevel 1 (
    echo ❌ Node.js not found
) else (
    echo ✅ Node.js installed
)
echo.

echo [3/7] Checking Docker...
docker --version 2>nul
if errorlevel 1 (
    echo ❌ Docker not found
) else (
    echo ✅ Docker installed
)
echo.

echo [4/7] Checking Backend API...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend not running
    echo    Start with: cd backend ^&^& uvicorn app.main:app --reload
) else (
    echo ✅ Backend running on port 8000
)
echo.

echo [5/7] Checking MQTT Broker...
netstat -an | findstr ":1883" >nul 2>&1
if errorlevel 1 (
    echo ❌ MQTT broker not running
    echo    Start with: docker-compose up mqtt-broker
) else (
    echo ✅ MQTT broker running on port 1883
)
echo.

echo [6/7] Checking Database...
cd backend
python -c "from app.core.database import engine; engine.connect(); print('✅ Database connected')" 2>nul
if errorlevel 1 (
    echo ❌ Database connection failed
    echo    Check DATABASE_URL in .env
)
cd ..
echo.

echo [7/7] Checking Redis...
if defined REDIS_URL (
    redis-cli -u %REDIS_URL% ping >nul 2>&1
) else (
    redis-cli -h localhost -p 6379 ping >nul 2>&1
)
if errorlevel 1 (
    echo ⚠️  Redis connection check skipped
) else (
    echo ✅ Redis connected
)
echo.

echo ========================================
echo  SYSTEM COMPONENTS STATUS
echo ========================================
echo.
echo Backend API:      http://localhost:8000
echo API Docs:         http://localhost:8000/docs
echo MQTT Broker:      mqtt://localhost:1883
echo WebSocket:        ws://localhost:8000/ws/{municipality_id}
echo.
echo ========================================
echo  QUICK ACTIONS
echo ========================================
echo.
echo Start Backend:    cd backend ^&^& uvicorn app.main:app --reload
echo Start Control:    cd frontend-control-room ^&^& npm run electron-dev
echo Start Mobile:     cd mobile-app ^&^& npm start
echo Start Simulator:  cd iot-gateway ^&^& python sensor_simulator.py
echo.
echo Use launcher.bat for automated startup
echo.
pause
