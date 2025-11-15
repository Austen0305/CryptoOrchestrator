# 🚀 CryptoOrchestrator - Complete Startup Guide

Welcome to **CryptoOrchestrator** - your professional cryptocurrency trading platform with automated bots, ML predictions, and real-time market analysis.

---

## 🎯 Quick Start (3 Steps)

### 1️⃣ Install Dependencies

```powershell
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
```

### 2️⃣ Configure Environment

```powershell
# Create environment file (if not exists)
if (!(Test-Path .env)) { Copy-Item .env.example .env }

# Edit .env with your Kraken API credentials
notepad .env
```

**Required Environment Variables:**
```env
KRAKEN_API_KEY=your_api_key_here
KRAKEN_SECRET=your_secret_here
DATABASE_URL=postgresql://user:pass@localhost/cryptoorch
REDIS_URL=redis://localhost:6379
```

### 3️⃣ Start the Application

**Option A: Full Stack Development**
```powershell
# Terminal 1: Start FastAPI Backend
npm run dev:fastapi

# Terminal 2: Start Frontend Dev Server
npm run dev

# Access at: http://localhost:5173
```

**Option B: Desktop App (Electron)**
```powershell
# Start both backend and Electron
npm run dev:fastapi
# In another terminal:
npm run electron
```

---

## 📱 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend (Dev)** | http://localhost:5173 | Vite dev server with HMR |
| **Backend API** | http://localhost:8000 | FastAPI REST endpoints |
| **API Documentation** | http://localhost:8000/docs | Interactive Swagger UI |
| **Alternative Docs** | http://localhost:8000/redoc | ReDoc documentation |
| **Health Check** | http://localhost:8000/health | System status endpoint |

---

## 🛠️ Available Commands

### Development

```powershell
# Frontend Development
npm run dev              # Start Vite dev server (port 5173)
npm run dev:web          # Alias for dev

# Backend Development
npm run dev:fastapi      # Start FastAPI with auto-reload (port 8000)

# Desktop App
npm run electron         # Launch Electron in development mode
```

### Building & Production

```powershell
# Build for Web
npm run build            # Build frontend + bundle server

# Build Desktop App
npm run build:electron   # Create packaged Electron app
npm run electron:pack    # Build unpacked directory
npm run electron:dist    # Build distributable installers

# Production Server
npm run start            # Run production build (Node.js)
```

### Testing & Quality

```powershell
# Python Tests
npm test                 # Run pytest with coverage
npm run test:watch       # Watch mode for TDD

# Type Checking
npm run check            # TypeScript type checking (no emit)

# Python Linting & Formatting
npm run lint:py          # Flake8 linting
npm run format:py        # Black code formatter
```

### Database & Migrations

```powershell
# Alembic Migrations
npm run migrate          # Apply all pending migrations
npm run migrate:create "description"  # Create new migration
npm run migrate:rollback # Rollback last migration

# Drizzle ORM
npm run db:push          # Push schema changes to DB
```

### Services & Infrastructure

```powershell
# Redis (Required for caching/jobs)
npm run redis:start      # Start Redis server (Windows)

# Celery (Background Tasks)
npm run celery:worker    # Start Celery worker
npm run celery:beat      # Start Celery beat scheduler
```

### Maintenance

```powershell
# Health Checks
npm run health           # Quick backend health check
npm run health:advanced  # Detailed health information

# Cleanup
npm run cleanup          # Remove build artifacts, caches, logs
```

---

## 🏗️ Project Structure

```
CryptoOrchestrator/
├── client/                 # React + Vite Frontend
│   ├── src/
│   │   ├── pages/         # Route pages (Dashboard, Bots, Markets, etc.)
│   │   ├── components/    # Reusable UI components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # Utilities and helpers
│   │   └── App.tsx        # Main app component with routing
│   └── index.html
│
├── server_fastapi/        # FastAPI Backend (Python)
│   ├── main.py           # App factory & middleware
│   ├── routes/           # API endpoint definitions
│   ├── services/         # Business logic layer
│   ├── models/           # Database models
│   ├── middleware/       # Custom middleware
│   └── tests/            # Backend tests
│
├── electron/             # Electron Desktop App
│   ├── index.js          # Main process
│   └── preload.js        # Secure bridge
│
├── server/               # Legacy Node.js server (reference)
│   └── integrations/     # Trading bot adapters
│       ├── freqtrade_adapter.py
│       └── jesse_adapter.py
│
├── shared/               # Shared types/schemas
│   ├── types.ts          # TypeScript definitions
│   └── schema.py         # Python schemas
│
└── scripts/              # Utility scripts
    ├── cleanup.ps1       # Project cleanup
    ├── start_redis.ps1   # Redis launcher
    └── start_celery.ps1  # Celery launcher
```

---

## 🎨 Features & Pages

### 📊 Dashboard (`/`)
- **Real-time portfolio overview** with P&L metrics
- **Live price charts** with technical indicators
- **Quick trade panel** for instant orders
- **Order book** visualization
- **AI predictions** from Freqtrade + Jesse ensemble

