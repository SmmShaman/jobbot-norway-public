#!/bin/bash
# Quick Worker restart script for Terminal Claude
# This script pulls latest code and restarts the Worker

set -e  # Exit on error

echo "=================================================="
echo "🔄 JobBot Worker Quick Restart"
echo "=================================================="
echo ""

# Navigate to project directory
cd ~/jobbot-norway-public

echo "📥 Step 1/4: Pulling latest code from git..."
git pull origin claude/jobbot-norway-metadata-011CUuyJhire2DdZRPu76sND
echo "✅ Code updated"
echo ""

echo "🛑 Step 2/4: Stopping old Worker process..."
pkill -f "python.*worker.py" 2>/dev/null || echo "No Worker process found (OK)"
sleep 1
echo "✅ Old Worker stopped"
echo ""

echo "🚀 Step 3/4: Starting Worker..."
cd worker
export SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_ROLE_KEY

# Clear old log
> worker.log

nohup python worker.py > worker.log 2>&1 &
WORKER_PID=$!
echo "✅ Worker started (PID: $WORKER_PID)"
echo ""

echo "⏳ Step 4/4: Waiting for Worker to initialize..."
sleep 3

echo ""
echo "=================================================="
echo "✅ WORKER IS RUNNING!"
echo "=================================================="
echo ""
echo "📊 Showing last 20 lines of log:"
echo "--------------------------------------------------"
tail -20 worker.log
echo "--------------------------------------------------"
echo ""
echo "💡 To monitor logs in real-time:"
echo "   tail -f ~/jobbot-norway-public/worker/worker.log"
echo ""
echo "💡 To stop Worker:"
echo "   pkill -f 'python.*worker.py'"
echo ""
echo "🎯 Now create a task in Dashboard and watch the logs!"
echo "=================================================="
