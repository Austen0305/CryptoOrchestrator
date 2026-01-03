#!/bin/bash
# Quick Setup: Cloudflare Tunnel for HTTPS Backend
# This is a quick solution for HTTPS without domain setup

set -e

echo "☁️  Setting up Cloudflare Tunnel for CryptoOrchestrator Backend"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        ARCH=$(uname -m)
        if [ "$ARCH" = "x86_64" ]; then
            ARCH="amd64"
        elif [ "$ARCH" = "aarch64" ]; then
            ARCH="arm64"
        fi
        
        curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}" -o cloudflared
        chmod +x cloudflared
        sudo mv cloudflared /usr/local/bin/
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install cloudflare/cloudflare/cloudflared || {
            curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64" -o cloudflared
            chmod +x cloudflared
            sudo mv cloudflared /usr/local/bin/
        }
    else
        echo "❌ Unsupported OS. Please install cloudflared manually."
        exit 1
    fi
fi

echo "✅ cloudflared installed"
echo ""

# Start tunnel
echo "🚇 Starting Cloudflare Tunnel..."
echo "   This will expose http://localhost:8000 over HTTPS"
echo "   Press Ctrl+C to stop"
echo ""

# Run tunnel (this will output the HTTPS URL)
cloudflared tunnel --url http://localhost:8000

# Note: For persistent tunnel, use:
# cloudflared tunnel create cryptoorchestrator
# cloudflared tunnel route dns cryptoorchestrator api.yourdomain.com
# cloudflared tunnel run cryptoorchestrator
