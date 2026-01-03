# Quick Start Guide

Get CryptoOrchestrator up and running in 5 minutes.

## One-Command Setup

**Fastest way to get started**:

```bash
npm run quick-start
```

This automatically:
- ✅ Checks system requirements
- ✅ Creates `.env` file with secure secrets
- ✅ Installs all dependencies (Python + Node.js)
- ✅ Initializes database
- ✅ Verifies installation

## Manual Quick Start

If automated setup doesn't work:

### Step 1: Install Dependencies (2 minutes)

**Python**:
```bash
pip install -r requirements.txt
```

**Node.js**:
```bash
npm install --legacy-peer-deps
```

### Step 2: Configure Environment (1 minute)

```bash
# Copy example environment file
cp .env.example .env

# Edit if needed (defaults work for development)
# Minimum required: DATABASE_URL and JWT_SECRET (already set)
```

### Step 3: Initialize Database (1 minute)

```bash
# Run database migrations
alembic upgrade head
```

### Step 4: Start Services (1 minute)

```bash
# Start all services
npm run start:all
```

Or start individually:
```bash
# Terminal 1: Backend
npm run dev:fastapi

# Terminal 2: Frontend
npm run dev
```

## Verify Installation

### Quick Verification

```bash
# Run startup verification
npm run verify:startup
```

### Manual Verification

1. **Backend**: http://localhost:8000/health
2. **Frontend**: http://localhost:5173
3. **API Docs**: http://localhost:8000/docs

## First Steps

1. **Register Account**: http://localhost:5173/register
2. **Login**: http://localhost:5173/login
3. **Explore Dashboard**: Check out the features
4. **Read API Docs**: http://localhost:8000/docs

## Common Issues

### Port Already in Use

**Windows**:
```bash
netstat -ano | findstr :8000
# Kill process or change PORT in .env
```

**Linux/Mac**:
```bash
lsof -i :8000
# Kill process or change PORT in .env
```

### Database Connection Failed

1. Verify `DATABASE_URL` in `.env`
2. Check PostgreSQL is running
3. Run migrations: `alembic upgrade head`

### Dependencies Missing

1. Install Python deps: `pip install -r requirements.txt`
2. Install Node deps: `npm install --legacy-peer-deps`
3. Verify: `npm run setup:deps`

## Next Steps

After quick start:
1. **Read Documentation**: Check `docs/` directory
2. **Explore Features**: Try creating a trading bot
3. **Check Examples**: Look at example code
4. **Join Community**: Connect with other developers

## Summary

✅ **One Command**: `npm run quick-start`  
✅ **Manual**: 4 steps, ~5 minutes  
✅ **Verify**: `npm run verify:startup`  
✅ **Access**: http://localhost:5173

**You're ready to code!** 🚀
