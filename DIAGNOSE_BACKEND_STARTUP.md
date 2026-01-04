# Diagnose Backend Startup Issue

**Problem:** Backend stuck in "starting" status, healthcheck failing

---

## Step 1: Check Backend Logs (Correct Syntax)

```bash
# Correct syntax for docker-compose logs
sudo docker-compose logs --tail 100 backend

# Or use docker logs directly
sudo docker logs crypto-orchestrator-backend --tail 100
```

---

## Step 2: Test Healthcheck Manually

```bash
# Test the healthcheck command manually
sudo docker exec crypto-orchestrator-backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz').read()"

# If that fails, test if Python can reach the endpoint
sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:8000/healthz', timeout=5)
    print('Status:', response.status)
    print('Response:', response.read().decode())
except Exception as e:
    print('Error:', e)
"
```

---

## Step 3: Check if Backend is Actually Running

```bash
# Check if uvicorn process is running
sudo docker exec crypto-orchestrator-backend ps aux | grep uvicorn

# Check if port 8000 is listening
sudo docker exec crypto-orchestrator-backend netstat -tuln | grep 8000
# Or
sudo docker exec crypto-orchestrator-backend ss -tuln | grep 8000
```

---

## Step 4: Test Health Endpoints Directly

```bash
# Test from inside container
sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
import json

try:
    # Test /healthz
    response = urllib.request.urlopen('http://localhost:8000/healthz', timeout=5)
    print('✅ /healthz:', response.read().decode())
except Exception as e:
    print('❌ /healthz failed:', e)

try:
    # Test /health
    response = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
    print('✅ /health:', response.read().decode())
except Exception as e:
    print('❌ /health failed:', e)
"
```

---

## Step 5: Check for Startup Errors

```bash
# Check for import errors or startup failures
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -i error | tail -20

# Check for database connection errors
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -i "database\|postgres\|connection" | tail -20
```

---

## Step 6: Simplify Healthcheck (Temporary Fix)

If the healthcheck is the issue, we can temporarily use a simpler one:

Edit `docker-compose.yml` backend healthcheck to:
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import socket; s=socket.socket(); s.connect(('localhost', 8000)); s.close()"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

Or even simpler - just check if process is running:
```yaml
healthcheck:
  test: ["CMD", "pgrep", "-f", "uvicorn"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

---

**Run Step 1 first and share the backend logs output!**
