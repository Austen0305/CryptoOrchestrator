#!/bin/bash
# Check startup errors in application logs

set -e

PROJECT_DIR="/home/labarcodez/CryptoOrchestrator"
cd "$PROJECT_DIR"

echo "🔍 Checking Application Startup Errors"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📋 Step 1: Checking if logs directory exists..."
if [ ! -d "logs" ]; then
    echo "⚠️  Logs directory doesn't exist. Creating it..."
    mkdir -p logs
    chmod 755 logs
    echo "✅ Logs directory created"
else
    echo "✅ Logs directory exists"
fi
echo ""

echo "📋 Step 2: Checking log file permissions..."
if [ -f "logs/app.log" ]; then
    ls -la logs/app.log
    echo ""
    echo "📋 Step 3: Recent application logs (last 100 lines)..."
    tail -100 logs/app.log 2>/dev/null || echo "Log file is empty or cannot be read"
else
    echo "⚠️  Log file doesn't exist yet"
    echo "📋 Step 3: Checking if process is running..."
fi
echo ""

echo "📋 Step 4: Checking for Python process..."
ps aux | grep -E "uvicorn|python.*server_fastapi" | grep -v grep || echo "No uvicorn process found"
echo ""

echo "📋 Step 5: Trying to manually start backend to see errors..."
echo "Running: source venv/bin/activate && python3 -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000 --timeout-graceful-shutdown 60"
echo ""
echo "Press Ctrl+C after a few seconds to stop..."
timeout 10 bash -c "source venv/bin/activate && python3 -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000 --timeout-graceful-shutdown 60 2>&1" || true

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
