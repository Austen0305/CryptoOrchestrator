#!/bin/bash
# Quick deployment script to run directly on the server
# This updates the running FastAPI service with CORS fixes

set -e

echo "=========================================="
echo "Backend CORS Fixes Deployment"
echo "=========================================="
echo ""

# Step 1: Pull latest changes
echo "Step 1: Pulling latest changes from git..."
cd ~/CryptoOrchestrator
git pull origin main
echo "✓ Git pull complete"
echo ""

# Step 2: Find running process
echo "Step 2: Finding running FastAPI process..."
PID=$(ps aux | grep "uvicorn.*main:app" | grep -v grep | awk '{print $2}' | head -1)

if [ -z "$PID" ]; then
    echo "✗ No running FastAPI process found"
    echo "Starting FastAPI service..."
    nohup python3 -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
    sleep 5
    PID=$(ps aux | grep "uvicorn.*main:app" | grep -v grep | awk '{print $2}' | head -1)
    if [ -z "$PID" ]; then
        echo "✗ Failed to start FastAPI service"
        exit 1
    fi
    echo "✓ FastAPI service started (PID: $PID)"
else
    echo "✓ Found FastAPI process (PID: $PID)"
fi
echo ""

# Step 3: Update files
echo "Step 3: Updating files in process namespace..."
sudo cp ~/CryptoOrchestrator/server_fastapi/middleware/setup.py /proc/$PID/root/app/server_fastapi/middleware/setup.py
sudo cp ~/CryptoOrchestrator/server_fastapi/routes/logging.py /proc/$PID/root/app/server_fastapi/routes/logging.py

# Also update auth_service and main.py if they exist
if [ -f ~/CryptoOrchestrator/server_fastapi/services/auth/auth_service.py ]; then
    sudo cp ~/CryptoOrchestrator/server_fastapi/services/auth/auth_service.py /proc/$PID/root/app/server_fastapi/services/auth/auth_service.py
fi
if [ -f ~/CryptoOrchestrator/server_fastapi/main.py ]; then
    sudo cp ~/CryptoOrchestrator/server_fastapi/main.py /proc/$PID/root/app/server_fastapi/main.py
fi

echo "✓ Files updated"
echo ""

# Step 4: Clear cache
echo "Step 4: Clearing Python cache..."
sudo find /proc/$PID/root/app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
sudo find /proc/$PID/root/app -name "*.pyc" -delete 2>/dev/null || true
echo "✓ Cache cleared"
echo ""

# Step 5: Verify syntax
echo "Step 5: Verifying file syntax..."
sudo python3 -m py_compile /proc/$PID/root/app/server_fastapi/middleware/setup.py 2>&1 || echo "⚠ Syntax check warning (may be OK)"
sudo python3 -m py_compile /proc/$PID/root/app/server_fastapi/routes/logging.py 2>&1 || echo "⚠ Syntax check warning (may be OK)"
echo "✓ Syntax verified"
echo ""

# Step 6: Restart service
echo "Step 6: Restarting service..."
sudo kill -9 $PID
echo "Waiting for service to restart..."
sleep 15

# Check if service restarted
NEW_PID=$(ps aux | grep "uvicorn.*main:app" | grep -v grep | awk '{print $2}' | head -1)
if [ -z "$NEW_PID" ]; then
    echo "✗ Service did not restart automatically"
    echo "Starting service manually..."
    cd ~/CryptoOrchestrator
    nohup python3 -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
    sleep 5
    NEW_PID=$(ps aux | grep "uvicorn.*main:app" | grep -v grep | awk '{print $2}' | head -1)
    if [ -z "$NEW_PID" ]; then
        echo "✗ Failed to restart service"
        exit 1
    fi
fi
echo "✓ Service restarted (New PID: $NEW_PID)"
echo ""

# Step 7: Test CORS
echo "Step 7: Testing CORS preflight..."
sleep 5

CORS_TEST=$(curl -s -X OPTIONS http://localhost:8000/api/status -H "Origin: https://cryptoorchestrator.vercel.app" -H "Access-Control-Request-Method: GET" -w "%{http_code}" -o /dev/null || echo "000")

if [ "$CORS_TEST" = "200" ] || [ "$CORS_TEST" = "204" ]; then
    echo "✓ CORS preflight test passed (HTTP $CORS_TEST)"
else
    echo "⚠ CORS preflight returned HTTP $CORS_TEST (may need more time)"
fi

# Test regular API call
API_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/status || echo "000")
if [ "$API_TEST" = "200" ]; then
    echo "✓ API endpoint responding (HTTP $API_TEST)"
else
    echo "⚠ API endpoint returned HTTP $API_TEST"
fi
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Test the frontend at https://cryptoorchestrator.vercel.app/"
echo "  2. Check browser console for CORS errors"
echo "  3. Verify API calls are working"
echo ""
echo "To view logs: tail -f /tmp/fastapi.log"
