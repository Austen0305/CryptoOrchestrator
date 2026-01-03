# Fix Redis Restarting Issue

**Problem:** Redis container is restarting, preventing backend from starting.

---

## Step 1: Check Redis Logs

```bash
# Check why Redis is failing
sudo docker-compose logs redis --tail 50

# Check Redis container details
sudo docker inspect crypto-orchestrator-redis | grep -A 20 "State"
```

---

## Step 2: Common Redis Issues

### Issue 1: Redis Password Configuration

If `REDIS_PASSWORD` is set but Redis command doesn't match:

```bash
# Check if REDIS_PASSWORD is set
echo $REDIS_PASSWORD

# Check docker-compose.yml redis command
grep -A 5 "redis:" docker-compose.yml
```

### Issue 2: Redis Volume Permissions

```bash
# Check Redis volume
sudo docker volume ls | grep redis

# Check permissions
sudo ls -la $(sudo docker volume inspect cryptoorchestrator_redis_data | grep Mountpoint | cut -d'"' -f4)
```

---

## Step 3: Quick Fix - Restart Redis

```bash
# Stop Redis
sudo docker-compose stop redis

# Remove Redis container
sudo docker rm crypto-orchestrator-redis

# Start Redis fresh
sudo docker-compose up -d redis

# Check logs
sudo docker-compose logs -f redis
```

---

## Step 4: Alternative - Start Redis Without Password

If password is causing issues, temporarily remove it:

Edit `docker-compose.yml` redis service:
```yaml
redis:
  # ... other config ...
  command: redis-server --appendonly yes  # Remove --requirepass
```

Then:
```bash
sudo docker-compose up -d redis
```

---

## Step 5: Check Redis Health

```bash
# Test Redis connection
sudo docker exec crypto-orchestrator-redis redis-cli ping

# Should return: PONG
```

---

## Step 6: Once Redis is Fixed, Start Backend

```bash
# Start backend
sudo docker-compose up -d backend

# Check status
sudo docker-compose ps

# Check backend logs
sudo docker-compose logs backend --tail 50
```

---

**Run these commands and share the Redis logs output!**
