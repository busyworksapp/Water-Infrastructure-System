#!/usr/bin/env pwsh
# ===================================================================
#   WATER INFRASTRUCTURE SYSTEM - AUTOMATED DEPLOYMENT SCRIPT
#   Deploy to: https://github.com/busyworksapp/Water-Infrastructure-System.git
#   Target: Railway.app
# ===================================================================

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  WATER INFRASTRUCTURE SYSTEM - PRODUCTION DEPLOYMENT" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-CommandExists {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Check if git is installed
if (-not (Test-CommandExists git)) {
    Write-Host "[ERROR] Git is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Then restart this script." -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host "[OK] Git found" -ForegroundColor Green
git --version
Write-Host ""

# Change to project directory
Set-Location c:\Users\me\Desktop\randwater -ErrorAction Stop
Write-Host "[OK] In project directory: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# Step 1: Configure git user
Write-Host "[STEP 1] Configuring git user..." -ForegroundColor Cyan
git config --global user.name "Water Infrastructure System"
git config --global user.email "system@waterinfra.dev"
Write-Host "[OK] Git user configured" -ForegroundColor Green
Write-Host ""

# Step 2: Initialize git repository
Write-Host "[STEP 2] Initializing git repository..." -ForegroundColor Cyan
if (Test-Path .git) {
    Write-Host "[OK] Repository already initialized" -ForegroundColor Green
} else {
    git init
    Write-Host "[OK] Repository initialized" -ForegroundColor Green
}
Write-Host ""

# Step 3: Add all files
Write-Host "[STEP 3] Adding all files to git..." -ForegroundColor Cyan
git add .
Write-Host "[OK] Files added" -ForegroundColor Green
Write-Host ""

# Step 4: Create commit
Write-Host "[STEP 4] Creating initial commit..." -ForegroundColor Cyan
git commit -m "Initial commit: National Water Infrastructure Monitoring System - Production Ready"
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Commit created" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Commit may have failed or nothing to commit" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Add remote
Write-Host "[STEP 5] Adding GitHub remote..." -ForegroundColor Cyan
git remote remove origin 2>$null
git remote add origin https://github.com/busyworksapp/Water-Infrastructure-System.git
Write-Host "[OK] Remote added" -ForegroundColor Green
Write-Host ""

# Step 6: Set main branch
Write-Host "[STEP 6] Setting main branch..." -ForegroundColor Cyan
git branch -M main 2>$null
Write-Host "[OK] Main branch set" -ForegroundColor Green
Write-Host ""

# Step 7: Push to GitHub
Write-Host "[STEP 7] Pushing code to GitHub..." -ForegroundColor Cyan
Write-Host ""
Write-Host "[NOTE] You may be prompted for GitHub credentials." -ForegroundColor Yellow
Write-Host "[NOTE] Use: GitHub username + personal access token OR SSH key" -ForegroundColor Yellow
Write-Host ""
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Push may have failed. Check your GitHub credentials." -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}
Write-Host "[OK] Code pushed to GitHub!" -ForegroundColor Green
Write-Host ""

# Step 8: Check Railway CLI
if (-not (Test-CommandExists railway)) {
    Write-Host "[INFO] Railway CLI not installed. Installing..." -ForegroundColor Yellow
    if (-not (Test-CommandExists npm)) {
        Write-Host "[ERROR] Node.js/npm not found!" -ForegroundColor Red
        Write-Host "Please install from: https://nodejs.org/" -ForegroundColor Yellow
        Write-Host "Then run this script again." -ForegroundColor Yellow
        Write-Host ""
        pause
        exit 1
    }
    npm install -g @railway/cli
}
Write-Host ""

# Step 8: Railway Login
Write-Host "[STEP 8] Logging in to Railway..." -ForegroundColor Cyan
Write-Host "[NOTE] A browser window will open. Log in with your Railway account." -ForegroundColor Yellow
Write-Host ""
railway login
Write-Host "[OK] Railway login complete" -ForegroundColor Green
Write-Host ""

# Final Summary
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  DEPLOYMENT SUMMARY" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[OK] Code committed to git" -ForegroundColor Green
Write-Host "[OK] Code pushed to GitHub" -ForegroundColor Green
Write-Host "[OK] Ready for Railway deployment" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. Go to: https://railway.app/dashboard" -ForegroundColor White
Write-Host "  2. Click: New Project" -ForegroundColor White
Write-Host "  3. Select: Deploy from GitHub" -ForegroundColor White
Write-Host "  4. Choose: Water-Infrastructure-System repository" -ForegroundColor White
Write-Host "  5. Click: Deploy" -ForegroundColor White
Write-Host "  6. Add environment variables (see IMMEDIATE_DEPLOYMENT_STEPS.md)" -ForegroundColor White
Write-Host "  7. Monitor deployment in Railway dashboard" -ForegroundColor White
Write-Host ""
Write-Host "Estimated time to production: 10-15 minutes" -ForegroundColor Cyan
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
pause
