#!/bin/bash
# Setup Cloudflare Tunnel for HTTPS backend access
# This provides free HTTPS for your backend without needing a domain or SSL certificate

set -e

echo "Setting up Cloudflare Tunnel..."

# Install cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "Installing cloudflared..."
    curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared.deb
    rm cloudflared.deb
    echo "cloudflared installed successfully"
else
    echo "cloudflared already installed"
fi

# Create systemd service for cloudflared
echo "Creating cloudflared service..."

sudo tee /etc/systemd/system/cloudflared.service > /dev/null <<EOF
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Start and enable the service
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

echo "Cloudflare Tunnel service started"
echo "Waiting for tunnel to establish..."

sleep 5

# Get the tunnel URL
TUNNEL_URL=$(sudo journalctl -u cloudflared -n 50 --no-pager | grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1)

if [ -z "$TUNNEL_URL" ]; then
    echo "Warning: Could not automatically detect tunnel URL"
    echo "Please check: sudo journalctl -u cloudflared -f"
    echo "Look for a line containing: https://*.trycloudflare.com"
else
    echo ""
    echo "========================================="
    echo "✅ Cloudflare Tunnel is running!"
    echo "========================================="
    echo "Your backend HTTPS URL is: $TUNNEL_URL"
    echo ""
    echo "Update your Vercel environment variable:"
    echo "VITE_API_URL = $TUNNEL_URL"
    echo "VITE_WS_URL = $(echo $TUNNEL_URL | sed 's|https://|wss://|')"
    echo "========================================="
fi
