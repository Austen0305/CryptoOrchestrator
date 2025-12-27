# CryptoOrchestrator - Setup Guide

## Quick Start

**One-command setup:**
```bash
npm run setup
```

This automatically:
- ✅ Checks system requirements
- ✅ Creates .env file with secure secrets
- ✅ Installs all dependencies
- ✅ Initializes database
- ✅ Verifies installation

## Manual Setup Steps

### 1. Environment Setup

```bash
# Create .env file
python scripts/setup/create_env_file.py

# Or manually
cp .env.example .env
# Edit .env with your configuration
```

### 2. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
npm install --legacy-peer-deps
```

### 3. Database Setup

```bash
# Initialize database and run migrations
python scripts/setup/init_database.py

# Or manually
alembic upgrade head
```

### 4. Start Services

```bash
# Start all services
npm run start:all

# Or individually
npm run dev:fastapi  # Backend
npm run dev          # Frontend
```

### 5. Verify Setup

```bash
# Health check
npm run setup:health

# Feature verification
npm run setup:verify
```

## Available Setup Commands

- `npm run setup` - Complete setup (all steps)
- `npm run setup:env` - Create .env file only
- `npm run setup:db` - Initialize database only
- `npm run setup:verify` - Verify all features
- `npm run setup:health` - Health check
- `npm run setup:deps` - Verify dependencies

## Troubleshooting

**Run diagnostics:**
```bash
python scripts/diagnostics/runtime_diagnostics.py --auto-fix
```

**Common issues:**
- Missing .env → `python scripts/setup/create_env_file.py`
- Database not initialized → `python scripts/setup/init_database.py`
- Missing dependencies → `pip install -r requirements.txt && npm install`
- Port conflicts → Change ports in `.env` or stop conflicting services

## Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get running in 5 minutes
- **[Complete Setup Guide](docs/COMPLETE_SETUP_GUIDE.md)** - Detailed setup instructions ✅ NEW
- **[Database Setup Guide](docs/DATABASE_SETUP.md)** - Database configuration guide ✅ NEW
- **[Service Startup Guide](docs/SERVICE_STARTUP.md)** - Service management guide ✅ NEW
- **[Feature Verification](docs/FEATURE_VERIFICATION.md)** - Verify all features work
- **[Troubleshooting Guide](docs/TROUBLESHOOTING_RUNTIME.md)** - Fix common issues

## Next Steps

After setup:

1. **Start services**: `npm run start:all`
2. **Access application**: http://localhost:5173
3. **API documentation**: http://localhost:8000/docs
4. **Run E2E tests**: `npm run test:e2e:complete`
5. **Verify features**: `npm run setup:verify`
