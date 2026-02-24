# 🚀 Quick Deploy to Railway

## Method 1: One-Click Deploy (Easiest)

### Windows:
```bash
deploy_railway.bat
```

### Linux/Mac:
```bash
chmod +x deploy_railway.sh
./deploy_railway.sh
```

---

## Method 2: Manual Deploy (5 Minutes)

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/randwater.git
git push -u origin main
```

### Step 2: Deploy on Railway

1. Go to **[railway.app](https://railway.app)**
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository

### Step 3: Configure Backend

1. Select **backend** folder as root directory
2. Add environment variables:
   ```
   DATABASE_URL=mysql+pymysql://root:password@interchange.proxy.rlwy.net:20906/railway
   REDIS_URL=redis://default:password@switchyard.proxy.rlwy.net:10457
   SECRET_KEY=your-secret-key
   ENVIRONMENT=production
   PORT=8000
   ```
3. Click **Deploy**
4. Copy the backend URL

### Step 4: Configure Frontend

1. Click **"New Service"** → **"GitHub Repo"**
2. Select **frontend-web** folder as root directory
3. Add environment variables:
   ```
   VITE_API_URL=https://your-backend-url.railway.app/api/v1
   VITE_WS_URL=wss://your-backend-url.railway.app
   ```
4. Click **Deploy**

### Step 5: Initialize Database

In Railway backend terminal:
```bash
python scripts/init_db.py
```

---

## Method 3: Railway CLI

```bash
# Install CLI
npm i -g @railway/cli

# Login
railway login

# Deploy backend
cd backend
railway init
railway up

# Deploy frontend
cd ../frontend-web
railway init
railway up
```

---

## ✅ Verify Deployment

1. Visit your frontend URL
2. Login: `admin` / `admin123`
3. Check dashboard loads
4. Verify real-time updates

---

## 🔧 Post-Deployment

1. **Change admin password** (Settings → Users)
2. **Add custom domain** (Railway dashboard)
3. **Enable monitoring** (Railway metrics)
4. **Set up backups** (Database backups)

---

## 📊 Expected Costs

- **Free Tier**: $5 credit/month
- **Usage**: ~$4/month (backend + frontend)
- **Remaining**: $1/month buffer

---

## 🆘 Need Help?

See **RAILWAY_DEPLOY.md** for detailed instructions.
