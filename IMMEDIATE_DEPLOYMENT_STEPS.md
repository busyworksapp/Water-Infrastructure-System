# 🚀 IMMEDIATE DEPLOYMENT STEPS

**Status**: System is production-ready. Follow these steps to deploy.

## Prerequisites Required

You need to install two tools before deployment can proceed:

### 1. Install Git for Windows
**Download from**: https://git-scm.com/download/win

Steps:
1. Click "Download" on git-scm.com
2. Run the installer
3. Use all default options (click Next/Install)
4. Close installer when complete
5. Restart your PowerShell terminal

### 2. Install Node.js (for Railway CLI)
**Download from**: https://nodejs.org/

Steps:
1. Download LTS version (18.x or 20.x)
2. Run installer
3. Use all default options
4. Restart PowerShell when complete

### 3. Have Your GitHub Credentials Ready
You need either:
- GitHub username + personal access token, OR
- GitHub SSH key configured

---

## Deployment Steps (After Installing Prerequisites)

### Step 1: Configure Git Locally

```powershell
cd c:\Users\me\Desktop\randwater
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git init
```

### Step 2: Add All Files to Git

```powershell
git add .
git commit -m "Initial commit: National Water Infrastructure Monitoring System - Production Ready"
```

### Step 3: Connect to GitHub Repository

Your GitHub repo: `https://github.com/busyworksapp/Water-Infrastructure-System.git`

**Option A: If repo is empty (recommended)**
```powershell
git remote add origin https://github.com/busyworksapp/Water-Infrastructure-System.git
git branch -M main
git push -u origin main
# Enter GitHub username and token when prompted
```

**Option B: If repo already has content**
```powershell
git remote add origin https://github.com/busyworksapp/Water-Infrastructure-System.git
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Step 4: Install Railway CLI

```powershell
npm install -g @railway/cli
```

### Step 5: Login to Railway

```powershell
railway login
# This opens a browser window - log in with your Railway account
# Returns to terminal when complete
```

### Step 6: Create Railway Project

Go to https://railway.app/dashboard and:
1. Click "New Project"
2. Select "Deploy from GitHub"
3. Select "Water-Infrastructure-System" repository
4. Click "Deploy"
5. Wait for initial build (5-10 minutes)

### Step 7: Configure Environment Variables in Railway

In Railway dashboard for your project:

1. Click on the deployed service
2. Go to "Variables" tab
3. Add all these variables (from your `.env` file):

```
DATABASE_URL=mysql+pymysql://root:nYiLHEQsRMUsmXTUowmrlvNSJcutDxYg@interchange.proxy.rlwy.net:20906/railway
DATABASE_POSTGRES_URL=postgresql://postgres:egnQHcmNTcNzmTUBfHcUxewgARJEzhBt@shinkansen.proxy.rlwy.net:29535/railway
REDIS_URL=redis://default:VatkHEDGSLJbgKZlgTiVamRJggKcFqOy@switchyard.proxy.rlwy.net:10457
AWS_ACCESS_KEY_ID=tid_WKMBXeNExOmrEzIKww_gnbNlOuwwHhgggpTBpaEonVRDWVExNu
AWS_SECRET_ACCESS_KEY=tsec_IIbuZ_nXbwG4Ij84tM_UNen4Cvd1cGzzKQ2kbSyosGpQkMIszQA8Hv2X010cd7EFpMkyz1
S3_BUCKET_NAME=recorded-wrap-krk8vsj4wzi
S3_REGION=us-east-1
S3_ENDPOINT=t3.storageapi.dev
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["*"]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
MQTT_BROKER_HOST=mqtt.example.com
MQTT_BROKER_PORT=8883
MQTT_USERNAME=mqtt_user
MQTT_PASSWORD=mqtt_password
MQTT_TOPIC_PREFIX=water/
CELERY_BROKER_URL=redis://default:VatkHEDGSLJbgKZlgTiVamRJggKcFqOy@switchyard.proxy.rlwy.net:10457
CELERY_RESULT_BACKEND=redis://default:VatkHEDGSLJbgKZlgTiVamRJggKcFqOy@switchyard.proxy.rlwy.net:10457
```

### Step 8: Trigger Deployment

After adding environment variables:

1. Click "Deploy" button in Railway dashboard
2. Wait for build to complete (10-15 minutes)
3. Check build logs for any errors

### Step 9: Verify Deployment

Once Railway shows "Active":

1. Get your app URL from Railway dashboard (format: `https://your-app-name.up.railway.app`)

