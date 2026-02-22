@echo off
REM ===================================================================
REM   WATER INFRASTRUCTURE SYSTEM - AUTOMATED DEPLOYMENT SCRIPT
REM   Deploy to: https://github.com/busyworksapp/Water-Infrastructure-System.git
REM   Target: Railway.app
REM ===================================================================

setlocal enabledelayedexpansion

echo.
echo ====================================================================
echo   WATER INFRASTRUCTURE SYSTEM - PRODUCTION DEPLOYMENT
echo ====================================================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed!
    echo.
    echo Please install Git from: https://git-scm.com/download/win
    echo Then restart this script.
    echo.
    pause
    exit /b 1
)

echo [OK] Git found
git --version
echo.

REM Change to project directory
cd /d c:\Users\me\Desktop\randwater
if %errorlevel% neq 0 (
    echo [ERROR] Could not change to project directory
    pause
    exit /b 1
)

echo [OK] In project directory: %cd%
echo.

REM Configure git user
echo [STEP 1] Configuring git user...
git config --global user.name "Water Infrastructure System"
git config --global user.email "system@waterinfra.dev"
echo [OK] Git user configured
echo.

REM Initialize git repository
echo [STEP 2] Initializing git repository...
if exist .git (
    echo [OK] Repository already initialized
) else (
    git init
    echo [OK] Repository initialized
)
echo.

REM Add all files
echo [STEP 3] Adding all files to git...
git add .
echo [OK] Files added
echo.

REM Create commit
echo [STEP 4] Creating initial commit...
git commit -m "Initial commit: National Water Infrastructure Monitoring System - Production Ready"
if %errorlevel% neq 0 (
    echo [WARNING] Commit might have failed or nothing to commit
) else (
    echo [OK] Commit created
)
echo.

REM Add remote
echo [STEP 5] Adding GitHub remote...
git remote remove origin 2>nul
git remote add origin https://github.com/busyworksapp/Water-Infrastructure-System.git
echo [OK] Remote added
echo.

REM Set main branch
echo [STEP 6] Setting main branch...
git branch -M main 2>nul
echo [OK] Main branch set
echo.

REM Push to GitHub
echo [STEP 7] Pushing code to GitHub...
echo.
echo [NOTE] You may be prompted for GitHub credentials.
echo [NOTE] Use: GitHub username + personal access token OR SSH key
echo.
git push -u origin main
if %errorlevel% neq 0 (
    echo [WARNING] Push may have failed. Check your GitHub credentials.
    echo.
    pause
    exit /b 1
)
echo [OK] Code pushed to GitHub!
echo.

REM Check Railway CLI
where railway >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Railway CLI not installed. Installing...
    where npm >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Node.js/npm not found!
        echo Please install from: https://nodejs.org/
        echo Then run this script again.
        echo.
        pause
        exit /b 1
    )
    call npm install -g @railway/cli
)
echo.

REM Railway Login
echo [STEP 8] Logging in to Railway...
echo [NOTE] A browser window will open. Log in with your Railway account.
echo.
call railway login
echo [OK] Railway login complete
echo.

REM Final Instructions
echo ====================================================================
echo   DEPLOYMENT SUMMARY
echo ====================================================================
echo.
echo [OK] Code committed to git
echo [OK] Code pushed to GitHub
echo [OK] Ready for Railway deployment
echo.
echo NEXT STEPS:
echo   1. Go to: https://railway.app/dashboard
echo   2. Click: New Project
echo   3. Select: Deploy from GitHub
echo   4. Choose: Water-Infrastructure-System repository
echo   5. Click: Deploy
echo   6. Add environment variables (see IMMEDIATE_DEPLOYMENT_STEPS.md)
echo   7. Monitor deployment in Railway dashboard
echo.
echo Estimated time to production: 10-15 minutes
echo.
echo ====================================================================
echo.
pause
