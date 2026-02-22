@echo off
echo ========================================
echo National Water Monitoring System
echo Starting Control Room Application...
echo ========================================

cd frontend-control-room

echo.
echo Checking Node.js installation...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found!
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
call npm install

echo.
echo Starting Electron application...
echo.

call npm run electron-dev

pause
