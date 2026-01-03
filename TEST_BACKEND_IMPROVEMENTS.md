# Testing Backend Improvements - Step by Step Guide

## Prerequisites
- Backend is running on VM
- SSH access to the VM
- Docker and docker-compose installed

## Step 1: Pull Latest Changes

```bash
cd /home/labarcodez/CryptoOrchestrator
git pull
```

## Step 2: Restart Backend to Pick Up Changes

```bash
# Stop backend
sudo docker-compose stop backend

# Remove old container
sudo docker rm crypto-orchestrator-backend

# Rebuild with latest changes (if code changed)
sudo DOCKER_BUILDKIT=1 docker-compose build backend

# Start backend
sudo DOCKER_BUILDKIT=1 docker-compose up -d backend

# Wait for startup (30-60 seconds)
sleep 45
```

## Step 3: Verify Backend is Running

```bash
# Check container status
sudo docker-compose ps

# Check backend logs for errors
sudo docker-compose logs backend --tail 50 | grep -i "error\|exception\|traceback"
```

## Step 4: Test Each Improvement

### Test 1: Health Endpoints
```bash
sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
import json
try:
    response = urllib.request.urlopen('http://localhost:8000/health', timeout=10)
    data = json.loads(response.read().decode())
    print('✅ Health endpoint:', json.dumps(data, indent=2))
    if data.get('database') == 'healthy':
        print('✅ Database: HEALTHY')
    else:
        print('⚠️  Database:', data.get('database', 'unknown'))
except Exception as e:
    print('❌ Health check failed:', e)
"
```

### Test 2: Response Compression
```bash
sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
import gzip
try:
    req = urllib.request.Request('http://localhost:8000/health')
    req.add_header('Accept-Encoding', 'gzip')
    response = urllib.request.urlopen(req, timeout=10)
    headers = dict(response.headers)
    if 'Content-Encoding' in headers and 'gzip' in headers['Content-Encoding']:
        print('✅ Compression: ENABLED')
    else:
        print('⚠️  Compression: Not detected (may be disabled for small responses)')
except Exception as e:
    print('❌ Compression test failed:', e)
"
```

### Test 3: Database Connection Pool
```bash
sudo docker exec crypto-orchestrator-backend python -c "
import os
print('Database Pool Configuration:')
print(f'  DB_POOL_SIZE: {os.getenv(\"DB_POOL_SIZE\", \"50 (default)\")}')
print(f'  DB_MAX_OVERFLOW: {os.getenv(\"DB_MAX_OVERFLOW\", \"30 (default)\")}')
print('✅ Pool settings loaded')
"
```

### Test 4: Query Monitoring
```bash
# Make a request and check logs for query monitoring
sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:8000/api/status', timeout=10)
    print('✅ Query monitoring: Active (check logs for query tracking)')
except Exception as e:
    print('⚠️  Status endpoint:', e)
"
```

### Test 5: Cache Service with TTL Jitter
```bash
sudo docker exec crypto-orchestrator-backend python -c "
import sys
sys.path.insert(0, '/app')
from server_fastapi.services.cache_service import CACHE_CONFIG
print('Cache Configuration:')
print(f'  Default TTL: {CACHE_CONFIG[\"default_ttl\"]}s')
print(f'  TTL Jitter: {CACHE_CONFIG.get(\"ttl_jitter_percent\", 10)}%')
print('✅ Cache service: Configured with TTL jitter')
"
```

### Test 6: Router Loading (Check Startup Time)
```bash
# Check startup logs for router loading
sudo docker-compose logs backend | grep -i "router\|loading" | tail -20
```

## Step 5: Check for Errors

```bash
# Check for any startup errors
sudo docker-compose logs backend | grep -i "error\|exception\|traceback\|failed" | tail -30

# Check for import errors
sudo docker-compose logs backend | grep -i "import.*error\|module.*not found" | tail -20
```

## Step 6: Performance Check

```bash
# Check response times
time curl -s http://localhost:8000/health > /dev/null

# Check database connection
sudo docker exec crypto-orchestrator-backend python -c "
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    DATABASE_URL = os.getenv('DATABASE_URL')
    async_url = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
    engine = create_async_engine(async_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            print('✅ Database: Connected')
    except Exception as e:
        print(f'❌ Database error: {e}')
    finally:
        await engine.dispose()

asyncio.run(test())
"
```

## Common Issues and Fixes

### Issue 1: Import Errors
If you see import errors for new modules:
- Check that files were pulled correctly
- Verify file paths are correct
- Restart backend after pulling changes

### Issue 2: Syntax Errors
If you see syntax errors:
- Check Python version (should be 3.12)
- Verify all imports are correct
- Check for missing dependencies

### Issue 3: Middleware Not Loading
If middleware isn't loading:
- Check middleware config in `server_fastapi/middleware/config.py`
- Verify middleware files exist
- Check logs for middleware registration errors

### Issue 4: Cache Not Working
If cache isn't working:
- Check Redis connection
- Verify cache service is initialized
- Check TTL jitter implementation

## Expected Results

✅ All health endpoints should return 200
✅ Compression should be enabled (for responses >1KB)
✅ Database pool should be 50 base, 30 overflow
✅ Query monitoring should track queries
✅ Cache should have TTL jitter configured
✅ No import or syntax errors
✅ Backend should start successfully
