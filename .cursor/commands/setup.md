# Complete Project Setup

Guide the user through complete CryptoOrchestrator setup.

## Quick Setup (Recommended)

Run the automated setup script:
```bash
npm run setup
```

This automatically:
- Checks system requirements
- Creates `.env` file with secure secrets
- Installs all dependencies (Python + Node.js)
- Initializes database
- Verifies installation

## Manual Setup Steps

If automated setup fails or user prefers manual setup:

### 1. Install Dependencies

**Python:**
```bash
pip install -r requirements.txt
```

**Node.js:**
```bash
npm install --legacy-peer-deps
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Minimum required: DATABASE_URL and JWT_SECRET (defaults work for development)
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

## Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Next Steps

1. Register an account at http://localhost:5173/register
2. Login at http://localhost:5173/login
3. Explore the dashboard and features
4. Check API docs at http://localhost:8000/docs

## Troubleshooting

If setup fails:
1. Check system requirements (Python 3.12+, Node.js 18+)
2. Verify ports 8000 and 5173 are available
3. Check database connection in `.env`
4. Run `npm run verify:startup` for diagnostics
