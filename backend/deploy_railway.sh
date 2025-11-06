#!/bin/bash
# Railway Backend Deployment Script
# This script automates Railway deployment

set -e  # Exit on error

echo "🚂 JobBot Norway - Railway Backend Deployment"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}⚠️  Railway CLI not found. Installing...${NC}"

    # Install Railway CLI
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install railway
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        npm i -g @railway/cli
    else
        echo -e "${RED}❌ Please install Railway CLI manually:${NC}"
        echo "   npm i -g @railway/cli"
        echo "   OR visit: https://docs.railway.app/develop/cli"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Railway CLI installed${NC}"
echo ""

# Check if logged in
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Railway${NC}"
    echo ""
    echo "Please login to Railway:"
    echo "  1. Running 'railway login' will open browser"
    echo "  2. Authorize Railway CLI"
    echo "  3. Come back here and run this script again"
    echo ""
    railway login
    exit 0
fi

echo -e "${GREEN}✅ Authenticated to Railway${NC}"
RAILWAY_USER=$(railway whoami)
echo "   User: $RAILWAY_USER"
echo ""

# Check if we're in a Railway project
echo "📦 Checking Railway project..."
if ! railway status &> /dev/null; then
    echo -e "${YELLOW}⚠️  No Railway project linked${NC}"
    echo ""
    echo "Creating new Railway project..."

    # Create new project
    railway init

    echo -e "${GREEN}✅ Railway project created${NC}"
else
    echo -e "${GREEN}✅ Railway project found${NC}"
    railway status
fi
echo ""

# Link to GitHub (if not already)
echo "🔗 Linking to GitHub repository..."
railway link

# Read environment variables from .env
echo ""
echo "📝 Setting environment variables..."

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Found .env file${NC}"
    echo "   Reading variables..."

    # Read .env and set variables in Railway
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z $key ]] && continue

        # Remove quotes from value
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

        echo "   Setting: $key"
        railway variables --set "$key=$value" 2>/dev/null || echo "   ⚠️  Could not set $key"
    done < .env

    echo -e "${GREEN}✅ Environment variables set${NC}"
else
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "   Please create backend/.env with all required variables"
    exit 1
fi

echo ""
echo "🚀 Deploying to Railway..."
echo ""

# Deploy
railway up --detach

echo ""
echo -e "${GREEN}✅ Deployment started!${NC}"
echo ""
echo "📊 Monitor deployment:"
echo "   railway logs"
echo ""
echo "🌐 Get service URL:"
echo "   railway domain"
echo ""
echo "⚙️  View in dashboard:"
railway open
echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Wait 2-3 minutes for build"
echo "  2. Get your URL: railway domain"
echo "  3. Update Netlify VITE_API_URL with Railway URL"
echo "  4. Test: curl https://your-url.railway.app/health"
