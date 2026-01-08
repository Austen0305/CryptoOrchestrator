# Fix HTTP 500 Error

**Problem:** Backend is running but returning HTTP 500 errors

---

## Step 1: Check Backend Error Logs

```bash
# Get recent errors
sudo docker logs crypto-orchestrator-backend 2>&1 | tail -100 | grep -i "error\|exception\|traceback" | tail -30

# Check what happens when /health is called
sudo docker logs crypto-orchestrator-backend 2>&1 | tail -50

# Check for database connection errors
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -i "database\|postgres\|connection" | tail -20
```

---

## Step 2: Test Database Connection

```bash
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

---

## Step 3: Check Health Endpoint Code

The /health endpoint might be failing due to database connection. Let's see the actual error:

```bash
# Get the full error when calling /health
sudo docker exec crypto-orchestrator-backend python -c "
import urllib.request
import json
try:
    response = urllib.request.urlopen('http://localhost:8000/health')
    print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.reason}')
    print('Response:', e.read().decode())
except Exception as e:
    print(f'Error: {e}')
"
```

---

**Run Step 1 first to see the actual error!**
