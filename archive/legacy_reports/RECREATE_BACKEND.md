# Recreate Backend with Correct Environment Variable

**Problem:** Container is using old EXCHANGE_KEY_ENCRYPTION_KEY (23 chars, needs 32+)

---

## Step 1: Pull Latest docker-compose.yml

```bash
cd /home/labarcodez/CryptoOrchestrator
git pull
```

---

## Step 2: Recreate Backend Container

```bash
# Stop and remove backend
sudo docker-compose stop backend
sudo docker rm crypto-orchestrator-backend

# Recreate with new environment variables
sudo docker-compose up -d backend

# Wait for startup
sleep 15
```

---

## Step 3: Verify Environment Variable

```bash
# Check the value
sudo docker exec crypto-orchestrator-backend env | grep EXCHANGE_KEY_ENCRYPTION_KEY

# Should show: EXCHANGE_KEY_ENCRYPTION_KEY=change-me-in-production-use-32-byte-key-here-now
# (46 characters - long enough!)
```

---

## Step 4: Check if Backend Starts

```bash
# Check status
sudo docker-compose ps

# Check logs
sudo docker-compose logs --tail 30 backend | grep -i "uvicorn running\|startup\|error"

# Test health
curl http://localhost:8000/health
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
sudo docker exec crypto-orchestrator-backend env | grep EXCHANGE_KEY_ENCRYPTION_KEY && \
sudo docker-compose ps && \
curl http://localhost:8000/health
```

---

**Run these commands to fix the environment variable issue!**