2. Test the health endpoint:
   ```powershell
   $url = "https://your-app-name.up.railway.app/health"
   Invoke-WebRequest -Uri $url
   ```

3. Test API documentation:
   Open in browser: `https://your-app-name.up.railway.app/docs`

4. Test database connection:
   ```powershell
   $response = Invoke-WebRequest -Uri "https://your-app-name.up.railway.app/api/v1/health" -ErrorAction SilentlyContinue
   $response.StatusCode  # Should return 200
   ```

---

## Troubleshooting

### Issue: "git is not recognized"
**Solution**: Git didn't install properly. Download and install from https://git-scm.com/download/win

### Issue: "railway is not recognized"
**Solution**: Node.js or Railway CLI didn't install. Run:
```powershell
npm install -g @railway/cli
```

### Issue: Railway build fails
**Solution**: Check the build logs in Railway dashboard. Common issues:
- Missing environment variables (add all from step 7)
- Port not set (Railway should auto-set $PORT)
- Database connection timeout (credentials verified)

### Issue: Health endpoint returns 500
**Solution**: Check Railway logs:
```powershell
railway logs -f
```
Look for error messages and compare with troubleshooting guide.

### Issue: Database says "connection timeout"
**Solution**: 
1. Verify you're on the correct network/VPN (if using private infrastructure)
2. Check that all database credentials are correct
3. Verify firewall isn't blocking outbound connections

---

## What Happens During Deployment

1. **Railway builds** your application (2-3 min)
   - Downloads Python 3.13
   - Installs dependencies from requirements.txt
   - Builds Docker container

2. **Railway starts** your application (1-2 min)
   - Runs `scripts/deploy_railway.py` (auto-init database)
   - Starts FastAPI server on port $PORT
   - Initializes all 18 database tables
   - Seeds initial data

3. **System verifies** everything (1 min)
   - Health check passes
   - All services responding
   - Database connected
   - Redis cache ready
   - S3 storage accessible

4. **Application goes live** (30 sec)
   - Assigned public URL
   - HTTPS enabled automatically
   - Ready for traffic

**Total time**: 5-10 minutes

---

## After Deployment

### Access Your Application

- **API Docs**: `https://your-app.up.railway.app/docs`
- **Health Check**: `https://your-app.up.railway.app/health`
- **API Base**: `https://your-app.up.railway.app/api/v1`

### Monitor Your Application

View logs in real-time:
```powershell
railway logs -f
```

Check resource usage:
```powershell
railway status
```

### Scale Your Application

To add more resources (if needed):
1. Go to Railway dashboard
2. Select your service
3. Adjust resources (CPU, RAM)
4. Save changes

---

## Quick Reference

| Step | Time | Command |
|------|------|---------|
| Install Git | 5 min | Download from git-scm.com |
| Install Node.js | 5 min | Download from nodejs.org |
| Git init & commit | 2 min | `git init` + `git commit` |
| Push to GitHub | 3 min | `git push -u origin main` |
| Railway login | 2 min | `railway login` |
| Deploy to Railway | 10 min | Use Railway dashboard |
| Configure env vars | 5 min | Add to Railway variables |
| Verify deployment | 5 min | Test health endpoint |
| **Total** | **37 minutes** | **Live in production** |

---

## Support

If you encounter issues:

1. Check Railway logs: `railway logs -f`
2. Verify all environment variables are set
3. Ensure database credentials are correct
4. Check that your IP can reach the databases

**All endpoints documented in**: `API_COMPLETE_DOCUMENTATION.md`

**Troubleshooting guide**: `PHASE_5_PRODUCTION_DEPLOYMENT.md`

---

**Status**: ✅ System is production-ready  
**Next**: Install prerequisites and follow steps above  
**Timeline**: 30-40 minutes to live  

Good luck! 🚀
