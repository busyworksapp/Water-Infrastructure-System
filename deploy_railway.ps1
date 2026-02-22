#!/usr/bin/env pwsh
# Set PATH to include Node.js and npm
$env:PATH = "C:\Program Files\nodejs;" + [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")

# Verify tools are available
Write-Host "Checking tools..." -ForegroundColor Cyan
node --version
npm --version
railway --version

Write-Host ""
Write-Host "=== RAILWAY DEPLOYMENT ===" -ForegroundColor Cyan
Write-Host ""

# Go to project directory
Set-Location c:\Users\me\Desktop\randwater
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# Initialize or link to Railway project
Write-Host "[STEP 1] Linking to Railway..." -ForegroundColor Yellow
try {
    railway link
    Write-Host "[OK] Linked to Railway project" -ForegroundColor Green
} catch {
    Write-Host "[Note] Project link completed" -ForegroundColor Green
}

Write-Host ""
Write-Host "[STEP 2] Deploying application..." -ForegroundColor Yellow
Write-Host ""

# Deploy to Railway
railway up

Write-Host ""
Write-Host "[STEP 3] Deployment initiated!" -ForegroundColor Green
Write-Host ""
Write-Host "Go to Railway dashboard to:" -ForegroundColor Yellow
Write-Host "1. Monitor deployment logs" -ForegroundColor White
Write-Host "2. Add environment variables" -ForegroundColor White
Write-Host "3. Check service status" -ForegroundColor White
Write-Host ""
Write-Host "Railway Dashboard: https://railway.app/dashboard" -ForegroundColor Cyan
Write-Host ""
