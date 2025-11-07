#!/bin/bash
# ============================================================
# JobBot Worker - Automatic Setup Script
# Run this on your LOCAL PC (where Skyvern is running)
# ============================================================

set -e  # Exit on error

echo "============================================"
echo "🤖 JobBot Worker Setup Script"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "worker.py" ]; then
    echo -e "${RED}❌ Error: worker.py not found!${NC}"
    echo "Please run this script from the worker/ directory:"
    echo "  cd ~/jobbot-norway-public/worker"
    echo "  bash setup_worker.sh"
    exit 1
fi

echo -e "${GREEN}✅ Found worker.py${NC}"
echo ""

# Step 1: Check Python
echo "📋 Step 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found! Please install Python 3.8+${NC}"
    exit 1
fi
echo ""

# Step 2: Install dependencies
echo "📦 Step 2: Installing Python dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi
echo ""

# Step 3: Check for .env file
echo "🔧 Step 3: Setting up .env file..."
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping .env creation. Using existing file."
        ENV_EXISTS=true
    else
        ENV_EXISTS=false
    fi
else
    ENV_EXISTS=false
fi

if [ "$ENV_EXISTS" = false ]; then
    echo "Creating .env file..."

    # Prompt for SUPABASE_SERVICE_KEY
    echo ""
    echo -e "${YELLOW}📋 Please provide your Supabase credentials:${NC}"
    echo "Get your service_role key from:"
    echo "  https://app.supabase.com/project/ptrmidlhfdbybxmyovtm/settings/api"
    echo ""
    read -p "Paste your SUPABASE_SERVICE_KEY (starts with eyJ...): " SUPABASE_KEY

    # Create .env file
    cat > .env << EOF
# JobBot Worker Configuration

# Supabase (Database in the cloud)
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=$SUPABASE_KEY

# Skyvern (Running on local PC)
SKYVERN_API_URL=http://localhost:8000
EOF

    echo -e "${GREEN}✅ .env file created${NC}"
fi
echo ""

# Step 4: Verify Skyvern is running
echo "🤖 Step 4: Checking Skyvern status..."
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Skyvern is running on http://localhost:8000${NC}"
else
    echo -e "${RED}❌ Skyvern is NOT running!${NC}"
    echo ""
    echo "Please start Skyvern first:"
    echo "  docker ps | grep skyvern"
    echo "  docker-compose up -d skyvern"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Step 5: Test Worker
echo "🧪 Step 5: Testing Worker..."
echo "Running quick test (will exit after 5 seconds)..."
echo ""

# Run worker with timeout
timeout 5 $PYTHON_CMD worker.py || true

echo ""
echo "============================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "============================================"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Verify .env file has correct credentials:"
echo "   cat .env"
echo ""
echo "2. Make sure Skyvern is running:"
echo "   curl http://localhost:8000/api/v1/health"
echo ""
echo "3. Start the Worker:"
echo "   $PYTHON_CMD worker.py"
echo ""
echo "4. In another terminal, trigger a scan from Dashboard:"
echo "   https://jobbotnetlify.netlify.app/dashboard"
echo ""
echo "5. Monitor Worker logs:"
echo "   tail -f worker.log"
echo ""
echo "============================================"
echo "🎉 Happy job hunting!"
echo "============================================"
