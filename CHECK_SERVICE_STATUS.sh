#!/bin/bash
# Check backend service status and logs

echo "🔍 Checking backend service status..."
echo ""

# Check if service is running
if systemctl is-active --quiet cryptoorchestrator-backend; then
    echo "✅ Service is active"
else
    echo "❌ Service is not active"
fi

echo ""
echo "📋 Service status:"
sudo systemctl status cryptoorchestrator-backend --no-pager -l | head -30

echo ""
echo "📋 Recent logs (last 50 lines):"
tail -50 ~/CryptoOrchestrator/logs/app.log 2>/dev/null || echo "Log file not found or empty"

echo ""
echo "📋 Journal logs (last 30 lines):"
sudo journalctl -u cryptoorchestrator-backend -n 30 --no-pager

echo ""
echo "🔍 Checking if port 8000 is listening:"
sudo ss -tlnp | grep 8000 || echo "Port 8000 is not listening"

echo ""
echo "🔍 Checking for Python processes:"
ps aux | grep -E "uvicorn|python.*server_fastapi" | grep -v grep || echo "No backend processes found"

echo ""
echo "⏳ Waiting 10 seconds and testing endpoint again..."
sleep 10

echo ""
echo "🧪 Testing /health endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:8000/health || echo "Connection failed"

echo ""
echo "🧪 Testing /api/status/ endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:8000/api/status/ || echo "Connection failed"
