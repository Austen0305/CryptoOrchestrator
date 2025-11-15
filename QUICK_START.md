# 🚀 Quick Reference Guide

## **Start Your App (3 Simple Steps)**

### **Option A: Full Stack (Recommended)**
```powershell
# Terminal 1: Start Redis (for caching)
docker run -d -p 6379:6379 --name redis redis

# Terminal 2: Start Backend
npm run dev:fastapi

# Terminal 3: Start Frontend
npm run electron
```

### **Option B: Backend Only (API Development)**
```powershell
# Just start the API server
npm run dev:fastapi

# Test it
npm run health:advanced
```

### **Option C: Production Mode**
```powershell
# Build everything
npm run build:electron

# Start production server
npm run start
```

---

## **📊 Available Commands**

### **Development**
```bash
npm run dev              # Start Node.js development server
npm run dev:fastapi      # Start Python FastAPI server
npm run electron         # Start Electron desktop app
npm run check            # TypeScript type checking
```

### **Health & Monitoring**
```bash
npm run health           # Quick health check
npm run health:advanced  # Detailed system health report
curl http://localhost:8000/health/live    # Liveness probe
curl http://localhost:8000/health/ready   # Readiness probe
```

### **Redis & Caching**
```bash
npm run redis:start      # Start Redis server (Windows)
docker run -d -p 6379:6379 redis  # Redis via Docker (All platforms)
```

### **Background Tasks**
```bash
npm run celery:worker    # Start Celery worker
npm run celery:beat      # Start scheduled tasks
```

### **Database**
```bash
npm run migrate          # Apply migrations
npm run migrate:create "Add user table"  # Create new migration
npm run migrate:rollback # Undo last migration
npm run db:push          # Push schema changes
```

### **Testing**
```bash
npm run test             # Run Python tests with coverage
npm run test:watch       # Watch mode testing
npm run lint:py          # Python linting
npm run format:py        # Format Python code
```

### **Building**
```bash
npm run build            # Build for production
npm run build:electron   # Build Electron app
npm run electron:pack    # Package Electron (no installer)
npm run electron:dist    # Create installer
```

---

## **🎯 Test Your New Features**

### **1. Test Health Checks**
```bash
# Full health report
curl http://localhost:8000/health | jq

# Should show:
# - status: "healthy"
# - database: "healthy"
# - redis: "healthy"
# - CPU/Memory metrics
```

### **2. Test API Versioning**
```bash
# V1 API
curl http://localhost:8000/api/v1/info

# V2 API (enhanced)
curl http://localhost:8000/api/v2/info
```

### **3. Test Caching (Response Time)**
```bash
# First call (no cache) - slow
time curl http://localhost:8000/api/markets/BTC-USD

# Second call (cached) - fast!
time curl http://localhost:8000/api/markets/BTC-USD
```

### **4. Test Background Tasks**
```python
# In Python console
from server_fastapi.celery_app import run_backtest_task

task = run_backtest_task.delay("bot_123", "2024-01-01", "2024-12-31")
print(task.status)  # PENDING, STARTED, SUCCESS
```

---

## **🔧 Configuration**

### **Essential Environment Variables**
```bash
# .env file (copy from .env.example)

# Core
NODE_ENV=development
PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./crypto_orchestrator.db

# Redis (for caching & Celery)
REDIS_URL=redis://localhost:6379/0
ENABLE_CACHING=true

# Celery (background tasks)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security
JWT_SECRET=your-secret-key-here
```

---

## **🚨 Troubleshooting**

### **Problem: Redis connection failed**
```bash
# Solution: Start Redis
docker run -d -p 6379:6379 --name redis redis

# Or install Redis
# Windows: https://github.com/microsoftarchive/redis/releases
# Mac: brew install redis
# Linux: sudo apt-get install redis-server
```

### **Problem: Port 8000 already in use**
```bash
# Solution: Change port in .env
PORT=8001

# Or kill the process
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:8000 | xargs kill -9
```

### **Problem: Database connection error**
```bash
# Solution: Initialize database
npm run migrate

# Or check DATABASE_URL in .env
```

### **Problem: Celery not starting**
```bash
# Make sure Redis is running first
docker ps | grep redis

# Then start Celery
npm run celery:worker
```

---

## **📚 Documentation Links**

- **Health Checks:** http://localhost:8000/docs#/Health
- **API v1:** http://localhost:8000/docs#/API%20v1
- **API v2:** http://localhost:8000/docs#/API%20v2
- **WebSocket:** http://localhost:8000/docs#/WebSocket
- **Prometheus Metrics:** http://localhost:8000/metrics

---

## **💡 Pro Tips**

### **1. View All Logs**
```bash
# FastAPI logs
tail -f logs/fastapi.log

# Celery logs
tail -f logs/celery.log

# Audit logs
tail -f logs/audit.log
```

### **2. Monitor Performance**
```bash
# Get performance metrics
curl http://localhost:8000/metrics

# View in Prometheus format
# - CPU usage
# - Memory usage
# - Request count
# - Response times
```

### **3. Clear Cache**
```python
# In Python console
from server_fastapi.middleware.cache_manager import clear_all_cache
import asyncio

asyncio.run(clear_all_cache())
```

### **4. Check Circuit Breaker Status**
```python
# In Python console
from server_fastapi.middleware.circuit_breaker import exchange_breaker

print(exchange_breaker.get_stats())
# Shows: state, failure_count, last_failure_time
```

---

## **🎉 Your App is Ready!**

**Everything works out of the box!** Just run:

```powershell
npm run dev:fastapi
```

Then visit: http://localhost:8000/docs

**That's it!** 🚀

---

**Need help?** Check:
- `FINAL_STATUS.md` - Complete feature list
- `ENHANCEMENTS_GUIDE.md` - Detailed guides
- `PROJECT_STATUS.md` - Project overview
- `/docs` folder - All documentation
