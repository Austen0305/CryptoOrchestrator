# CryptoOrchestrator - Quick Start Guide

**Get up and running in 5 minutes!**

## Prerequisites

- **Python 3.11+** (3.12 recommended)
- **Node.js 18+** (LTS recommended)
- **npm** or **yarn**

## One-Command Setup

```bash
npm run setup
```

This automatically:
- ✅ Checks system requirements
- ✅ Creates `.env` file with secure secrets
- ✅ Installs all dependencies
- ✅ Initializes database
- ✅ Verifies installation

## Manual Setup (Step-by-Step)

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
npm install --legacy-peer-deps
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration (optional - defaults work for development)
# Minimum required: DATABASE_URL and JWT_SECRET (already set)
```

### 3. Initialize Database

```bash
# Run database migrations
alembic upgrade head

# Or use the setup script
python scripts/setup/init_database.py
```

### 4. Start Services

```bash
# Start all services (recommended)
npm run start:all

# Or start individually:
# Terminal 1: Backend
npm run dev:fastapi

# Terminal 2: Frontend
npm run dev
```

### 5. Verify Installation

```bash
# Run startup verification
npm run verify:startup

# Check health
curl http://localhost:8000/health
```

## Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## First Steps

1. **Register an account** at http://localhost:5173/register
2. **Login** at http://localhost:5173/login
3. **Explore the dashboard** and features
4. **Check API docs** at http://localhost:8000/docs

## Common Issues

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
# Kill the process or change PORT in .env

# Linux/Mac
lsof -i :8000
# Kill the process or change PORT in .env
```

### Database Connection Failed

```bash
# Check DATABASE_URL in .env
# For SQLite, ensure the directory exists:
mkdir -p data
```

### Missing Dependencies

```bash
# Reinstall Python dependencies
pip install -r requirements.txt

# Reinstall Node.js dependencies
npm install --legacy-peer-deps
```

## Next Steps

- Read the [Complete Setup Guide](docs/COMPLETE_SETUP_GUIDE.md)
- Check [Troubleshooting Guide](docs/TROUBLESHOOTING_RUNTIME.md)
- Review [API Documentation](http://localhost:8000/docs)

## Need Help?

- **Documentation**: See `docs/` directory
- **Troubleshooting**: `docs/TROUBLESHOOTING_RUNTIME.md`
- **Setup Issues**: Run `python scripts/diagnostics/runtime_diagnostics.py --auto-fix`

---

**Ready to start trading!** 🚀

