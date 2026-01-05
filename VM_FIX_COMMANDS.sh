#!/bin/bash
# Commands to run on the VM to fix and restart the backend

echo "🔍 Step 1: Checking how backend is running..."
echo ""

# Check for systemd services
echo "Checking systemd services:"
systemctl list-units --type=service | grep -i crypto || echo "No crypto services found in systemd"
echo ""

# Check for running processes
echo "Checking running processes:"
ps aux | grep -E "uvicorn|python.*server_fastapi" | grep -v grep || echo "No uvicorn processes found"
echo ""

# Check service files
echo "Checking service files:"
ls -la /etc/systemd/system/ | grep -i crypto || echo "No crypto service files found"
echo ""

# Check port 8000
echo "Checking port 8000:"
sudo ss -tlnp | grep 8000 || echo "Port 8000 not in use"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Step 2: Applying compression middleware fix..."
echo ""

cd ~/CryptoOrchestrator

# Check if the fix is already applied
if grep -q "trycloudflare.com.*in host" server_fastapi/middleware/compression.py 2>/dev/null; then
    echo "✅ Fix appears to already be applied!"
else
    echo "Applying fix..."
    # Create a Python script to apply the fix
    python3 << 'PYTHON_SCRIPT'
import re

file_path = 'server_fastapi/middleware/compression.py'

with open(file_path, 'r') as f:
    content = f.read()

# Check if fix is already applied
if 'trycloudflare.com.*in host' in content or 'Also check Host header' in content:
    print("Fix already applied!")
else:
    # Pattern to find and replace
    pattern = r'(is_behind_cloudflare = any\(\s+header in request\.headers for header in cloudflare_headers\s+\))\s+(\n\s+if is_behind_cloudflare:)'
    
    replacement = r'''\1
            
            # Also check Host header for Cloudflare tunnel domains
            if not is_behind_cloudflare:
                host = request.headers.get("host", "").lower()
                is_behind_cloudflare = (
                    "trycloudflare.com" in host or
                    "cloudflare.com" in host or
                    host.endswith(".trycloudflare.com") or
                    host.endswith(".cloudflare.com")
                )
            \2'''
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        # Backup original
        with open(file_path + '.backup', 'w') as f:
            f.write(content)
        
        # Write fixed version
        with open(file_path, 'w') as f:
            f.write(new_content)
        print("✅ Fix applied successfully!")
        print("Backup saved to: " + file_path + '.backup')
    else:
        print("⚠️  Could not automatically apply fix. Please apply manually.")
        print("See QUICK_FIX_ON_VM.md for manual instructions.")
PYTHON_SCRIPT
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Step 3: Restarting backend..."
echo ""

# Try different service names
SERVICE_STARTED=false

for service_name in "cryptoorchestrator-backend" "cryptoorchestrator-backend.service" "cryptoorchestrator.service"; do
    if systemctl list-units --type=service --all | grep -q "$service_name"; then
        echo "Found service: $service_name"
        sudo systemctl restart "$service_name"
        sleep 3
        if systemctl is-active --quiet "$service_name"; then
            echo "✅ Service $service_name restarted successfully!"
            SERVICE_STARTED=true
            sudo systemctl status "$service_name" --no-pager -l | head -15
            break
        fi
    fi
done

if [ "$SERVICE_STARTED" = false ]; then
    echo "⚠️  No systemd service found. Checking if backend is running manually..."
    BACKEND_PID=$(pgrep -f "uvicorn.*server_fastapi" | head -1)
    if [ -n "$BACKEND_PID" ]; then
        echo "Found backend process: $BACKEND_PID"
        echo "Killing process..."
        kill $BACKEND_PID
        sleep 2
    fi
    
    echo "Starting backend manually..."
    cd ~/CryptoOrchestrator
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    nohup python3 -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000 > logs/app.log 2>&1 &
    echo "Backend started in background. PID: $!"
    sleep 3
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Step 4: Testing endpoints..."
echo ""

# Test health endpoint
echo "Testing /health endpoint:"
curl -s http://localhost:8000/health | head -5 || echo "❌ Health endpoint failed"
echo ""

# Test status endpoint
echo "Testing /api/status/ endpoint:"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/status/)
if [ "$STATUS_CODE" = "200" ]; then
    echo "✅ Status endpoint returned 200 OK"
    curl -s http://localhost:8000/api/status/ | head -3
else
    echo "⚠️  Status endpoint returned HTTP $STATUS_CODE"
    curl -s http://localhost:8000/api/status/ | head -5
fi
echo ""

# Check logs for compression errors
echo "Checking logs for compression errors (last 20 lines):"
tail -20 logs/app.log 2>/dev/null | grep -i "compression" || echo "No compression-related log entries found"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Done! Check the results above."
echo ""
echo "If the status endpoint still returns 500, check logs:"
echo "  tail -100 logs/app.log"
echo "  sudo journalctl -u cryptoorchestrator-backend -n 100"
