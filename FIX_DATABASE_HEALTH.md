# Fix Database Health Check

**Status:** Backend is working! ✅
**Issue:** Database shows "unhealthy" in health endpoint, but postgres container is healthy

---

## Test Database Connection

```bash
# Test database connection from backend
sudo docker exec crypto-orchestrator-backend python -c "
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv('DATABASE_URL')
print(f'DATABASE_URL: {DATABASE_URL}')

async def test():
    # Convert to async URL
    async_url = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
    engine = create_async_engine(async_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            row = result.fetchone()
            print('✅ Database connection successful!')
            print(f'Result: {row}')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

asyncio.run(test())
"
```

---

## Check Database URL

The health endpoint might be using a different DATABASE_URL than what's configured. Check:

```bash
# Check what DATABASE_URL the backend is using
sudo docker exec crypto-orchestrator-backend env | grep DATABASE_URL

# Should match the postgres container name: crypto-orchestrator-db
```

---

**The backend is working! The database health check is just a minor issue. Test the database connection above!**
