@echo off
title National Water Infrastructure Monitoring System - Launcher

:menu
cls
echo ========================================
echo  WATER MONITORING SYSTEM LAUNCHER
echo ========================================
echo.
echo  1. Start Backend API
echo  2. Start Control Room Desktop App
echo  3. Start Mobile App (Expo)
echo  4. Start Sensor Simulator
echo  5. Start All Services (Docker)
echo  6. Initialize Database
echo  7. View System Status
echo  8. Exit
echo.
echo ========================================
set /p choice="Select option (1-8): "

if "%choice%"=="1" goto backend
if "%choice%"=="2" goto controlroom
if "%choice%"=="3" goto mobile
if "%choice%"=="4" goto simulator
if "%choice%"=="5" goto docker
if "%choice%"=="6" goto initdb
if "%choice%"=="7" goto status
if "%choice%"=="8" goto end

echo Invalid choice!
timeout /t 2
goto menu

:backend
cls
echo Starting Backend API...
cd backend
start cmd /k "python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && uvicorn app.main:app --reload"
echo Backend started in new window
timeout /t 3
goto menu

:controlroom
cls
echo Starting Control Room...
cd frontend-control-room
start cmd /k "npm install && npm run electron-dev"
echo Control Room started in new window
timeout /t 3
goto menu

:mobile
cls
echo Starting Mobile App...
cd mobile-app
start cmd /k "npm install && npm start"
echo Mobile App started in new window
timeout /t 3
goto menu

:simulator
cls
echo Starting Sensor Simulator...
cd iot-gateway
start cmd /k "python sensor_simulator.py"
echo Simulator started in new window
timeout /t 3
goto menu

:docker
cls
echo Starting Docker Services...
docker-compose up -d
echo.
echo Services started:
docker-compose ps
echo.
pause
goto menu

:initdb
cls
echo Initializing Database...
cd backend
python scripts\init_db.py
echo.
echo Database initialized!
echo Default credentials:
echo   Username: admin
echo   Password: admin123
echo.
pause
goto menu

:status
cls
echo ========================================
echo  SYSTEM STATUS
echo ========================================
echo.
echo Checking Backend API...
curl -s http://localhost:8000/health
echo.
echo.
echo Checking Docker Services...
docker-compose ps
echo.
pause
goto menu

:end
echo.
echo Exiting...
exit
