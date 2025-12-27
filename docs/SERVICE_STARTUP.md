# Service Startup Guide

Complete guide for starting and managing all CryptoOrchestrator services.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Service Overview](#service-overview)
3. [Starting Services](#starting-services)
4. [Health Checks](#health-checks)
5. [Service Management](#service-management)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### Start All Services

```bash
npm run start:all
```

This automatically:
- Validates environment
- Starts PostgreSQL (if using Docker)
- Starts Redis (if using Docker)
- Starts FastAPI backend
- Starts React frontend
- Waits for health checks
- Reports service status

## Service Overview

### Services

1. **Backend (FastAPI)**
   - Port: 8000
   - URL: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

2. **Frontend (React + Vite)**
   - Port: 5173
   - URL: http://localhost:5173
   - Dev server with HMR

3. **PostgreSQL Database**
   - Port: 5432
   - Default database: `cryptoorchestrator`

4. **Redis Cache** (Optional)
   - Port: 6379
   - Used for caching and rate limiting

5. **Celery Worker** (Optional)
   - Background job processor
   - Requires Redis

## Starting Services

### Automated Startup

**Start all services:**
```bash
npm run start:all
```

**Platform-specific:**
```bash
# Windows
.\scripts\utilities\start-all-services.js

# Linux/Mac
node scripts/utilities/start-all-services.js
```

### Manual Startup

#### Backend Only

```bash
npm run dev:fastapi
# or
python -m uvicorn server_fastapi.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Only

```bash
npm run dev
# or
cd client && npm run dev
```

#### Database (PostgreSQL)

**Using Docker:**
```bash
docker run -d \
  --name postgres-crypto \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cryptoorchestrator \
  postgres:14
```

**Using Local Installation:**
```bash
# Linux
sudo systemctl start postgresql

# macOS
brew services start postgresql@14

# Windows
# Start via Services panel or:
net start postgresql-x64-14
```

#### Redis

**Using Docker:**
```bash
docker run -d \
  --name redis-crypto \
  -p 6379:6379 \
  redis:6
```

**Using Local Installation:**
```bash
# Linux
sudo systemctl start redis

# macOS
brew services start redis

# Windows
# Start via Services panel
```

#### Celery Worker

```bash
npm run celery:worker
# or
celery -A server_fastapi.celery_app worker --loglevel=info
```

#### Celery Beat (Scheduler)

```bash
npm run celery:beat
# or
celery -A server_fastapi.celery_app beat --loglevel=info
```

## Health Checks

### Comprehensive Health Check

```bash
npm run setup:health
# or
python scripts/setup/health_check.py
```

This checks:
- Backend health endpoints
- Frontend accessibility
- Database connection
- Redis connection (if configured)
- WebSocket connectivity

### Individual Health Checks

**Backend:**
```bash
curl http://localhost:8000/health
# or
npm run health
```

**Frontend:**
```bash
curl http://localhost:5173
```

**Database:**
```bash
python scripts/setup/init_database.py --skip-create --skip-migrations
```

**Redis:**
```bash
redis-cli ping
# Should return: PONG
```

### Service Status Check

```bash
npm run check:services
# or
node scripts/utilities/check-services.js
```

## Service Management

### Service Manager

The project includes a service manager for automated service lifecycle:

```javascript
import ServiceManager from './scripts/utilities/service-manager.js';

const manager = new ServiceManager();

// Start all services
await manager.startAll();

// Wait for services to be ready
await manager.waitForServices(60000); // 60 second timeout

// Stop all services
manager.stopAll();
```

### Environment Validation

Before starting services, validate environment:

```bash
npm run validate:env
# or
node scripts/utilities/validate-environment.js
```

This checks:
- Required environment variables
- Python and Node.js versions
- Dependencies installed
- Port availability

### Graceful Shutdown

Services support graceful shutdown:

- **SIGINT (Ctrl+C)**: Gracefully stops all services
- **SIGTERM**: Gracefully stops all services
- **Process exit**: Automatically cleans up

### Service Dependencies

Services start in this order:

1. **Database** (PostgreSQL/SQLite)
2. **Redis** (if configured)
3. **Backend** (FastAPI)
4. **Frontend** (React)

Each service waits for dependencies to be ready before starting.

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
# Backend logs
tail -f logs/fastapi.log

# Frontend logs
# Check terminal output
```

**Check ports:**
```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# Linux/Mac
lsof -i :8000
lsof -i :5173
```

**Port conflicts:**
- Change ports in `.env` file
- Or stop conflicting services

### Backend Issues

**Backend won't start:**
```bash
# Check environment
npm run validate:env

# Check database
python scripts/setup/init_database.py

# Check dependencies
npm run setup:deps

# Run diagnostics
python scripts/diagnostics/runtime_diagnostics.py --auto-fix
```

**Backend crashes:**
- Check logs: `logs/fastapi.log`
- Verify database connection
- Check for missing environment variables
- Verify dependencies are installed

### Frontend Issues

**Frontend won't start:**
```bash
# Check Node.js version
node --version  # Should be 18+

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps

# Check for port conflicts
lsof -i :5173
```

**Frontend can't connect to backend:**
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings in `.env`
- Verify `BACKEND_URL` in frontend config

### Database Issues

**Database connection failed:**
```bash
# Check database is running
pg_isready  # PostgreSQL
# or check SQLite file exists

# Verify connection string
python scripts/setup/init_database.py --skip-create --skip-migrations

# Check migrations
alembic current
```

### Redis Issues

**Redis connection failed:**
```bash
# Check Redis is running
redis-cli ping

# Verify connection string in .env
# REDIS_URL=redis://localhost:6379/0
```

**Note:** Redis is optional. Services will work without it (with reduced caching).

### WebSocket Issues

**WebSocket connection failed:**
- Verify backend is running
- Check WebSocket endpoint: `ws://localhost:8000/ws`
- Verify CORS settings allow WebSocket connections
- Check firewall settings

## Service Configuration

### Environment Variables

Configure services via `.env`:

```env
# Backend
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=DEBUG

# Frontend
VITE_API_URL=http://localhost:8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/app.db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Celery (optional)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### Port Configuration

Change ports if conflicts occur:

```env
# Backend port
PORT=8001

# Frontend port (in vite.config.ts)
# server: { port: 5174 }
```

## Production Considerations

### Process Management

**Use process managers in production:**

**PM2 (Node.js):**
```bash
npm install -g pm2
pm2 start npm --name "crypto-backend" -- run dev:fastapi
pm2 start npm --name "crypto-frontend" -- run dev
```

**Supervisor (Python):**
```ini
[program:crypto-backend]
command=uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
```

### Docker Compose

Use Docker Compose for production:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

Deploy to Kubernetes:

```bash
kubectl apply -f k8s/
```

## Additional Resources

- **[Complete Setup Guide](COMPLETE_SETUP_GUIDE.md)** - Full setup instructions
- **[Environment Setup](guides/ENVIRONMENT_SETUP.md)** - Environment configuration
- **[Troubleshooting Guide](TROUBLESHOOTING_RUNTIME.md)** - Fix common issues
- **[Health Monitoring](monitoring/health_monitor.py)** - Continuous health monitoring

---

**Last Updated:** December 12, 2025
