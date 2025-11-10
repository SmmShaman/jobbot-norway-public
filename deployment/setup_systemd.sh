#!/bin/bash
# ============================================================
# Setup systemd service for JobBot Worker v2
# This script configures worker to run as a system service
# ============================================================

set -e  # Exit on error

echo "=========================================="
echo "Setting up JobBot Worker v2 systemd service"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

SERVICE_NAME="worker_v2"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SOURCE_FILE="/home/stuard/jobbot-norway-public/deployment/worker_v2.service"

# Step 1: Check if source service file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "ERROR: Service file not found: $SOURCE_FILE"
    exit 1
fi

echo "Found service file: $SOURCE_FILE"

# Step 2: Check if worker directory and script exist
if [ ! -f "/home/stuard/jobbot-norway-public/worker/worker_v2.py" ]; then
    echo "ERROR: Worker script not found"
    exit 1
fi

echo "Worker script found"

# Step 3: Check if .env file exists
if [ ! -f "/home/stuard/jobbot-norway-public/worker/.env" ]; then
    echo "WARNING: .env file not found - worker may fail to start"
    echo "Create .env file with:"
    echo "  SUPABASE_URL=your_url"
    echo "  SUPABASE_SERVICE_KEY=your_key"
fi

# Step 4: Stop existing service if running
if systemctl is-active --quiet ${SERVICE_NAME}; then
    echo "Stopping existing ${SERVICE_NAME} service..."
    systemctl stop ${SERVICE_NAME}
fi

# Step 5: Copy service file
echo "Installing service file..."
cp "$SOURCE_FILE" "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

# Step 6: Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Step 7: Enable service (start on boot)
echo "Enabling ${SERVICE_NAME} service..."
systemctl enable ${SERVICE_NAME}

# Step 8: Start service
echo "Starting ${SERVICE_NAME} service..."
systemctl start ${SERVICE_NAME}

# Step 9: Wait a moment and check status
sleep 3

echo ""
echo "=========================================="
echo "Service Status:"
echo "=========================================="
systemctl status ${SERVICE_NAME} --no-pager

echo ""
echo "=========================================="
echo "SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  - Check status:   sudo systemctl status ${SERVICE_NAME}"
echo "  - View logs:      sudo journalctl -u ${SERVICE_NAME} -f"
echo "  - Restart:        sudo systemctl restart ${SERVICE_NAME}"
echo "  - Stop:           sudo systemctl stop ${SERVICE_NAME}"
echo "  - Start:          sudo systemctl start ${SERVICE_NAME}"
echo ""
echo "Worker will now:"
echo "  - Start automatically on system boot"
echo "  - Restart automatically if it crashes"
echo "  - Log to systemd journal"
echo ""
