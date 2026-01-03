# Fix Backend Health Check Issue

**Issue:** Backend container showing as "unhealthy"

---

## Step 1: Check Backend Logs

Run this on your VM:

```bash
sudo docker-compose logs backend --tail 50
```

Look for:
- Database connection errors
- Import errors
- Startup errors

---

## Step 2: Test Health Endpoints Manually

```bash
# Test /health endpoint
curl http://localhost:8000/health

# Test /healthz endpoint (used by healthcheck)
curl http://localhost:8000/healthz
```

---

## Step 3: Check Container Status

```bash
# Check container health status
sudo docker ps -a | grep backend

# Check healthcheck details
sudo docker inspect crypto-orchestrator-backend | grep -A 10 Health
```

---

## Step 4: Common Fixes

### Fix 1: Database Connection Issue

If database connection is failing:

```bash
# Check if postgres is running
sudo docker-compose ps postgres

# Check postgres logs
sudo docker-compose logs postgres --tail 20

# Test database connection from backend container
sudo docker exec crypto-orchestrator-backend python -c "
import asyncio
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv('DATABASE_URL')
print(f'DATABASE_URL: {DATABASE_URL}')

async def test():
    async_url = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
    engine = create_async_engine(async_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            print('✅ Database connection successful!')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
    finally:
        await engine.dispose()

asyncio.run(test())
"
```

### Fix 2: Healthcheck Endpoint Issue

If `/healthz` is not responding:

```bash
# Restart backend
sudo docker-compose restart backend

# Wait a moment
sleep 10

# Test again
curl http://localhost:8000/healthz
```

### Fix 3: Change Healthcheck to Use /health

If `/healthz` doesn't work, we can change the healthcheck to use `/health`:

Edit `docker-compose.yml`:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]  # Changed from /healthz
```

Then restart:
```bash
sudo docker-compose up -d backend
```

---

## Step 5: Restart Services

```bash
# Restart everything
sudo docker-compose restart

# Or restart just backend
sudo docker-compose restart backend

# Check status
sudo docker-compose ps
```

---

## Quick Diagnostic Commands

```bash
# Full diagnostic
echo "=== Container Status ==="
sudo docker-compose ps

echo ""
echo "=== Backend Logs (last 30 lines) ==="
sudo docker-compose logs backend --tail 30

echo ""
echo "=== Health Endpoint Test ==="
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health endpoint failed"

echo ""
echo "=== Healthz Endpoint Test ==="
curl -s http://localhost:8000/healthz | python3 -m json.tool || echo "Healthz endpoint failed"
```

---

**Run these commands on your VM and share the output!**
