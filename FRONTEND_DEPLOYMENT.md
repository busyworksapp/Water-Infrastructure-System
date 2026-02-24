# 🚀 Frontend Deployment Guide

## Quick Deploy Options

### Option 1: Vercel (Recommended - Easiest)

1. **Install Vercel CLI:**
```bash
npm install -g vercel
```

2. **Deploy Control Room:**
```bash
cd frontend-control-room
vercel
```

3. **Follow prompts:**
   - Login to Vercel
   - Set project name
   - Deploy!

**Your app will be live at:** `https://your-project.vercel.app`

---

### Option 2: Netlify

1. **Install Netlify CLI:**
```bash
npm install -g netlify-cli
```

2. **Build and Deploy:**
```bash
cd frontend-control-room
npm run build
netlify deploy --prod
```

---

### Option 3: Run Locally (Development)

**Control Room Desktop:**
```bash
cd frontend-control-room
npm install
npm start  # Web version
# or
npm run electron-dev  # Desktop version
```

**Mobile App:**
```bash
cd mobile-app
npm install
npm start  # Opens Expo
```

---

## 📝 Before Deploying

The `.env.production` files are already configured with your Railway API:

**frontend-control-room/.env.production:**
```
REACT_APP_API_URL=https://water-infrastructure-system-production.up.railway.app
REACT_APP_WS_URL=wss://water-infrastructure-system-production.up.railway.app
```

**mobile-app/.env.production:**
```
EXPO_PUBLIC_API_URL=https://water-infrastructure-system-production.up.railway.app
```

---

## 🎯 Recommended: Deploy to Vercel Now

Run these commands:

```bash
# 1. Go to frontend directory
cd frontend-control-room

# 2. Install dependencies
npm install

# 3. Deploy to Vercel
npx vercel --prod
```

That's it! Your frontend will be live in ~2 minutes! 🎉

---

## 📱 For Mobile App

Use Expo's build service:

```bash
cd mobile-app
npm install
npx expo build:web  # Web version
# or
eas build --platform android  # Android APK
eas build --platform ios  # iOS IPA
```

---

## 🔗 After Deployment

1. Visit your deployed frontend URL
2. Login with the credentials you created via API
3. Start monitoring your water infrastructure!

---

**Need help?** Let me know which deployment option you prefer!
