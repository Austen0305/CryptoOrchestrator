#!/bin/bash
# Find Cloudflare tunnel URL

echo "🔍 Checking for Cloudflare tunnel..."
echo ""

# Check if cloudflared service is running
if systemctl is-active --quiet cloudflared 2>/dev/null; then
    echo "✅ Cloudflare tunnel service is running"
    systemctl status cloudflared --no-pager -l | head -20
elif systemctl is-active --quiet cloudflare-tunnel 2>/dev/null; then
    echo "✅ Cloudflare tunnel service is running (cloudflare-tunnel)"
    systemctl status cloudflare-tunnel --no-pager -l | head -20
else
    echo "⚠️  Cloudflare tunnel service not found in systemd"
fi

echo ""
echo "🔍 Checking for cloudflared processes:"
ps aux | grep cloudflared | grep -v grep || echo "No cloudflared processes found"

echo ""
echo "🔍 Checking cloudflared logs (if available):"
if [ -f ~/.cloudflared/logs ]; then
    tail -30 ~/.cloudflared/logs 2>/dev/null | grep -i "url\|trycloudflare\|https://" || echo "No URLs found in logs"
fi

echo ""
echo "🔍 Checking for cloudflared config:"
if [ -f ~/.cloudflared/config.yml ]; then
    echo "Config file found at ~/.cloudflared/config.yml"
    cat ~/.cloudflared/config.yml | grep -i "url\|hostname\|tunnel" || echo "No URL config found"
fi

echo ""
echo "💡 To find your Cloudflare tunnel URL, you can:"
echo "   1. Check your Cloudflare dashboard"
echo "   2. Check the terminal where you started the tunnel"
echo "   3. Look for a line like: 'https://xxxxx.trycloudflare.com'"
echo "   4. If using quick tunnel: cloudflared tunnel --url http://localhost:8000"
echo "   5. Check systemd logs: sudo journalctl -u cloudflared -n 50 | grep -i url"
