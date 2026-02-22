@echo off
REM National Water Infrastructure Monitoring System
REM Quick Start and Verification Script
REM Version 2.0.0

echo ========================================
echo National Water Infrastructure System
echo Quick Start Script
echo ========================================
echo.

REM Check if Docker is running
echo [1/8] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running
    echo Please install Docker Desktop and try again
    pause
    exit /b 1
)
echo OK: Docker is installed

REM Check if Docker Compose is available
echo [2/8] Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not available
    pause
    exit /b 1
)
echo OK: Docker Compose is available

REM Check if .env file exists
echo [3/8] Checking environment configuration...
if not exist "backend\.env" (
    echo WARNING: backend\.env not found
    echo Copying from .env.production.template...
    copy .env.production.template backend\.env
)
echo OK: Environment file exists

REM Stop any running containers
echo [4/8] Stopping existing containers...
docker-compose down >nul 2>&1
echo OK: Containers stopped

REM Start services
echo [5/8] Starting services...
echo This may take a few minutes on first run...
docker-compose up -d
if errorlevel 1 (
    echo ERROR: Failed to start services
    echo Check docker-compose logs for details
    pause
    exit /b 1
)
echo OK: Services started

REM Wait for services to be ready
echo [6/8] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check backend health
echo [7/8] Checking backend health...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo WARNING: Backend not responding yet
    echo Waiting additional 10 seconds...
    timeout /t 10 /nobreak >nul
    curl -s http://localhost:8000/health >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Backend failed to start
        echo Check logs: docker-compose logs backend
        pause
        exit /b 1
    )
)
echo OK: Backend is healthy

REM Display service status
echo [8/8] Checking service status...
docker-compose ps

echo.
echo ========================================
echo System Started Successfully!
echo ========================================
echo.
echo Services:
echo   Backend API:     http://localhost:8000
echo   API Docs:        http://localhost:8000/docs
echo   MQTT Broker:     localhost:1883
echo   Redis:           localhost:6379
echo   Metrics:         http://localhost:8000/metrics
echo.
echo Next Steps:
echo   1. Initialize database: run_init_db.bat
echo   2. Start Control Room: start_control_room.bat
echo   3. View logs: docker-compose logs -f
echo   4. Stop system: docker-compose down
echo.
echo ========================================

REM Ask if user wants to initialize database
echo.
set /p INIT_DB="Initialize database now? (y/n): "
if /i "%INIT_DB%"=="y" (
    echo.
    echo Initializing database...
    call run_init_db.bat
)

REM Ask if user wants to open API docs
echo.
set /p OPEN_DOCS="Open API documentation in browser? (y/n): "
if /i "%OPEN_DOCS%"=="y" (
    start http://localhost:8000/docs
)

echo.
echo Press any key to exit...
pause >nul
