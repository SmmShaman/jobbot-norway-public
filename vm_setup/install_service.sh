#!/bin/bash
# ====================================================================
# 🔧 ВСТАНОВЛЕННЯ WORKER ЯК SYSTEMD SERVICE
# ====================================================================

echo "======================================================================"
echo "🔧 Installing JobBot Worker as systemd service"
echo "======================================================================"
echo ""

# Перевірка прав
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root or with sudo:"
    echo "   sudo bash vm_setup/install_service.sh"
    exit 1
fi

echo "✅ Running as root"
echo ""

# Копіювати service file
echo "📝 Installing service file..."
cp /home/stuard/jobbot-norway-public/vm_setup/jobbot-worker.service /etc/systemd/system/

if [ $? -eq 0 ]; then
    echo "✅ Service file copied to /etc/systemd/system/"
else
    echo "❌ Failed to copy service file"
    exit 1
fi

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Зупинити старий Worker якщо працює
echo "🛑 Stopping old Worker process..."
pkill -f "python3 worker_v2.py" || echo "No running Worker found"

sleep 2

# Enable service
echo "⚙️ Enabling service to start on boot..."
systemctl enable jobbot-worker.service

# Start service
echo "🚀 Starting Worker service..."
systemctl start jobbot-worker.service

sleep 3

# Check status
echo ""
echo "======================================================================"
echo "📊 Service Status:"
echo "======================================================================"
systemctl status jobbot-worker.service --no-pager

echo ""
echo "======================================================================"
echo "✅ INSTALLATION COMPLETE!"
echo "======================================================================"
echo ""
echo "📋 Useful commands:"
echo "   sudo systemctl status jobbot-worker    # Check status"
echo "   sudo systemctl restart jobbot-worker   # Restart Worker"
echo "   sudo systemctl stop jobbot-worker      # Stop Worker"
echo "   sudo systemctl start jobbot-worker     # Start Worker"
echo "   sudo journalctl -u jobbot-worker -f    # View logs (live)"
echo "   tail -f /home/stuard/jobbot-norway-public/worker/worker.log"
echo ""
echo "======================================================================"
