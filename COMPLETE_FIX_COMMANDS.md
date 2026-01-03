# Complete Fix Commands - Run These on Your VM

**Date:** January 2, 2026  
**Purpose:** Fix Redis and Backend startup issues

---

## Step 1: Pull Latest Changes

```bash
cd /home/labarcodez/CryptoOrchestrator
git pull
```

This will get:
- ✅ Fixed Redis configuration (works without password)
- ✅ Fixed backend healthcheck (uses Python instead of curl)

---

## Step 2: Stop and Remove Problematic Containers

```bash
# Stop everything
sudo docker-compose down

# Remove Redis container (to start fresh)
sudo docker rm -f crypto-orchestrator-redis 2>/dev/null || true

# Remove backend container if it exists
sudo docker rm -f crypto-orchestrator-backend 2>/dev/null || true
```

---

## Step 3: Start Services in Order

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Start postgres first
sudo DOCKER_BUILDKIT=1 docker-compose up -d postgres

# Wait for postgres to be healthy
sleep 5

# Start redis
sudo DOCKER_BUILDKIT=1 docker-compose up -d redis

# Wait for redis to be healthy
sleep 10

# Check redis is working
sudo docker exec crypto-orchestrator-redis redis-cli ping
# Should return: PONG

# Start backend
sudo DOCKER_BUILDKIT=1 docker-compose up -d backend

# Wait a moment
sleep 5
```

---

## Step 4: Verify Everything Works

```bash
# Check all services
sudo docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check backend logs
sudo docker-compose logs backend --tail 30
```

---

## Step 5: If Redis Still Fails

If Redis is still restarting, check logs:

```bash
# Check Redis logs
sudo docker logs crypto-orchestrator-redis --tail 50

# Try starting Redis manually to see errors
sudo docker run --rm -it \
  --name test-redis \
  redis:7-alpine \
  redis-server --appendonly yes
```

---

## All-in-One Command

```bash
cd /home/labarcodez/CryptoOrchestrator && \
git pull && \
sudo docker-compose down && \
sudo docker rm -f crypto-orchestrator-redis crypto-orchestrator-backend 2>/dev/null || true && \
export DOCKER_BUILDKIT=1 && \
export COMPOSE_DOCKER_CLI_BUILD=1 && \
sudo DOCKER_BUILDKIT=1 docker-compose up -d postgres && \
sleep 5 && \
sudo DOCKER_BUILDKIT=1 docker-compose up -d redis && \
sleep 10 && \
sudo docker exec crypto-orchestrator-redis redis-cli ping && \
sudo DOCKER_BUILDKIT=1 docker-compose up -d backend && \
sleep 5 && \
sudo docker-compose ps && \
curl http://localhost:8000/health
```

---

## What Was Fixed

1. **Redis Configuration:**
   - ✅ Only requires password if `REDIS_PASSWORD` is set
   - ✅ Healthcheck works with or without password
   - ✅ Added start_period for initialization

2. **Backend Healthcheck:**
   - ✅ Changed from `curl` to Python (curl not in optimized image)
   - ✅ Uses Python's urllib which is always available

3. **Service Dependencies:**
   - ✅ Start services in order (postgres → redis → backend)
   - ✅ Wait for each service to be ready

---

**Run the commands above and share the output!**
