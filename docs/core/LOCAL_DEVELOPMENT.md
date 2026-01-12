# Local Development Guide

Complete guide for setting up and running CryptoOrchestrator locally for development and testing.

## Prerequisites

### Required Software
- **Python** 3.12+ ([Download](https://www.python.org/downloads/))
- **Node.js** 18+ ([Download](https://nodejs.org/))
- **npm** (comes with Node.js)
- **Git** ([Download](https://git-scm.com/downloads))

### Optional Software
- **Docker & Docker Compose** (for PostgreSQL/Redis) ([Download](https://www.docker.com/products/docker-desktop))
- **Redis CLI** (for testing Redis connection)
- **PostgreSQL client** (if using local PostgreSQL)

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd Crypto-Orchestrator
```

### 2. Create Environment File
```bash
# Windows
powershell -ExecutionPolicy Bypass -File scripts/create_env.ps1

# Linux/Mac
python scripts/generate_env.py
```

This creates a `.env` file with:
- Secure random secrets (JWT_SECRET, EXCHANGE_KEY_ENCRYPTION_KEY)
- Development-friendly defaults
- SQLite database configuration
- Optional Redis configuration

### 3. Install Dependencies

**Python dependencies:**
```bash
pip install -r requirements.txt
```

**Node.js dependencies:**
```bash
npm install --legacy-peer-deps
```

### 4. Initialize Database
```bash
alembic upgrade head
```

This creates the SQLite database file: `crypto_orchestrator.db`

### 5. Start Services

**Option A: Start both services (Windows)**
```bash
start-all.bat
```


**Option B: Start separately**
```bash
# Terminal 1: Backend
npm run dev:fastapi

# Terminal 2: Frontend
npm run dev
```


### 6. Verify Setup

- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Frontend:** http://localhost:5173
- **Health Check:** http://localhost:8000/healthz

## Environment Variables

### Required Variables

```env
NODE_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./crypto_orchestrator.db
JWT_SECRET=<generated-secret-64-chars>
EXCHANGE_KEY_ENCRYPTION_KEY=<generated-secret-32-chars>
```

### Optional Variables

```env
# Redis (optional - app works without it)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# Trading Configuration
DEFAULT_TRADING_MODE=paper
ENABLE_MOCK_DATA=true
PRODUCTION_MODE=false

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000
```

### Exchange API Keys (Optional)

See [TESTNET_API_KEYS.md](./TESTNET_API_KEYS.md) for details on configuring exchange API keys.


**For US Users (Recommended):**

```env
# Binance.US (No testnet - use paper trading mode for testing)
BINANCEUS_API_KEY=<your-api-key>
BINANCEUS_API_SECRET=<your-api-secret>
BINANCEUS_BASE_URL=https://api.binance.us

# Use paper trading for testing
DEFAULT_TRADING_MODE=paper
ENABLE_MOCK_DATA=true
```

**For International Users:**
```env
# Binance Testnet
BINANCE_TESTNET_API_KEY=<your-testnet-key>
BINANCE_TESTNET_API_SECRET=<your-testnet-secret>
BINANCE_TESTNET_BASE_URL=https://testnet.binancefuture.com

# Coinbase Sandbox
COINBASE_SANDBOX_API_KEY=<your-sandbox-key>
COINBASE_SANDBOX_API_SECRET=<your-sandbox-secret>
COINBASE_SANDBOX_BASE_URL=https://api-public.sandbox.exchange.coinbase.com
```

## Database Setup

### SQLite (Default - Recommended for Local Development)

No additional setup needed! The `.env` file is already configured for SQLite.

**Database file location:** `./crypto_orchestrator.db`

**Run migrations:**

```bash
alembic upgrade head
```

### PostgreSQL (Optional)

**Option A: Docker Compose**
```bash
docker-compose up postgres -d
```

Update `.env`:
```env
DATABASE_URL=postgresql+asyncpg://crypto_user:crypto_pass@localhost:5432/cryptoorchestrator
```

**Option B: Local PostgreSQL**

1. Install PostgreSQL
2. Create database: `CREATE DATABASE cryptoorchestrator;`
3. Update `.env` with connection string
4. Run migrations: `alembic upgrade head`

## Redis Setup (Optional)

The application works without Redis, but it's recommended for:
- Caching
- Rate limiting
- Session storage

### Option A: Docker Compose

```bash
docker-compose up redis -d
```

### Option B: Local Redis
1. Install Redis
2. Start Redis service
3. Verify: `redis-cli ping` (should return "PONG")

### Option C: Skip Redis
The app gracefully handles missing Redis - features will work but without caching.

## Running Tests

### Backend Tests
```bash
# All tests
npm test

# Watch mode
npm run test:watch

# With coverage
pytest tests/ -v --cov=server_fastapi --cov-report=html
```

### Frontend Tests
```bash
# Unit tests
npm run test:frontend

# UI mode
npm run test:frontend:ui

# With coverage
npm run test:frontend:coverage
```

### End-to-End Tests
```bash
# Run all E2E tests
npm run test:e2e

# UI mode (interactive)
npm run test:e2e:ui
```

**Prerequisites for E2E:**
- Backend running on port 8000
- Frontend running on port 5173
- Test database initialized

### Infrastructure Tests
```bash
npm run test:infrastructure
```

Tests:
- Database connectivity
- Redis connectivity (if available)
- External API connectivity
- Service health checks

## Development Workflow

### 1. Make Changes
- Edit code in `server_fastapi/` (backend) or `client/src/` (frontend)
- Backend auto-reloads with `--reload` flag
- Frontend hot-reloads automatically

### 2. Test Changes
```bash
# Backend
pytest server_fastapi/tests/ -v

# Frontend
npm run test:frontend

# E2E
npm run test:e2e
```

### 3. Verify System Health (New standard)

```bash
# Run the end-to-end verification script
python scripts/verify_full_system.py
```

- Validates: Health, Auth, Market Data, Wallet, Trading.
- Success output: `All E2E checks passed!`

### 4. Check Code Quality

```bash
# Python linting
npm run lint:py

# Python formatting
npm run format:py

# TypeScript checking
npm run check
```

## Common Issues & Solutions

### Port Already in Use

**Error:** Port 8000 or 5173 already in use

**Solution:**
```bash
# Windows - Find process using port
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different ports in .env
PORT=8001  # Backend
# Frontend: Update vite.config.ts
```

### Database Migration Errors

**Error:** Migration fails or database locked

**Solution:**
```bash
# Delete old database (development only!)
rm crypto_orchestrator.db  # Linux/Mac
del crypto_orchestrator.db  # Windows

# Re-run migrations
alembic upgrade head
```

### Import Errors

**Error:** Module not found

**Solution:**
```bash
# Reinstall Python dependencies
pip install -r requirements.txt

# Reinstall Node.js dependencies
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Environment Variable Not Found

**Error:** Missing environment variable

**Solution:**
1. Check `.env` file exists
2. Verify variable name matches (case-sensitive)
3. Restart services after changing `.env`

### Redis Connection Errors

**Error:** Redis connection failed

**Solution:**
- App works without Redis (optional dependency)
- Check Redis is running: `redis-cli ping`
- Or remove `REDIS_URL` from `.env` to disable Redis features

## Enhanced Features

### TradingView Lightweight Charts

The application includes an enhanced chart component using TradingView Lightweight Charts:

**Component:** `client/src/components/EnhancedPriceChart.tsx`

**Features:**
- Professional candlestick charts
- Area charts
- Real-time price updates
- Technical indicators support
- Better performance than Recharts

**Usage:**
```tsx
import { EnhancedPriceChart } from "@/components/EnhancedPriceChart";

<EnhancedPriceChart
  pair="BTC/USD"
  currentPrice={47350}
  change24h={4.76}
  live={true}
/>
```

### Market Data Integration

Real-time price data with CoinCap/CoinLore fallbacks:

**Service:** `server_fastapi/services/market_data_service.py`

**Features:**
- Multi-provider support (CoinCap, CoinLore)
- Automatic fallback when primary provider fails
- Caching to reduce API calls
- Rate limiting built-in
- No API keys required for standard usage

**Configuration:**
No specific environment variables required for standard usage.

### Advanced Trading Orders

Support for advanced order types:

**Service:** `server_fastapi/services/trading/advanced_orders.py`

**API Routes:** `/api/advanced-orders/*`

**Order Types:**
- Stop-loss orders
- Take-profit orders
- Trailing stop orders
- OCO (One-Cancels-Other) orders
- Time-in-Force options (GTC, IOC, FOK)

**Frontend API:**
```typescript
import { advancedOrdersApi } from "@/lib/api";

// Create stop-loss order
await advancedOrdersApi.createStopLoss({
  symbol: "BTC/USD",
  side: "sell",
  amount: 0.1,
  stop_price: 45000,
});

// Create trailing stop
await advancedOrdersApi.createTrailingStop({
  symbol: "BTC/USD",
  side: "sell",
  amount: 0.1,
  trailing_stop_percent: 2.0, // 2% trailing stop
});
```

## Project Structure

```
Crypto-Orchestrator/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   │   ├── ui/        # shadcn/ui components
│   │   │   └── EnhancedPriceChart.tsx  # New enhanced chart
│   │   ├── hooks/         # React hooks
│   │   ├── lib/           # Utilities & API clients
│   │   │   └── api.ts     # API functions (includes advancedOrdersApi)
│   │   └── pages/         # Page components
│   └── public/            # Static assets
├── server_fastapi/         # FastAPI backend
│   ├── routes/            # API endpoints
│   │   └── advanced_orders.py  # Advanced orders routes
│   ├── services/          # Business logic
│   │   ├── market_data_service.py # Market Data integration
│   │   └── trading/
│   │       └── advanced_orders.py  # Advanced orders service
│   ├── models/            # Database models
│   │   └── order.py       # Order model (with advanced fields)
│   └── main.py            # App entry point
├── .env                   # Environment variables (DO NOT COMMIT)
├── alembic/               # Database migrations
└── docs/                  # Documentation
    ├── LOCAL_DEVELOPMENT.md  # This file
    └── TESTNET_API_KEYS.md   # Testnet setup guide
```

## Next Steps

1. **Test Everything Locally**
   - Start backend: `npm run dev:fastapi`
   - Start frontend: `npm run dev`
   - Test all features in browser

2. **Run Tests**
   - Backend: `npm test`
   - Frontend: `npm run test:frontend`
   - E2E: `npm run test:e2e`

3. **Configure Testnet API Keys** (Optional)
   - See [TESTNET_API_KEYS.md](./TESTNET_API_KEYS.md)
   - Add keys to `.env` file
   - Test exchange connections

4. **Deploy When Ready**
   - See [FREE_STACK_DEPLOYMENT_GUIDE.md](./FREE_STACK_DEPLOYMENT_GUIDE.md)
   - Deploy to Koyeb/Render (backend)
   - Deploy to Netlify/Cloudflare Pages (frontend)

## Troubleshooting

See [docs/troubleshooting/common_issues.md](./troubleshooting/common_issues.md) for detailed troubleshooting guide.

## Additional Resources

- **API Documentation:** http://localhost:8000/docs (when backend is running)
- **Project README:** [README.md](../README.md)
- **Architecture Docs:** [docs/architecture.md](./architecture.md)
- **Environment Variables:** [docs/ENV_VARIABLES.md](./ENV_VARIABLES.md)

---

**Last Updated:** 2025-01-XX  
**Version:** 1.0.0
