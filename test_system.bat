@echo off
title Water Monitoring System - Test Suite

echo ========================================
echo  WATER MONITORING SYSTEM TEST SUITE
echo ========================================
echo.

:menu
echo  1. Test Backend API
echo  2. Test Database Connection
echo  3. Test MQTT Connection
echo  4. Test WebSocket
echo  5. Run All Tests
echo  6. Load Test
echo  7. Back to Main Menu
echo.
set /p choice="Select test (1-7): "

if "%choice%"=="1" goto test_api
if "%choice%"=="2" goto test_db
if "%choice%"=="3" goto test_mqtt
if "%choice%"=="4" goto test_ws
if "%choice%"=="5" goto test_all
if "%choice%"=="6" goto load_test
if "%choice%"=="7" goto end

:test_api
cls
echo Testing Backend API...
echo.
echo 1. Health Check:
curl -s http://localhost:8000/health
echo.
echo.
echo 2. Root Endpoint:
curl -s http://localhost:8000/
echo.
echo.
echo 3. API Documentation:
echo Visit: http://localhost:8000/docs
echo.
pause
goto menu

:test_db
cls
echo Testing Database Connection...
cd backend
python -c "from app.core.database import engine; print('✅ Database connected!' if engine.connect() else '❌ Connection failed')"
cd ..
echo.
pause
goto menu

:test_mqtt
cls
echo Testing MQTT Connection...
echo Subscribing to sensor topics...
timeout /t 2
mosquitto_sub -h localhost -p 1883 -t "sensors/#" -v -C 5
echo.
pause
goto menu

:test_ws
cls
echo Testing WebSocket...
echo WebSocket endpoint: ws://localhost:8000/ws/{municipality_id}
echo Use browser console or wscat to test
echo.
pause
goto menu

:test_all
cls
echo Running All Tests...
echo.
echo === Backend Tests ===
cd backend
pytest tests/ -v
cd ..
echo.
echo === API Tests ===
curl -s http://localhost:8000/health
echo.
echo.
echo === Database Test ===
cd backend
python -c "from app.core.database import engine; engine.connect()"
cd ..
echo.
echo All tests completed!
pause
goto menu

:load_test
cls
echo Load Testing Backend...
echo.
echo Running 1000 requests with 10 concurrent connections...
ab -n 1000 -c 10 http://localhost:8000/health
echo.
pause
goto menu

:end
echo.
echo Exiting test suite...
exit
