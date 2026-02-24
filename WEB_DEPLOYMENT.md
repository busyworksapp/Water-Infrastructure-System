# Web Application Deployment Guide

## Quick Start (Local Development)

### 1. Start Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. Start Web Frontend
```bash
cd frontend-web
npm install
npm run dev
```

Access at: http://localhost:3000

---

## Production Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose -f docker-compose.web.yml up -d

# View logs
docker-compose -f docker-compose.web.yml logs -f

# Stop services
docker-compose -f docker-compose.web.yml down
```

Access at: http://localhost

---

### Option 2: Railway (Backend + Frontend)

#### Backend Deployment:
1. Push code to GitHub
2. Go to railway.app
3. Create new project from GitHub repo
4. Select `backend` folder
5. Add environment variables:
   - DATABASE_URL
   - REDIS_URL
   - SECRET_KEY
   - S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY

#### Frontend Deployment:
1. Create another service in same project
2. Select `frontend-web` folder
3. Add environment variables:
   - VITE_API_URL=https://your-backend.railway.app/api/v1
   - VITE_WS_URL=wss://your-backend.railway.app

---

### Option 3: Vercel (Frontend) + Railway (Backend)

#### Backend on Railway:
Same as Option 2 backend steps

#### Frontend on Vercel:
```bash
cd frontend-web
npm install -g vercel
vercel --prod
```

Set environment variables in Vercel dashboard:
- VITE_API_URL
- VITE_WS_URL

---

### Option 4: AWS/Azure/GCP

#### Backend:
- Deploy to EC2/App Service/Compute Engine
- Use managed PostgreSQL/MySQL
- Use managed Redis
- Configure load balancer

#### Frontend:
- Build: `npm run build`
- Deploy dist/ to S3/Blob Storage/Cloud Storage
- Use CloudFront/CDN for distribution

---

## Environment Variables

### Backend (.env)
```
DATABASE_URL=mysql+pymysql://user:pass@host:port/db
REDIS_URL=redis://default:pass@host:port
SECRET_KEY=your-secret-key
S3_ENDPOINT=https://t3.storageapi.dev
S3_BUCKET=your-bucket
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
```

### Frontend (.env.production)
```
VITE_API_URL=https://your-backend-url.com/api/v1
VITE_WS_URL=wss://your-backend-url.com
```

---

## Default Credentials

After running init_db.py:
- Username: `admin`
- Password: `admin123`

**Change immediately in production!**

---

## Features

✅ Real-time sensor monitoring
✅ WebSocket live updates
✅ Interactive map with Leaflet
✅ Alert management
✅ SCADA-style industrial UI
✅ Mobile responsive
✅ JWT authentication
✅ Role-based access control

---

## Troubleshooting

### CORS Issues
Update backend `app/core/config.py`:
```python
CORS_ORIGINS = ["https://your-frontend-url.com"]
```

### WebSocket Connection Failed
Ensure backend supports WebSocket and CORS is configured

### Map Not Loading
Check Leaflet CSS is loaded in index.html

---

## Production Checklist

- [ ] Change default admin password
- [ ] Set strong SECRET_KEY
- [ ] Configure HTTPS/SSL
- [ ] Enable security headers
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Set up logging
- [ ] Enable rate limiting
- [ ] Configure firewall rules
- [ ] Set up CI/CD pipeline

---

## Support

For issues, check logs:
- Backend: `docker-compose logs backend`
- Frontend: Browser console (F12)
