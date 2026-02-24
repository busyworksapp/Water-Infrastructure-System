@echo off
echo Fixing Railway deployment...
echo.

cd frontend-web

echo Generating package-lock.json...
if not exist package-lock.json (
    npm install
)

echo.
echo Committing changes...
cd ..
git add frontend-web/package-lock.json
git add frontend-web/Dockerfile
git add frontend-web/nixpacks.toml
git add frontend-web/.dockerignore
git commit -m "Fix: Add package-lock.json for Railway deployment"
git push

echo.
echo ========================================
echo Fixed! Now redeploy on Railway:
echo 1. Go to Railway dashboard
echo 2. Click "Redeploy" on frontend service
echo ========================================
pause
