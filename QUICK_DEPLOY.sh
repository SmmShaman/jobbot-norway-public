#!/bin/bash
# 🚀 ONE-COMMAND DEPLOYMENT SCRIPT
# Deploys both frontend and backend automatically

set -e

echo "🚀 JobBot Norway - Quick Deploy"
echo "================================"
echo ""
echo "This script will:"
echo "  ✅ Deploy backend to Railway"
echo "  ✅ Get Railway URL"
echo "  ✅ Update Netlify environment variables"
echo "  ✅ Trigger Netlify redeploy"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Canceled."
    exit 1
fi

# Step 1: Deploy backend
echo ""
echo "📦 Step 1: Deploying backend to Railway..."
cd backend
./deploy_railway.sh

# Get Railway URL
echo ""
echo "🌐 Getting Railway URL..."
RAILWAY_URL=$(railway domain 2>/dev/null | grep -o 'https://[^[:space:]]*' | head -1)

if [ -z "$RAILWAY_URL" ]; then
    echo "⚠️  Could not auto-detect Railway URL"
    echo "Please enter your Railway URL manually:"
    read -r RAILWAY_URL
fi

echo "✅ Railway URL: $RAILWAY_URL"

# Step 2: Update Netlify
echo ""
echo "📝 Step 2: Updating Netlify environment variables..."
echo ""
echo "⚠️  MANUAL ACTION REQUIRED:"
echo ""
echo "1. Go to: https://app.netlify.com"
echo "2. Your site → Site settings → Environment variables"
echo "3. Update: VITE_API_URL = $RAILWAY_URL"
echo "4. Save and trigger redeploy"
echo ""
echo "OR use Netlify CLI:"
echo "   netlify env:set VITE_API_URL $RAILWAY_URL"
echo "   netlify deploy --prod"
echo ""

read -p "Press Enter when Netlify is updated..."

# Step 3: Test
echo ""
echo "🧪 Step 3: Testing deployment..."
echo ""
echo "Testing backend health..."
curl -s "$RAILWAY_URL/health" | jq '.' || echo "⚠️  Backend not responding yet (may still be deploying)"

echo ""
echo "Testing frontend..."
NETLIFY_URL="https://jobbotnetlify.netlify.app"  # Replace with your actual URL
curl -s -o /dev/null -w "%{http_code}" "$NETLIFY_URL" || echo "⚠️  Frontend check failed"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 URLs:"
echo "   Frontend: $NETLIFY_URL"
echo "   Backend:  $RAILWAY_URL"
echo "   API Docs: $RAILWAY_URL/docs"
echo ""
echo "🎉 Done! Test your application now."
