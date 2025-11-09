#!/bin/bash
# ====================================================================
# 🤖 НАЛАШТУВАННЯ GITHUB ACTIONS RUNNER
# ====================================================================
# Цей скрипт допоможе тобі налаштувати GitHub Actions self-hosted runner
# ====================================================================

echo "======================================================================"
echo "🤖 GitHub Actions Self-Hosted Runner Setup"
echo "======================================================================"
echo ""

echo "📋 INSTRUCTIONS:"
echo ""
echo "1️⃣ Відкрий GitHub в браузері:"
echo "   https://github.com/SmmShaman/jobbot-norway-public/settings/actions/runners/new"
echo ""
echo "2️⃣ Вибери:"
echo "   • Operating System: Linux"
echo "   • Architecture: X64"
echo ""
echo "3️⃣ GitHub покаже команди схожі на ці:"
echo ""
echo "   # Download"
echo "   mkdir actions-runner && cd actions-runner"
echo "   curl -o actions-runner-linux-x64-2.XXX.X.tar.gz -L https://github.com/actions/runner/releases/download/vX.XXX.X/actions-runner-linux-x64-2.XXX.X.tar.gz"
echo "   tar xzf ./actions-runner-linux-x64-2.XXX.X.tar.gz"
echo ""
echo "   # Configure"
echo "   ./config.sh --url https://github.com/SmmShaman/jobbot-norway-public --token YOUR_TOKEN"
echo ""
echo "   # Run as service"
echo "   sudo ./svc.sh install"
echo "   sudo ./svc.sh start"
echo ""
echo "======================================================================"
echo ""

read -p "❓ Хочеш щоб я автоматично завантажив і встановив Runner? (Y/N): " AUTO_INSTALL

if [ "$AUTO_INSTALL" != "Y" ] && [ "$AUTO_INSTALL" != "y" ]; then
    echo ""
    echo "👍 OK! Встанови вручну використовуючи команди з GitHub."
    echo "   URL: https://github.com/SmmShaman/jobbot-norway-public/settings/actions/runners/new"
    exit 0
fi

echo ""
echo "🚀 Автоматичне встановлення..."
echo ""

# Create actions-runner directory
RUNNER_DIR="/home/stuard/actions-runner"

if [ -d "$RUNNER_DIR" ]; then
    echo "⚠️ Directory $RUNNER_DIR already exists!"
    read -p "   Видалити і створити заново? (Y/N): " RECREATE

    if [ "$RECREATE" = "Y" ] || [ "$RECREATE" = "y" ]; then
        # Stop service if running
        if [ -f "$RUNNER_DIR/svc.sh" ]; then
            sudo $RUNNER_DIR/svc.sh stop 2>/dev/null || true
            sudo $RUNNER_DIR/svc.sh uninstall 2>/dev/null || true
        fi

        rm -rf "$RUNNER_DIR"
        echo "✅ Old runner removed"
    else
        echo "❌ Cancelled"
        exit 1
    fi
fi

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Download latest runner (check https://github.com/actions/runner/releases)
echo "📥 Downloading GitHub Actions Runner..."
RUNNER_VERSION="2.321.0"  # Оновлюється часто, перевір актуальну версію
RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"

curl -o actions-runner-linux-x64.tar.gz -L "$RUNNER_URL"

if [ $? -ne 0 ]; then
    echo "❌ Failed to download runner!"
    echo "💡 Спробуй вручну:"
    echo "   https://github.com/SmmShaman/jobbot-norway-public/settings/actions/runners/new"
    exit 1
fi

echo "✅ Downloaded!"
echo ""

# Extract
echo "📦 Extracting..."
tar xzf ./actions-runner-linux-x64.tar.gz
rm actions-runner-linux-x64.tar.gz

echo "✅ Extracted!"
echo ""

echo "======================================================================"
echo "⚠️ ВАЖЛИВО: Тепер потрібен TOKEN з GitHub!"
echo "======================================================================"
echo ""
echo "1. Відкрий в браузері:"
echo "   https://github.com/SmmShaman/jobbot-norway-public/settings/actions/runners/new"
echo ""
echo "2. Знайди команду ./config.sh --url ... --token XXXXX"
echo ""
echo "3. Скопіюй ТІЛЬКИ TOKEN (довгий рядок після --token)"
echo ""
read -p "Вставляй TOKEN сюди: " GITHUB_TOKEN

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Token порожній!"
    echo ""
    echo "💡 Запусти конфігурацію вручну:"
    echo "   cd $RUNNER_DIR"
    echo "   ./config.sh --url https://github.com/SmmShaman/jobbot-norway-public --token YOUR_TOKEN"
    exit 1
fi

echo ""
echo "🔧 Configuring runner..."

./config.sh \
    --url https://github.com/SmmShaman/jobbot-norway-public \
    --token "$GITHUB_TOKEN" \
    --name "azure-vm-worker" \
    --labels self-hosted,linux,x64,azure,jobbot \
    --work _work \
    --unattended \
    --replace

if [ $? -ne 0 ]; then
    echo "❌ Configuration failed!"
    exit 1
fi

echo "✅ Runner configured!"
echo ""

# Install as service
echo "🔧 Installing as systemd service..."
sudo ./svc.sh install

if [ $? -ne 0 ]; then
    echo "❌ Service installation failed!"
    exit 1
fi

echo "✅ Service installed!"
echo ""

# Start service
echo "🚀 Starting runner service..."
sudo ./svc.sh start

if [ $? -ne 0 ]; then
    echo "❌ Failed to start service!"
    exit 1
fi

echo "✅ Runner started!"
echo ""

# Check status
echo "======================================================================"
echo "📊 Runner Status:"
echo "======================================================================"
sudo ./svc.sh status

echo ""
echo "======================================================================"
echo "✅ GITHUB RUNNER INSTALLED!"
echo "======================================================================"
echo ""
echo "📋 Verify in GitHub:"
echo "   https://github.com/SmmShaman/jobbot-norway-public/settings/actions/runners"
echo ""
echo "   You should see: azure-vm-worker (Idle)"
echo ""
echo "🎯 Now when you (Claude) do 'git push', the workflow will run HERE!"
echo ""
echo "======================================================================"
