# Final Fix for Backend Startup

**Issues Found:**
1. `EXCHANGE_KEY_ENCRYPTION_KEY is too short` - Container using old env var
2. Syntax error in structured_logging_enhanced.py - Fixed but needs to be pulled

---

## Step 1: Pull Latest Code

```bash
cd /home/labarcodez/CryptoOrchestrator
git pull
```

This will get:
- ✅ Fixed `structured_logging_enhanced.py` (async function)
- ✅ Updated `docker-compose.yml` (longer encryption key)

---

## Step 2: Restart Backend to Pick Up Changes

```bash
# Stop backend
sudo docker-compose stop backend

# Remove container to force recreation with new env vars
sudo docker rm crypto-orchestrator-backend

# Start backend (will recreate with new env vars and code)
sudo docker-compose up -d backend

# Wait a moment
sleep 10
```

---

## Step 3: Check if It Works

```bash
# Check status
sudo docker-compose ps

# Check logs for errors
sudo docker-compose logs --tail 30 backend | grep -i "error\|startup\|uvicorn running"

# Test health endpoint
curl http://localhost:8000/health
```

---

## Step 4: If Still Failing - Check Environment Variable

```bash
# Check what EXCHANGE_KEY_ENCRYPTION_KEY the container is using
sudo docker exec crypto-orchestrator-backend env | grep EXCHANGE_KEY_ENCRYPTION_KEY

# Should show: EXCHANGE_KEY_ENCRYPTION_KEY=change-me-in-production-use-32-byte-key-here
# (42 characters - long enough!)
```

---

## All-in-One Command

```bash
cd /home/labarcodez/CryptoOrchestrator && \
git pull && \
sudo docker-compose stop backend && \
sudo docker rm crypto-orchestrator-backend && \
sudo docker-compose up -d backend && \
sleep 15 && \
sudo docker-compose ps && \
curl http://localhost:8000/health
```

---

**The fixes are now pushed. Pull and restart the backend!**
