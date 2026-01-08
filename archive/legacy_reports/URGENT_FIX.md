# 🚨 URGENT: Stop Build and Fix

**The build is using the OLD Dockerfile and installing ML dependencies!**

---

## ⚠️ IMMEDIATE ACTION REQUIRED

### Step 1: STOP THE BUILD NOW

```bash
# Press Ctrl+C in the terminal to stop the build
# Then run:
sudo docker-compose down
sudo docker ps -a | grep build | awk '{print $1}' | xargs -r sudo docker rm -f
```

### Step 2: Clean Up Disk Space (CRITICAL)

```bash
# Aggressive cleanup
sudo docker system prune -a -f --volumes
sudo docker builder prune -a -f

# Check space
df -h
```

### Step 3: Pull Latest Changes

```bash
cd /home/labarcodez/CryptoOrchestrator
git pull
```

**This will get:**
- ✅ Updated `docker-compose.yml` (uses optimized Dockerfile)
- ✅ `Dockerfile.optimized` (faster, no ML by default)
- ✅ `requirements-base.txt` (core deps only)

### Step 4: Start ONLY Essential Services (NO Celery)

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Start ONLY backend, postgres, redis (skip celery-worker!)
sudo DOCKER_BUILDKIT=1 docker-compose up -d postgres redis backend
```

**Why skip celery-worker?**
- It's not essential for basic functionality
- It's what's currently failing
- We can add it later once everything works

---

## 🔍 Why It's Still Slow

The build is still:
1. ❌ Using old `Dockerfile` (not optimized)
2. ❌ Installing ALL ML dependencies (TensorFlow, PyTorch, NVIDIA CUDA)
3. ❌ Building celery-worker (which you don't need right now)
4. ❌ Running out of disk space

---

## ✅ What Will Fix It

1. ✅ Use `Dockerfile.optimized` (already updated in docker-compose.yml)
2. ✅ Build WITHOUT ML dependencies (`INSTALL_ML_DEPS=false`)
3. ✅ Skip celery-worker (not essential)
4. ✅ Clean disk space first

---

## 📋 Complete Command Sequence

```bash
# 1. Stop everything
sudo docker-compose down
sudo docker ps -a | grep -E "build|celery" | awk '{print $1}' | xargs -r sudo docker rm -f

# 2. Clean up
sudo docker system prune -a -f --volumes
sudo docker builder prune -a -f

# 3. Pull changes
cd /home/labarcodez/CryptoOrchestrator
git pull

# 4. Enable BuildKit
export DOCKER_BUILDKIT=1

# 5. Start ONLY essential services
sudo DOCKER_BUILDKIT=1 docker-compose up -d postgres redis backend

# 6. Check status
sudo docker-compose ps
curl http://localhost:8000/health
```

---

## ⏱️ Expected Build Time

- **Old way (current):** 20-30+ minutes, fails with disk space
- **New way (optimized, no ML, no celery):** 5-7 minutes, succeeds

---

**DO THIS NOW:** Stop the build (Ctrl+C) and run the commands above!
