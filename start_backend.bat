@echo off
echo ========================================
echo National Water Monitoring System
echo Starting Backend Server...
echo ========================================

cd backend

echo.
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Initializing database...
python scripts\init_db.py

echo.
echo Starting FastAPI server...
echo API will be available at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

start cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo ========================================
echo Backend server started!
echo Press any key to exit...
echo ========================================
pause
