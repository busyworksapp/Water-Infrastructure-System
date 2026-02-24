@echo off
echo ========================================
echo RandWater Web Application Launcher
echo ========================================
echo.

echo Starting Backend...
start cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload"

timeout /t 5 /nobreak >nul

echo Starting Web Frontend...
start cmd /k "cd frontend-web && npm run dev"

echo.
echo ========================================
echo Services Starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Press any key to exit...
pause >nul
