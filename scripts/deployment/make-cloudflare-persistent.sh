#!/bin/bash
# Make Cloudflare Tunnel persistent with systemd
# This ensures the tunnel restarts automatically and survives reboots

set -e

echo "🔧 Making Cloudflare Tunnel Persistent"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not found. Installing..."
    
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ]; then
        ARCH="arm64"
    fi
    
    curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}" -o /tmp/cloudflared
    chmod +x /tmp/cloudflared
    mv /tmp/cloudflared /usr/local/bin/cloudflared
    
    echo "✅ cloudflared installed"
fi

# Get backend port (default 8000)
read -p "Enter backend port (default 8000): " BACKEND_PORT
BACKEND_PORT=${BACKEND_PORT:-8000}

# Create systemd service
echo "📝 Creating systemd service..."
cat > /etc/systemd/system/cloudflared.service <<EOF
[Unit]
Description=Cloudflare Tunnel for CryptoOrchestrator Backend
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:${BACKEND_PORT}
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable service (start on boot)
systemctl enable cloudflared

# Start service
systemctl start cloudflared

# Wait a moment for tunnel to start
sleep 3

# Check status
echo ""
echo "📊 Service Status:"
systemctl status cloudflared --no-pager -l

echo ""
echo "🔍 Getting tunnel URL..."
echo "   (This may take a few seconds)"
sleep 5

# Extract URL from logs
TUNNEL_URL=$(journalctl -u cloudflared --no-pager | grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1)

if [ -n "$TUNNEL_URL" ]; then
    echo ""
    echo "✅ Cloudflare Tunnel is running!"
    echo ""
    echo "📝 Your tunnel URL:"
    echo "   $TUNNEL_URL"
    echo ""
    echo "📝 Set this in Vercel:"
    echo "   VITE_API_URL = ${TUNNEL_URL}/api"
    echo ""
    echo "🔍 To view logs:"
    echo "   sudo journalctl -u cloudflared -f"
    echo ""
    echo "🛑 To stop tunnel:"
    echo "   sudo systemctl stop cloudflared"
    echo ""
    echo "▶️  To start tunnel:"
    echo "   sudo systemctl start cloudflared"
    echo ""
    echo "🔄 To restart tunnel:"
    echo "   sudo systemctl restart cloudflared"
else
    echo ""
    echo "⚠️  Could not extract URL automatically"
    echo "   Check logs manually:"
    echo "   sudo journalctl -u cloudflared -f"
    echo "   Look for a URL like: https://xxxxx.trycloudflare.com"
fi

echo ""
echo "✅ Tunnel is now persistent and will start on boot!"