### 🤖 Bots (`/bots`)
- **Create & manage** automated trading bots
- **Monitor performance** with live metrics
- **Start/stop controls** with safety checks
- **Strategy configuration** (Grid, DCA, ML-based)

### 📈 Markets (`/markets`)
- **Browse all trading pairs** with live prices
- **24h change indicators** and volume data
- **Favorites/watchlist** management
- **Quick navigation** to trade specific pairs

### 📉 Analytics (`/analytics`)
- **Performance tracking** (daily, weekly, monthly)
- **Win rate & ROI** calculations
- **Portfolio distribution** pie charts
- **Trade history analysis**

### 🛡️ Risk Management (`/risk`)
- **Overall risk score** (0-100)
- **Volatility & Sharpe ratio** metrics
- **Max drawdown** monitoring
- **Position concentration** analysis
- **AI-powered recommendations** for risk reduction

### ⚙️ Settings (`/settings`)
- **Theme customization** (Light/Dark/System)
- **Language selection** (English, Español, العربية)
- **Trading preferences** (defaults, confirmations)
- **Notification settings** (alerts, sounds)
- **Security configuration** (API keys, 2FA)

---

## 🔧 Configuration

### Backend Settings (`server_fastapi/main.py`)

```python
# CORS origins (for Electron compatibility)
ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev
    "http://localhost:3000",  # Alternative
    "file://",                # Electron
]

# Rate limiting
RATE_LIMIT = "100/minute"

# Database connection pool
POOL_SIZE = 10
MAX_OVERFLOW = 20
```

### Frontend Settings (`client/vite.config.ts`)

```typescript
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

---

## 🐛 Troubleshooting

### Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```powershell
# Ensure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Build Errors

**Error:** `Cannot find module '@/components/...'`

**Solution:**
```powershell
# Clear cache and reinstall
Remove-Item node_modules -Recurse -Force
Remove-Item package-lock.json -Force
npm install
```

### Electron App Issues

**Error:** `Cannot connect to backend`

**Solution:**
```powershell
# Ensure FastAPI is running first
npm run dev:fastapi

# Then start Electron in another terminal
npm run electron
```

### Database Connection Failed

**Error:** `Could not connect to database`

**Solution:**
```powershell
# Check PostgreSQL is running
# Verify DATABASE_URL in .env
# Run migrations
npm run migrate
```

### Redis Connection Failed

**Error:** `Redis connection refused`

**Solution:**
```powershell
# Start Redis server
npm run redis:start

# Or install Redis: https://github.com/microsoftarchive/redis/releases
```

---

## 📦 Production Deployment

### Web Application

```powershell
# 1. Build frontend
npm run build

# 2. Run production server
npm run start

# 3. Use a process manager (PM2)
npm install -g pm2
pm2 start dist/index.js --name cryptoorch
```

### Desktop Application

```powershell
# Build installers for Windows
npm run build:electron

# Outputs in dist-electron/:
# - CryptoOrchestrator Setup.exe (installer)
# - win-unpacked/ (portable)
```

### Docker Deployment (Optional)

```dockerfile
# Dockerfile example
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` files** - Keep API keys private
2. **Use environment-specific configs** - Separate dev/prod settings
3. **Enable 2FA** on exchange accounts
4. **Rotate API keys regularly** - Every 90 days recommended
5. **Use read-only keys** for testing - Never commit withdrawal permissions
6. **Keep dependencies updated** - Run `npm audit` regularly
7. **Validate all inputs** - Backend validates user data
8. **Use HTTPS in production** - Enable SSL certificates

---

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs (when running)
- **Advanced Features:** See `docs/ADVANCED_INTELLIGENCE_FEATURES.md`
- **Smart Bot Guide:** See `docs/SMART_BOT_QUICKSTART.md`
- **Troubleshooting:** See `docs/troubleshooting/common_issues.md`
- **GitHub Issues:** Report bugs at repository issues page

---

## 🆘 Getting Help

### Check Logs

```powershell
# Backend logs
Get-Content logs/app.log -Tail 50

# Celery worker logs
Get-Content logs/celery.log -Tail 50
```

### System Status

```powershell
# Quick health check
npm run health

# Detailed system information
npm run health:advanced
```

### Common Commands Reference

```powershell
# Start fresh development session
npm run cleanup           # Clean artifacts
npm run dev:fastapi      # Start backend
npm run dev              # Start frontend (new terminal)

# Full restart
taskkill /F /IM python.exe    # Kill Python processes
taskkill /F /IM node.exe      # Kill Node processes
# Then restart services
```

---

## 🎉 You're Ready!

Your CryptoOrchestrator setup is complete. Start with:

```powershell
npm run dev:fastapi
npm run dev
```

Then navigate to **http://localhost:5173** and begin trading!

---

**Happy Trading! 📈🚀**
