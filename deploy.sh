#!/bin/bash
# National Water Infrastructure Monitoring System - Railway Deployment Script
# This script automates the deployment process to Railway.app

set -e

echo "========================================"
echo "Water Monitoring System - Railway Deploy"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "${BLUE}[1/7] Checking prerequisites...${NC}"
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}Railway CLI not found. Installing...${NC}"
    npm install -g @railway/cli
fi
echo -e "${GREEN}✓ Railway CLI is installed${NC}"
echo ""

# Step 2: Setup environment
echo -e "${BLUE}[2/7] Setting up environment...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env from .env.example${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update .env with your Railway credentials before continuing...${NC}"
    echo "Press Enter to continue after updating .env"
    read
fi
echo -e "${GREEN}✓ Environment file ready${NC}"
echo ""

# Step 3: Login to Railway
echo -e "${BLUE}[3/7] Authenticating with Railway...${NC}"
railway login
echo -e "${GREEN}✓ Successfully authenticated${NC}"
echo ""

# Step 4: Create project (if needed)
echo -e "${BLUE}[4/7] Setting up Railway project...${NC}"
railway init --name water-monitoring || true
echo -e "${GREEN}✓ Project configured${NC}"
echo ""

# Step 5: Deploy backend
echo -e "${BLUE}[5/7] Deploying application...${NC}"
cd backend
railway up
cd ..
echo -e "${GREEN}✓ Application deployed${NC}"
echo ""

# Step 6: Initialize database
echo -e "${BLUE}[6/7] Initializing database...${NC}"
railway shell << 'EOF'
cd /app
python scripts/init_db.py
echo "Database initialized successfully"
EOF
echo -e "${GREEN}✓ Database initialized${NC}"
echo ""

# Step 7: Verification
echo -e "${BLUE}[7/7] Verifying deployment...${NC}"
sleep 10  # Wait for app to start

APP_URL=$(railway status | grep "https://" | awk '{print $NF}')
if [ -z "$APP_URL" ]; then
    echo -e "${YELLOW}Could not determine app URL automatically${NC}"
    echo "Please check your Railway dashboard for the app URL"
else
    echo "App URL: $APP_URL"
    
    # Check health
    if curl -s "$APP_URL/health" | grep -q "healthy"; then
        echo -e "${GREEN}✓ Health check passed${NC}"
    else
        echo -e "${YELLOW}Health check failed - may still be starting up${NC}"
    fi
fi

echo ""
echo "========================================"
echo -e "${GREEN}Deployment complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Create admin user:"
echo "   railway shell"
echo "   python -c 'from backend.app.core.security import get_password_hash; ...'"
echo ""
echo "2. Visit the app:"
echo "   $APP_URL"
echo ""
echo "3. Check API docs:"
echo "   $APP_URL/docs"
echo ""
echo "4. Configure your system:"
echo "   - Create municipalities"
echo "   - Register sensors"
echo "   - Set alert thresholds"
echo ""
echo "For detailed information, see QUICK_START_GUIDE.md"
echo ""
