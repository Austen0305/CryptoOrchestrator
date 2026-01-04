#!/bin/bash
# Comprehensive Backend Startup Fix Script
# Diagnoses and fixes systemd timeout and startup issues

set -e

echo "🔧 Backend Startup Fix Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PROJECT_DIR="/home/labarcodez/CryptoOrchestrator"
cd "$PROJECT_DIR"

echo "📋 Step 1: Checking for stuck processes..."
echo ""

# Find all uvicorn/python processes related to the backend
STUCK_PIDS=$(ps aux | grep -E "uvicorn.*server_fastapi|python.*server_fastapi" | grep -v grep | awk '{print $2}' || true)

if [ -n "$STUCK_PIDS" ]; then
    echo "⚠️  Found stuck processes: $STUCK_PIDS"
    echo "$STUCK_PIDS" | xargs -r sudo kill -9 2>/dev/null || true
    echo "✅ Killed stuck processes"
    sleep 2
else
    echo "✅ No stuck processes found"
fi

echo ""
echo "📋 Step 2: Checking port 8000..."
PORT_8000=$(sudo lsof -i :8000 2>/dev/null | grep LISTEN || true)
if [ -n "$PORT_8000" ]; then
    echo "⚠️  Port 8000 is in use:"
    echo "$PORT_8000"
    PORT_PID=$(echo "$PORT_8000" | awk '{print $2}' | head -1)
    if [ -n "$PORT_PID" ]; then
        echo "Killing process $PORT_PID using port 8000..."
        sudo kill -9 "$PORT_PID" 2>/dev/null || true
        sleep 2
    fi
else
    echo "✅ Port 8000 is free"
fi

echo ""
echo "📋 Step 3: Stopping service (if running)..."
sudo systemctl stop cryptoorchestrator-backend.service 2>/dev/null || true
sleep 3

echo ""
echo "📋 Step 4: Service status..."
sudo systemctl status cryptoorchestrator-backend.service --no-pager -l | head -30 || true

echo ""
echo "📋 Step 5: Recent service logs (last 50 lines, unfiltered)..."
sudo journalctl -u cryptoorchestrator-backend.service -n 50 --no-pager || true

echo ""
echo "📋 Step 6: Checking service file configuration..."
if [ -f "/etc/systemd/system/cryptoorchestrator-backend.service" ]; then
    echo "Service file exists. Checking timeout settings:"
    grep -E "Timeout|KillMode|KillSignal" /etc/systemd/system/cryptoorchestrator-backend.service || echo "No timeout settings found"
else
    echo "⚠️  Service file not found at /etc/systemd/system/cryptoorchestrator-backend.service"
fi

echo ""
echo "📋 Step 7: Reloading systemd daemon..."
sudo systemctl daemon-reload

echo ""
echo "📋 Step 8: Starting service..."
sudo systemctl start cryptoorchestrator-backend.service
sleep 5

echo ""
echo "📋 Step 9: Checking service status after start..."
if sudo systemctl is-active --quiet cryptoorchestrator-backend.service; then
    echo "✅ Service is ACTIVE"
else
    echo "❌ Service is NOT active"
fi

sudo systemctl status cryptoorchestrator-backend.service --no-pager -l | head -40 || true

echo ""
echo "📋 Step 10: Checking port 8000 after start..."
sleep 3
if sudo lsof -i :8000 2>/dev/null | grep -q LISTEN; then
    echo "✅ Port 8000 is now listening"
else
    echo "❌ Port 8000 is still not listening"
fi

echo ""
echo "📋 Step 11: Testing backend endpoint..."
sleep 2
if curl -s http://localhost:8000/api/status/ > /dev/null 2>&1; then
    echo "✅ Backend is responding!"
    curl http://localhost:8000/api/status/
else
    echo "❌ Backend is not responding"
    echo ""
    echo "📋 Step 12: Latest error logs..."
    sudo journalctl -u cryptoorchestrator-backend.service -n 100 --no-pager | tail -50
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Diagnostic complete"
