# Railway Deployment Guide

## 🚀 Quick Setup

### Step 1: Add Environment Variables to Railway

1. Go to your Railway project: https://railway.app
2. Click on your **Water-Infrastructure-System** service
3. Click on the **Variables** tab
4. Click **+ New Variable** and add each of these:

```
DATABASE_URL=mysql+pymysql://root:nYiLHEQsRMUsmXTUowmrlvNSJcutDxYg@interchange.proxy.rlwy.net:20906/railway

REDIS_URL=redis://default:VatkHEDGSLJbgKZlgTiVamRJggKcFqOy@switchyard.proxy.rlwy.net:10457

S3_ENDPOINT=https://t3.storageapi.dev

S3_BUCKET=recorded-wrap-krk8vsj4wzi

S3_ACCESS_KEY=tid_WKMBXeNExOmrEzIKww_gnbNlOuwwHhgggpTBpaEonVRDWVExNu

S3_SECRET_KEY=tsec_IIbuZ_nXbwG4Ij84tM_UNen4Cvd1cGzzKQ2kbSyosGpQkMIszQA8Hv2X010cd7EFpMkyz1

SECRET_KEY=nYiLHEQsRMUsmXTUowmrlvNSJcutDxYg-water-monitoring-2024

ENVIRONMENT=production

DATABASE_MODE=mysql
```

### Step 2: Railway Will Auto-Redeploy

Once you save the variables, Railway will automatically redeploy your service with the new configuration.

### Step 3: Verify Deployment

Check the logs to confirm:
- ✅ Database connection successful
- ✅ Redis connection successful
- ✅ Application startup complete

---

## 📊 Database Connections

### MySQL (Primary)
```bash
mysql -h interchange.proxy.rlwy.net -u root -p --port 20906 --protocol=TCP railway
Password: nYiLHEQsRMUsmXTUowmrlvNSJcutDxYg
```

### PostgreSQL (Alternative)
```bash
PGPASSWORD=egnQHcmNTcNzmTUBfHcUxewgARJEzhBt psql -h shinkansen.proxy.rlwy.net -U postgres -p 29535 -d railway
```

### Redis
```bash
redis-cli -u redis://default:VatkHEDGSLJbgKZlgTiVamRJggKcFqOy@switchyard.proxy.rlwy.net:10457
```

---

## 🔗 API Endpoints

Once deployed, your API will be available at:
- **Base URL**: `https://your-service.up.railway.app`
- **API Docs**: `https://your-service.up.railway.app/docs`
- **Health Check**: `https://your-service.up.railway.app/health`
- **Metrics**: `https://your-service.up.railway.app/metrics`

---

## 🎯 Next Steps

1. **Initialize Database**: The app will auto-create tables on first startup
2. **Create Super Admin**: Use the API to create your first admin user
3. **Configure Frontend**: Update frontend API URL to point to Railway deployment
4. **Test Endpoints**: Visit `/docs` to test API endpoints

---

## 🔧 Troubleshooting

### If deployment fails:
1. Check Railway logs for errors
2. Verify all environment variables are set correctly
3. Ensure database is accessible from Railway

### If database connection fails:
- Verify DATABASE_URL format: `mysql+pymysql://user:pass@host:port/database`
- Check Railway MySQL service is running
- Verify credentials are correct

---

## 📝 Important Notes

- The app is configured to start even if database/Redis are temporarily unavailable
- MQTT broker is optional (will use fallback if not configured)
- S3 storage is optional (for file uploads and backups)
- All credentials are production-ready from Railway services

---

**Status**: ✅ Application is running and ready for environment variable configuration!
