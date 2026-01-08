# Fix Backend Startup Failure

**Problem:** Backend is crashing with "Application startup failed. Exiting."

---

## Step 1: Get the Actual Error

```bash
# Get the full error traceback
sudo docker-compose logs backend 2>&1 | grep -A 20 "ERROR\|Traceback\|Exception" | tail -50

# Or get the last error before each crash
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -B 5 -A 15 "Application startup failed" | tail -30
```

---

## Step 2: Check for Specific Errors

```bash
# Check for import errors
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -i "import\|module\|no module"

# Check for database connection errors
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -i "database\|postgres\|connection"

# Check for validation errors
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -i "validation\|secret\|key"
```

---

## Step 3: Run Backend Manually to See Full Error

```bash
# Stop the container
sudo docker-compose stop backend

# Run backend manually to see full error
sudo docker run --rm \
  --network cryptoorchestrator_crypto-network \
  -e DATABASE_URL=postgresql+asyncpg://crypto_user:crypto_pass@crypto-orchestrator-db:5432/cryptoorchestrator \
  -e REDIS_URL=redis://crypto-orchestrator-redis:6379/0 \
  -e JWT_SECRET=change-me-in-production-use-strong-random-secret-32-chars \
  -e EXCHANGE_KEY_ENCRYPTION_KEY=change-me-in-production-use-32-byte-key-here \
  -e LOG_LEVEL=INFO \
  cryptoorchestrator_backend \
  python -m uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000
```

---

**Run Step 1 first to see the actual error!**
