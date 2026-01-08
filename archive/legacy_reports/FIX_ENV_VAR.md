# Fix Environment Variable Issue

The container is still using the old `EXCHANGE_KEY_ENCRYPTION_KEY` value. Check what it's using:

```bash
# Check what EXCHANGE_KEY_ENCRYPTION_KEY the container has
sudo docker exec crypto-orchestrator-backend env | grep EXCHANGE_KEY_ENCRYPTION_KEY

# Check the length
sudo docker exec crypto-orchestrator-backend python -c "
import os
key = os.getenv('EXCHANGE_KEY_ENCRYPTION_KEY', 'NOT SET')
print(f'Key: {key}')
print(f'Length: {len(key)}')
print(f'Is 32+ chars: {len(key) >= 32}')
"
```

---

## Quick Fix: Set Environment Variable Directly

If the container is using the old value, we can set it directly:

```bash
# Stop backend
sudo docker-compose stop backend

# Remove container
sudo docker rm crypto-orchestrator-backend

# Start with explicit environment variable
sudo docker run -d \
  --name crypto-orchestrator-backend \
  --network cryptoorchestrator_crypto-network \
  -p 8000:8000 \
  -e NODE_ENV=production \
  -e PORT=8000 \
  -e DATABASE_URL=postgresql+asyncpg://crypto_user:crypto_pass@crypto-orchestrator-db:5432/cryptoorchestrator \
  -e REDIS_URL=redis://crypto-orchestrator-redis:6379/0 \
  -e JWT_SECRET=change-me-in-production-use-strong-random-secret-32-chars \
  -e EXCHANGE_KEY_ENCRYPTION_KEY=change-me-in-production-use-32-byte-key-here-42-chars \
  -e LOG_LEVEL=INFO \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/server_fastapi:/app/server_fastapi \
  -v $(pwd)/shared:/app/shared \
  -v $(pwd)/alembic:/app/alembic \
  --restart unless-stopped \
  cryptoorchestrator_backend \
  python -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000
```

---

**First, run the check command to see what value the container has!**
