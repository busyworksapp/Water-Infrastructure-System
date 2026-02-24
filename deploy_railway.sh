#!/bin/bash

echo "🚂 RandWater Railway Deployment Script"
echo "========================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "🔐 Logging into Railway..."
railway login

# Deploy Backend
echo ""
echo "🔧 Deploying Backend..."
cd backend
railway init --name randwater-backend
railway up

echo ""
echo "⚙️  Setting backend environment variables..."
echo "Please enter your credentials:"

read -p "DATABASE_URL: " db_url
read -p "REDIS_URL: " redis_url
read -sp "SECRET_KEY (press enter to generate): " secret_key
echo ""

if [ -z "$secret_key" ]; then
    secret_key=$(openssl rand -hex 32)
    echo "Generated SECRET_KEY: $secret_key"
fi

railway variables set DATABASE_URL="$db_url"
railway variables set REDIS_URL="$redis_url"
railway variables set SECRET_KEY="$secret_key"
railway variables set ENVIRONMENT="production"
railway variables set PORT="8000"

# Get backend URL
backend_url=$(railway domain)
echo "✅ Backend deployed at: $backend_url"

# Initialize database
echo ""
echo "🗄️  Initializing database..."
railway run python scripts/init_db.py

# Deploy Frontend
echo ""
echo "🎨 Deploying Frontend..."
cd ../frontend-web
railway init --name randwater-frontend

railway variables set VITE_API_URL="https://$backend_url/api/v1"
railway variables set VITE_WS_URL="wss://$backend_url"

railway up

frontend_url=$(railway domain)
echo "✅ Frontend deployed at: $frontend_url"

# Update backend CORS
echo ""
echo "🔗 Updating CORS settings..."
cd ../backend
railway variables set CORS_ORIGINS="https://$frontend_url"

echo ""
echo "========================================"
echo "✅ Deployment Complete!"
echo "========================================"
echo ""
echo "🌐 Frontend: https://$frontend_url"
echo "🔧 Backend: https://$backend_url"
echo "📚 API Docs: https://$backend_url/docs"
echo ""
echo "🔑 Default Login:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "⚠️  IMPORTANT: Change the admin password immediately!"
echo ""
