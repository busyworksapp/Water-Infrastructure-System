# 🚂 Railway Deployment Guide

## Step-by-Step Deployment

### 1. Prerequisites
- GitHub account
- Railway account (sign up at railway.app)
- Push your code to GitHub

### 2. Deploy Backend

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `randwater` repository
5. Click **"Add variables"** and set:

```env
DATABASE_URL=mysql+pymysql://root:<password>@interchange.proxy.rlwy.net:20906/railway
REDIS_URL=redis://default:<password>@switchyard.proxy.rlwy.net:10457
SECRET_KEY=your-super-secret-key-change-this
S3_ENDPOINT=https://t3.storageapi.dev
S3_BUCKET=recorded-wrap-krk8vsj4wzi
S3_ACCESS_KEY=<your-s3-key>
S3_SECRET_KEY=<your-s3-secret>
ENVIRONMENT=production
PORT=8000
```

6. Set **Root Directory** to `backend`
7. Click **"Deploy"**
8. Wait for deployment (2-3 minutes)
9. Copy the generated URL (e.g., `https://randwater-backend.up.railway.app`)

### 3. Initialize Database

After backend deploys:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run database initialization
railway run python scripts/init_db.py
```

Or use Railway's web terminal:
1. Go to your backend service
2. Click **"Settings"** → **"Deploy"** → **"Run Command"**
3. Enter: `python scripts/init_db.py`

### 4. Deploy Frontend

1. In same Railway project, click **"New Service"**
2. Select **"GitHub Repo"** (same repo)
3. Set **Root Directory** to `frontend-web`
4. Add environment variables:

```env
VITE_API_URL=https://your-backend-url.up.railway.app/api/v1
VITE_WS_URL=wss://your-backend-url.up.railway.app
```

5. Click **"Deploy"**
6. Copy frontend URL (e.g., `https://randwater.up.railway.app`)

### 5. Configure CORS

Update backend environment variables:
```env
CORS_ORIGINS=https://your-frontend-url.up.railway.app
```

Redeploy backend.

### 6. Test Deployment

1. Visit your frontend URL
2. Login with:
   - Username: `admin`
   - Password: `admin123`
3. Verify dashboard loads
4. Check real-time updates work

---

## Quick Deploy (CLI Method)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy backend
cd backend
railway init
railway up
railway variables set DATABASE_URL="mysql+pymysql://..."
railway variables set REDIS_URL="redis://..."
railway variables set SECRET_KEY="your-secret"

# Deploy frontend
cd ../frontend-web
railway init
railway up
railway variables set VITE_API_URL="https://your-backend.railway.app/api/v1"
railway variables set VITE_WS_URL="wss://your-backend.railway.app"
```

---

## Environment Variables Reference

### Backend (Required)
```env
DATABASE_URL=mysql+pymysql://root:<password>@interchange.proxy.rlwy.net:20906/railway
REDIS_URL=redis://default:<password>@switchyard.proxy.rlwy.net:10457
SECRET_KEY=<generate-strong-key>
S3_ENDPOINT=https://t3.storageapi.dev
S3_BUCKET=recorded-wrap-krk8vsj4wzi
S3_ACCESS_KEY=<your-key>
S3_SECRET_KEY=<your-secret>
ENVIRONMENT=production
PORT=8000
```

### Frontend (Required)
```env
VITE_API_URL=https://your-backend.up.railway.app/api/v1
VITE_WS_URL=wss://your-backend.up.railway.app
```

---

## Custom Domain (Optional)

### Backend:
1. Go to backend service → **Settings** → **Domains**
2. Click **"Generate Domain"** or add custom domain
3. Update frontend `VITE_API_URL` with new domain

### Frontend:
1. Go to frontend service → **Settings** → **Domains**
2. Add your custom domain (e.g., `water.yourdomain.com`)
3. Update DNS records as shown

---

## Monitoring

### View Logs:
```bash
railway logs
```

Or in Railway dashboard:
- Click service → **Deployments** → **View Logs**

### Metrics:
- CPU usage
- Memory usage
- Request count
- Response times

Available in Railway dashboard under **Metrics** tab.

---

## Troubleshooting

### Backend won't start:
```bash
# Check logs
railway logs

# Common issues:
# - Missing environment variables
# - Database connection failed
# - Port binding error
```

### Frontend can't connect:
- Verify `VITE_API_URL` is correct
- Check CORS settings in backend
- Ensure backend is running

### Database errors:
```bash
# Reinitialize database
railway run python scripts/init_db.py
```

### WebSocket not working:
- Ensure using `wss://` (not `ws://`)
- Check Railway supports WebSocket (it does)
- Verify CORS allows WebSocket connections

---

## Cost Estimate

Railway free tier: **$5 credit/month**

Estimated usage:
- Backend: ~$3/month
- Frontend: ~$1/month
- Total: ~$4/month (within free tier)

For production with high traffic, upgrade to Pro plan ($20/month).

---

## Scaling

### Horizontal Scaling:
Railway auto-scales based on traffic.

### Vertical Scaling:
Upgrade service resources in Railway dashboard.

### Database:
Consider Railway's managed PostgreSQL for better performance.

---

## Backup Strategy

### Database Backup:
```bash
# Manual backup
railway run python scripts/backup.sh

# Automated backups
# Set up in Railway dashboard or use cron job
```

### Code Backup:
- GitHub (primary)
- Railway keeps deployment history

---

## Security Checklist

- [x] HTTPS enabled (automatic)
- [x] Environment variables secured
- [ ] Change default admin password
- [ ] Rotate SECRET_KEY
- [ ] Enable rate limiting
- [ ] Configure firewall rules
- [ ] Set up monitoring alerts

---

## Next Steps

1. ✅ Deploy backend
2. ✅ Deploy frontend
3. ✅ Initialize database
4. ✅ Test application
5. 🔄 Change admin password
6. 🔄 Configure custom domain
7. 🔄 Set up monitoring
8. 🔄 Enable backups

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: Your repo issues page

---

**Your app will be live at:**
- Frontend: `https://randwater.up.railway.app`
- Backend: `https://randwater-backend.up.railway.app`
- API Docs: `https://randwater-backend.up.railway.app/docs`
