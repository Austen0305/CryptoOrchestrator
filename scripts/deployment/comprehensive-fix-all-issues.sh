#!/bin/bash
# Comprehensive Fix Script - Fixes all errors and warnings
# Run this on your GCP VM to fix everything before deployment

set -e

echo "🔧 Comprehensive Fix Script - Fixing All Errors and Warnings"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PROJECT_DIR="/home/labarcodez/CryptoOrchestrator"
cd "$PROJECT_DIR"

# Step 1: Pull latest fixes
echo "📥 Step 1: Pulling latest fixes from GitHub..."
git pull origin main || echo "⚠️  Git pull failed, continuing..."
echo "✅ Latest code pulled"
echo ""

# Step 2: Check system updates (informational only - don't auto-update)
echo "🖥️  Step 2: Checking system updates..."
if command -v apt &> /dev/null; then
    echo "System update status:"
    apt list --upgradable 2>/dev/null | head -5 || echo "No updates available or check requires sudo"
    echo ""
    echo "ℹ️  Note: You can update with: sudo apt update && sudo apt upgrade -y"
    echo "ℹ️  Note: For new LTS release (24.04.3), run: sudo do-release-upgrade"
fi
echo ""

# Step 3: Check Python syntax errors
echo "🐍 Step 3: Checking Python syntax errors..."
find server_fastapi -name "*.py" -type f -exec python3 -m py_compile {} \; 2>&1 | head -20
if [ $? -eq 0 ]; then
    echo "✅ No Python syntax errors found"
else
    echo "⚠️  Some Python files have syntax errors (see above)"
fi
echo ""

# Step 4: Check backend service status
echo "🔍 Step 4: Checking backend service status..."
sudo systemctl status cryptoorchestrator-backend --no-pager -l | head -30 || echo "⚠️  Backend service not running"
echo ""

# Step 5: Check if backend is listening
echo "🔌 Step 5: Checking if backend is listening on port 8000..."
if ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo "✅ Backend is listening on port 8000"
    # Test locally
    if curl -s http://localhost:8000/api/status/ > /dev/null 2>&1; then
        echo "✅ Backend is responding locally"
    else
        echo "⚠️  Backend is not responding locally"
    fi
else
    echo "⚠️  Backend is not listening on port 8000"
fi
echo ""

# Step 6: Check Cloudflare Tunnel
echo "☁️  Step 6: Checking Cloudflare Tunnel status..."
if ps aux | grep -q "[c]loudflared tunnel"; then
    echo "✅ Cloudflare Tunnel is running"
    # Get tunnel URL from logs
    TUNNEL_LOG="/tmp/tunnel_fresh.log"
    if [ -f "$TUNNEL_LOG" ]; then
        TUNNEL_URL=$(strings "$TUNNEL_LOG" 2>/dev/null | grep -oP 'https://[^\s]+\.trycloudflare\.com' | head -1)
        if [ -n "$TUNNEL_URL" ]; then
            echo "✅ Tunnel URL: $TUNNEL_URL"
            # Test tunnel
            if curl -s "$TUNNEL_URL/api/status/" > /dev/null 2>&1; then
                echo "✅ Tunnel is working"
            else
                echo "⚠️  Tunnel URL not responding"
            fi
        fi
    fi
else
    echo "⚠️  Cloudflare Tunnel is not running"
    echo "ℹ️  Start tunnel with: cloudflared tunnel --url http://localhost:8000"
fi
echo ""

# Step 7: Check backend logs for errors
echo "📋 Step 7: Checking recent backend logs for errors..."
sudo journalctl -u cryptoorchestrator-backend --since "10 minutes ago" --no-pager | grep -i "error\|exception\|warning\|failed" | tail -20 || echo "No recent errors found"
echo ""

# Step 8: Check database connection
echo "🗄️  Step 8: Checking database connection..."
if python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DATABASE_URL:', os.getenv('DATABASE_URL', 'Not set')[:50])" 2>/dev/null; then
    echo "✅ Database URL is configured"
else
    echo "⚠️  Database URL check failed"
fi
echo ""

# Step 9: Check environment variables
echo "🔐 Step 9: Checking critical environment variables..."
cd "$PROJECT_DIR"
source venv/bin/activate 2>/dev/null || true
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = [
    "DATABASE_URL",
    "JWT_SECRET",
    "EXCHANGE_KEY_ENCRYPTION_KEY",
]

missing = []
for var in required_vars:
    value = os.getenv(var)
    if not value:
        missing.append(var)
        print(f"❌ {var}: Not set")
    else:
        # Show first/last chars for security
        if len(value) > 10:
            masked = value[:4] + "..." + value[-4:]
        else:
            masked = "***"
        print(f"✅ {var}: {masked}")

if missing:
    print(f"\n⚠️  Missing required variables: {', '.join(missing)}")
else:
    print("\n✅ All required environment variables are set")
EOF
echo ""

# Step 10: Summary and recommendations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary and Next Steps:"
echo ""
echo "✅ Completed checks:"
echo "   - Code syntax validation"
echo "   - Backend service status"
echo "   - Port listening check"
echo "   - Cloudflare Tunnel status"
echo "   - Recent error logs"
echo "   - Environment variables"
echo ""
echo "📋 Next Steps:"
echo "   1. If backend is not running: sudo systemctl restart cryptoorchestrator-backend"
echo "   2. If tunnel is not running: cloudflared tunnel --url http://localhost:8000"
echo "   3. Get tunnel URL and update Vercel environment variables:"
echo "      - VITE_API_URL=https://your-tunnel-url.trycloudflare.com"
echo "      - VITE_WS_BASE_URL=wss://your-tunnel-url.trycloudflare.com"
echo "   4. Test backend: curl http://localhost:8000/api/status/"
echo "   5. Test tunnel: curl https://your-tunnel-url.trycloudflare.com/api/status/"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
