# Deployment Fix Steps

**Date:** January 2, 2026  
**Issue:** Disk space full, Docker build failing

---

## Step 1: Clean Up Disk Space

```bash
cd /home/labarcodez/CryptoOrchestrator

# Run cleanup script
chmod +x scripts/deployment/fix-disk-space.sh
./scripts/deployment/fix-disk-space.sh

# Or manually:
sudo docker system prune -a -f --volumes
```

**Expected:** Free up 5-10GB of space

---

## Step 2: Pull Latest Changes (with optimized Dockerfile)

```bash
cd /home/labarcodez/CryptoOrchestrator
git pull
```

**This will get:**
- `Dockerfile.optimized` (faster builds)
- `requirements-base.txt` (core deps)
- `requirements-ml.txt` (ML deps, optional)
- Updated `docker-compose.yml` (uses optimized Dockerfile)

---

## Step 3: Enable BuildKit

```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Add to ~/.bashrc for persistence
echo 'export DOCKER_BUILDKIT=1' >> ~/.bashrc
echo 'export COMPOSE_DOCKER_CLI_BUILD=1' >> ~/.bashrc
```

---

## Step 4: Start Services (Without ML Dependencies)

```bash
cd /home/labarcodez/CryptoOrchestrator

# Start only essential services (backend, postgres, redis)
# Skip celery-worker and celery-beat for now to save space
sudo DOCKER_BUILDKIT=1 docker-compose up -d postgres redis backend
```

**This will:**
- Use `Dockerfile.optimized` (faster builds)
- Build without ML dependencies (saves ~4GB)
- Use BuildKit cache mounts (faster rebuilds)

---

## Step 5: Verify Services

```bash
# Check all services are running
sudo docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check backend logs
sudo docker-compose logs backend --tail 50
```

**Expected:**
- ✅ All services show "Up" status
- ✅ Health endpoint returns `{"status":"healthy","database":"healthy"}`
- ✅ No errors in logs

---

## Step 6: (Optional) Add Celery Services Later

Once everything is working and you have more disk space:

```bash
# Start celery services
sudo DOCKER_BUILDKIT=1 docker-compose up -d celery-worker celery-beat
```

---

## Troubleshooting

### Still Out of Disk Space?

```bash
# Check disk usage
df -h

# Check Docker disk usage
sudo docker system df

# Remove more aggressively
sudo docker system prune -a -f --volumes --filter "until=24h"
```

### Build Still Fails?

```bash
# Try building manually to see errors
sudo DOCKER_BUILDKIT=1 docker build \
  -f Dockerfile.optimized \
  --build-arg INSTALL_ML_DEPS=false \
  -t cryptoorchestrator:test \
  .

# Check build logs
sudo docker-compose build --no-cache backend 2>&1 | tee build.log
```

### Services Won't Start?

```bash
# Check for port conflicts
sudo netstat -tulpn | grep -E "8000|5432|6379"

# Remove old containers
sudo docker-compose down
sudo docker-compose up -d
```

---

## Quick Command Summary

```bash
# 1. Clean up
sudo docker system prune -a -f --volumes

# 2. Pull changes
git pull

# 3. Enable BuildKit
export DOCKER_BUILDKIT=1

# 4. Start services
sudo DOCKER_BUILDKIT=1 docker-compose up -d postgres redis backend

# 5. Check status
sudo docker-compose ps
curl http://localhost:8000/health
```

---

**Next Steps After Deployment Works:**
1. Test the optimized Docker build
2. Monitor disk space
3. Add celery services if needed
4. Consider ML dependencies if features require them
