@echo off
echo ========================================
echo Railway Deployment Script for RandWater
echo ========================================
echo.

echo Checking Railway CLI...
where railway >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing Railway CLI...
    npm install -g @railway/cli
)

echo.
echo Logging into Railway...
railway login

echo.
echo ========================================
echo BACKEND DEPLOYMENT
echo ========================================
cd backend

echo Creating Railway project...
railway init

echo.
echo Setting environment variables...
echo Please enter your credentials:
echo.

set /p DATABASE_URL="DATABASE_URL: "
set /p REDIS_URL="REDIS_URL: "
set /p SECRET_KEY="SECRET_KEY (leave empty to generate): "

railway variables set DATABASE_URL="%DATABASE_URL%"
railway variables set REDIS_URL="%REDIS_URL%"
railway variables set SECRET_KEY="%SECRET_KEY%"
railway variables set ENVIRONMENT="production"
railway variables set PORT="8000"

echo.
echo Deploying backend...
railway up

echo.
echo Initializing database...
railway run python scripts/init_db.py

echo.
echo ========================================
echo FRONTEND DEPLOYMENT
echo ========================================
cd ..\frontend-web

echo.
echo Enter your backend URL from Railway:
set /p BACKEND_URL="Backend URL (e.g., randwater-backend.up.railway.app): "

railway init

railway variables set VITE_API_URL="https://%BACKEND_URL%/api/v1"
railway variables set VITE_WS_URL="wss://%BACKEND_URL%"

echo.
echo Deploying frontend...
railway up

echo.
echo ========================================
echo DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Check Railway dashboard for your URLs
echo Default login: admin / admin123
echo.
echo IMPORTANT: Change admin password immediately!
echo.
pause
