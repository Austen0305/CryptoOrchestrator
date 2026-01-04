#!/bin/bash
# Setup systemd services for CryptoOrchestrator Backend and Cloudflare Tunnel
# Run this script on your GCP VM

set -e

echo "🔧 Setting up systemd services for CryptoOrchestrator"
echo ""

# Get the current user
CURRENT_USER=$(whoami)
PROJECT_DIR="/home/${CURRENT_USER}/CryptoOrchestrator"

# Check if running as root (we need sudo for systemd)
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please run this script as a regular user (not root)"
    echo "   The script will use sudo when needed"
    exit 1
fi

echo "📋 Current user: ${CURRENT_USER}"
echo "📁 Project directory: ${PROJECT_DIR}"
echo ""

# Step 1: Copy systemd service files
echo "📝 Step 1: Installing systemd service files..."
sudo cp "${PROJECT_DIR}/scripts/deployment/cryptoorchestrator-backend.service" /etc/systemd/system/
sudo cp "${PROJECT_DIR}/scripts/deployment/cloudflare-tunnel.service" /etc/systemd/system/

# Update service files with correct user
sudo sed -i "s/User=labarcodez/User=${CURRENT_USER}/g" /etc/systemd/system/cryptoorchestrator-backend.service
sudo sed -i "s/Group=labarcodez/Group=${CURRENT_USER}/g" /etc/systemd/system/cryptoorchestrator-backend.service
sudo sed -i "s|/home/labarcodez|/home/${CURRENT_USER}|g" /etc/systemd/system/cryptoorchestrator-backend.service

sudo sed -i "s/User=labarcodez/User=${CURRENT_USER}/g" /etc/systemd/system/cloudflare-tunnel.service
sudo sed -i "s/Group=labarcodez/Group=${CURRENT_USER}/g" /etc/systemd/system/cloudflare-tunnel.service
sudo sed -i "s|/home/labarcodez|/home/${CURRENT_USER}|g" /etc/systemd/system/cloudflare-tunnel.service

echo "✅ Service files installed"
echo ""

# Step 2: Reload systemd
echo "🔄 Step 2: Reloading systemd daemon..."
sudo systemctl daemon-reload
echo "✅ Systemd daemon reloaded"
echo ""

# Step 3: Enable and start backend service
echo "🚀 Step 3: Enabling and starting backend service..."
sudo systemctl enable cryptoorchestrator-backend.service
sudo systemctl start cryptoorchestrator-backend.service
echo "✅ Backend service enabled and started"
echo ""

# Step 4: Check backend service status
echo "📊 Step 4: Checking backend service status..."
sleep 2
sudo systemctl status cryptoorchestrator-backend.service --no-pager -l || true
echo ""

# Step 5: Install cloudflared if needed
echo "☁️  Step 5: Checking cloudflared installation..."
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."
    
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ]; then
        ARCH="arm64"
    else
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
    fi
    
    curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}" -o /tmp/cloudflared
    chmod +x /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    echo "✅ cloudflared installed"
else
    echo "✅ cloudflared already installed"
fi
echo ""

# Step 6: Enable Cloudflare Tunnel service (but don't start yet - user needs to see the URL first)
echo "🚇 Step 6: Enabling Cloudflare Tunnel service..."
sudo systemctl enable cloudflare-tunnel.service
echo "✅ Cloudflare Tunnel service enabled (not started yet)"
echo ""

# Step 7: Show status and next steps
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup Complete!"
echo ""
echo "📋 Service Status:"
sudo systemctl is-active cryptoorchestrator-backend.service && echo "   ✅ Backend: Running" || echo "   ❌ Backend: Not running"
sudo systemctl is-enabled cryptoorchestrator-backend.service && echo "   ✅ Backend: Enabled (will start on boot)" || echo "   ⚠️  Backend: Not enabled"
sudo systemctl is-enabled cloudflare-tunnel.service && echo "   ✅ Tunnel: Enabled" || echo "   ⚠️  Tunnel: Not enabled"
echo ""
echo "🔍 Useful Commands:"
echo "   View backend logs:     sudo journalctl -u cryptoorchestrator-backend -f"
echo "   View tunnel logs:      sudo journalctl -u cloudflare-tunnel -f"
echo "   Restart backend:       sudo systemctl restart cryptoorchestrator-backend"
echo "   Stop backend:          sudo systemctl stop cryptoorchestrator-backend"
echo "   Start tunnel:          sudo systemctl start cloudflare-tunnel"
echo "   Stop tunnel:           sudo systemctl stop cloudflare-tunnel"
echo ""
echo "🚇 To start Cloudflare Tunnel and get HTTPS URL:"
echo "   sudo systemctl start cloudflare-tunnel"
echo "   sudo journalctl -u cloudflare-tunnel -f"
echo "   (Look for a URL like: https://xxxxx.trycloudflare.com)"
echo ""
echo "🌐 After getting the tunnel URL, update Vercel environment variables:"
echo "   VITE_API_URL=https://xxxxx.trycloudflare.com"
echo "   VITE_WS_BASE_URL=wss://xxxxx.trycloudflare.com"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
