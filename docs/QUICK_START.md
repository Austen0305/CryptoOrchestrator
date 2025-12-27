# CryptoOrchestrator - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.11+ (3.12 recommended)
- Node.js 18+
- Git

## One-Command Setup

```bash
# Clone repository
git clone <repository-url>
cd Crypto-Orchestrator

# Run complete setup
npm run setup
```

That's it! The setup script will:
- ✅ Check system requirements
- ✅ Create .env file with secure secrets
- ✅ Install all dependencies
- ✅ Initialize database
- ✅ Verify everything works

## Start Services

```bash
# Start all services
npm run start:all

# Or start individually:
npm run dev:fastapi  # Backend (Terminal 1)
npm run dev          # Frontend (Terminal 2)
```

## Verify Setup

```bash
# Check health
npm run setup:health

# Verify features
npm run setup:verify
```

## Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Common Issues

**Problem**: Missing .env file
```bash
python scripts/setup/create_env_file.py
```

**Problem**: Database not initialized
```bash
python scripts/setup/init_database.py
```

**Problem**: Dependencies not installed
```bash
pip install -r requirements.txt
npm install --legacy-peer-deps
```

**Problem**: Port already in use
- Stop other services using ports 8000, 5173, 5432, 6379
- Or change ports in `.env` file

## Next Steps

1. Read [Complete Setup Guide](COMPLETE_SETUP_GUIDE.md) for detailed instructions
2. See [Feature Verification Guide](FEATURE_VERIFICATION.md) to verify all features
3. Run E2E tests: `npm run test:e2e:complete`
4. Explore the API: http://localhost:8000/docs

## Quick Reference

See [Quick Reference Guide](QUICK_REFERENCE_SETUP.md) for all commands and shortcuts.

## Need Help?

- Run diagnostics: `python scripts/diagnostics/runtime_diagnostics.py --auto-fix`
- Check logs: `tail -f logs/fastapi.log`
- See troubleshooting guide: [TROUBLESHOOTING_RUNTIME.md](TROUBLESHOOTING_RUNTIME.md)
- Quick reference: [QUICK_REFERENCE_SETUP.md](QUICK_REFERENCE_SETUP.md)
