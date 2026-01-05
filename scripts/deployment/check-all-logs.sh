#!/bin/bash
# Comprehensive Log Checking Script
# Check all logs to identify errors and warnings

set -e

echo "🔍 Comprehensive Log Checker - Finding All Errors and Warnings"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PROJECT_DIR="/home/labarcodez/CryptoOrchestrator"
cd "$PROJECT_DIR"

# Check if using systemd (not Docker)
if systemctl list-units | grep -q cryptoorchestrator-backend; then
    echo "📋 Using systemd service (not Docker)"
    echo ""
    
    echo "🔍 Step 1: Checking backend service status..."
    sudo systemctl status cryptoorchestrator-backend --no-pager -l | head -30
    echo ""
    
    echo "📋 Step 2: Recent backend logs (last 50 lines)..."
    sudo journalctl -u cryptoorchestrator-backend -n 50 --no-pager
    echo ""
    
    echo "❌ Step 3: Errors in backend logs (last 100 lines)..."
    sudo journalctl -u cryptoorchestrator-backend -n 100 --no-pager | grep -i "error\|exception\|failed\|traceback" || echo "No errors found in recent logs"
    echo ""
    
    echo "⚠️  Step 4: Warnings in backend logs (last 100 lines)..."
    sudo journalctl -u cryptoorchestrator-backend -n 100 --no-pager | grep -i "warning" || echo "No warnings found in recent logs"
    echo ""
    
    echo "📋 Step 5: Cloudflare Tunnel logs (if running)..."
    if systemctl list-units | grep -q cloudflare-tunnel; then
        sudo journalctl -u cloudflare-tunnel -n 50 --no-pager | tail -20
    else
        echo "Cloudflare Tunnel service not running"
    fi
    echo ""
    
    echo "📋 Step 6: Application log files..."
    if [ -d "logs" ]; then
        echo "Recent app.log entries:"
        tail -50 logs/app.log 2>/dev/null || echo "app.log not found"
        echo ""
        echo "Recent fastapi.log entries:"
        tail -50 logs/fastapi.log 2>/dev/null || echo "fastapi.log not found"
    else
        echo "logs directory not found"
    fi
    echo ""
    
else
    echo "📦 Using Docker (checking containers)..."
    echo ""
    
    echo "🔍 Step 1: Checking Docker containers..."
    docker ps -a | grep -E "crypto|backend" || echo "No backend containers found"
    echo ""
    
    echo "📋 Step 2: Backend container logs (last 100 lines)..."
    CONTAINER_NAME=$(docker ps -a --format "{{.Names}}" | grep -E "crypto|backend" | head -1)
    if [ -n "$CONTAINER_NAME" ]; then
        docker logs --tail 100 "$CONTAINER_NAME" 2>&1
        echo ""
        
        echo "❌ Step 3: Errors in container logs..."
        docker logs "$CONTAINER_NAME" 2>&1 | grep -i "error\|exception\|failed\|traceback" | tail -20 || echo "No errors found"
        echo ""
        
        echo "⚠️  Step 4: Warnings in container logs..."
        docker logs "$CONTAINER_NAME" 2>&1 | grep -i "warning" | tail -20 || echo "No warnings found"
    else
        echo "Backend container not found"
    fi
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Log check complete!"
echo ""
echo "Next steps:"
echo "1. Review errors above"
echo "2. Fix any issues found"
echo "3. Restart backend: sudo systemctl restart cryptoorchestrator-backend"
echo "4. Check logs again to verify fixes"
