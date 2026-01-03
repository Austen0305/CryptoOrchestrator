# Start Development Services

Start all development services for CryptoOrchestrator.

## Quick Start (All Services)

Start all services with one command:
```bash
npm run start:all
```

This automatically:
- Starts FastAPI backend (port 8000)
- Starts React frontend (port 5173)
- Checks service health
- Validates environment

## Individual Services

### Backend (FastAPI)

```bash
npm run dev:fastapi
```

Starts FastAPI server with hot reload:
- URL: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Frontend (React/Vite)

```bash
npm run dev
```

Starts Vite dev server with hot reload:
- URL: http://localhost:5173
- Hot Module Replacement enabled

### Electron Desktop App

```bash
npm run electron
```

Starts Electron desktop application in development mode.

## Service Health Checks

After starting services, verify they're running:

```bash
# Check all services
npm run check:services

# Check backend health
npm run health:check

# Advanced health check
npm run health:advanced
```

## Environment Validation

Before starting services, validate environment:

```bash
npm run validate:env
```

This checks:
- Required environment variables
- Database connection
- Redis connection (if configured)
- API keys (if required)

## Troubleshooting

### Port Already in Use

**Windows:**
```bash
netstat -ano | findstr :8000
# Kill process or change PORT in .env
```

**Linux/Mac:**
```bash
lsof -i :8000
# Kill process or change PORT in .env
```

### Services Not Starting

1. Check environment: `npm run validate:env`
2. Check dependencies: `npm install` and `pip install -r requirements.txt`
3. Check database: `alembic upgrade head`
4. Check logs for specific errors

### Database Connection Failed

1. Verify `DATABASE_URL` in `.env`
2. Check PostgreSQL is running
3. Run migrations: `alembic upgrade head`
4. Test connection: `python scripts/utilities/database-health.py`
