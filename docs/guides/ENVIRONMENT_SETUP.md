# Environment Setup Guide

This guide walks you through setting up the CryptoOrchestrator development and production environments.

## Quick Start

### Automated Setup (Recommended)

**Windows:**
```powershell
.\scripts\setup-complete.ps1
```

**Unix/Linux/Mac:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Manual Setup

Follow the steps below for manual setup.

## Prerequisites

- **Python 3.12+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **PostgreSQL 14+** (for production) or SQLite (for development)
- **Redis 6+** (optional but recommended for caching and rate limiting)

## Step 1: Environment Variables

### Create `.env` File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure the following variables:

#### Required Variables

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/app.db  # Development
# DATABASE_URL=postgresql://user:password@localhost:5432/cryptoorchestrator  # Production

# Security
JWT_SECRET=<generate-32-byte-random-secret>
EXCHANGE_KEY_ENCRYPTION_KEY=<generate-32-byte-random-key>

# Application
NODE_ENV=development  # or staging, production
PORT=8000
HOST=0.0.0.0
```

#### Optional but Recommended

```env
# Redis (for caching and rate limiting)
REDIS_URL=redis://localhost:6379/0

# Monitoring
SENTRY_DSN=<your-sentry-dsn>  # For error tracking
ENABLE_SENTRY=false  # Set to true in production

# Stripe (for payments)
STRIPE_SECRET_KEY=<your-stripe-secret-key>
STRIPE_PUBLISHABLE_KEY=<your-stripe-publishable-key>
STRIPE_WEBHOOK_SECRET=<your-stripe-webhook-secret>

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-email>
SMTP_PASSWORD=<your-password>
SMTP_FROM=<your-email>
EMAIL_ENABLED=false  # Set to true to enable email
```

#### DEX Trading Configuration

```env
# DEX Aggregator API Keys (at least one required for DEX trading)
ZEROX_API_KEY=<your-0x-api-key>
OKX_API_KEY=<your-okx-api-key>
OKX_SECRET_KEY=<your-okx-secret-key>
OKX_PASSPHRASE=<your-okx-passphrase>
RUBIC_API_KEY=<your-rubic-api-key>

# Blockchain RPC URLs (at least one required for DEX trading)
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/<your-api-key>
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/<your-api-key>
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/<your-api-key>
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/<your-api-key>
OPTIMISM_RPC_URL=https://opt-mainnet.g.alchemy.com/v2/<your-api-key>
AVALANCHE_RPC_URL=https://avax-mainnet.g.alchemy.com/v2/<your-api-key>
BNB_CHAIN_RPC_URL=https://bsc-dataseed.binance.org/

# RPC Configuration
RPC_PROVIDER_TYPE=alchemy  # alchemy, infura, quicknode, public
RPC_API_KEY=<your-rpc-provider-api-key>
RPC_TIMEOUT=30
RPC_MAX_RETRIES=3
```

### Generate Secure Secrets

**PowerShell:**
```powershell
# Generate JWT_SECRET (32 bytes)
$jwtSecret = [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
Write-Host "JWT_SECRET=$jwtSecret"

# Generate EXCHANGE_KEY_ENCRYPTION_KEY (32 bytes)
$encryptionKey = [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
Write-Host "EXCHANGE_KEY_ENCRYPTION_KEY=$encryptionKey"
```

**Bash:**
```bash
# Generate JWT_SECRET (32 bytes)
echo "JWT_SECRET=$(openssl rand -base64 32)"

# Generate EXCHANGE_KEY_ENCRYPTION_KEY (32 bytes)
echo "EXCHANGE_KEY_ENCRYPTION_KEY=$(openssl rand -base64 32)"
```

**Python:**
```python
import secrets
print(f"JWT_SECRET={secrets.token_urlsafe(32)}")
print(f"EXCHANGE_KEY_ENCRYPTION_KEY={secrets.token_urlsafe(32)}")
```

## Step 2: Database Setup

### Development (SQLite)

SQLite is used by default for development. No additional setup required.

### Production (PostgreSQL)

1. **Install PostgreSQL:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Create Database:**
   ```sql
   CREATE DATABASE cryptoorchestrator;
   CREATE USER cryptouser WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE cryptoorchestrator TO cryptouser;
   ```

3. **Update DATABASE_URL:**
   ```env
   DATABASE_URL=postgresql://cryptouser:your-password@localhost:5432/cryptoorchestrator
   ```

4. **Run Migrations:**
   ```bash
   alembic upgrade head
   ```

## Step 3: Redis Setup (Optional)

Redis is optional but recommended for:
- Caching
- Rate limiting
- Session storage
- Celery task queue

### Install Redis

**Docker (Recommended):**
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

**Local Installation:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# Download from https://github.com/microsoftarchive/redis/releases
```

### Configure Redis

Update `.env`:
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### Test Redis Connection

```bash
# Test connection
redis-cli ping
# Should return: PONG
```

## Step 4: Install Dependencies

### Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Node.js Dependencies

```bash
npm install --legacy-peer-deps
```

## Step 5: Validate Environment

Run the environment validation script:

```bash
# Node.js script
node scripts/validate-environment.js

# Or PowerShell script
.\scripts\validate-environment.ps1
```

This will check:
- ✅ Python and Node.js installations
- ✅ Dependencies installed
- ✅ Port availability
- ✅ Environment variables configured
- ✅ Database connectivity
- ✅ Redis connectivity (if configured)

## Step 6: Initialize Database

```bash
# Run Alembic migrations
alembic upgrade head

# Verify tables created
# SQLite:
sqlite3 data/app.db ".tables"

# PostgreSQL:
psql -U cryptouser -d cryptoorchestrator -c "\dt"
```

## Step 7: Start Services

### Development Mode

**Start Backend:**
```bash
cd server_fastapi
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Start Frontend:**
```bash
npm run dev
```

**Start Redis (if using):**
```bash
redis-server
```

**Start Celery Worker (if using background tasks):**
```bash
celery -A server_fastapi.celery_app worker --loglevel=info
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Environment-Specific Configuration

### Development

```env
NODE_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
ENABLE_MOCK_DATA=true
PRODUCTION_MODE=false
LOG_LEVEL=DEBUG
```

### Staging

```env
NODE_ENV=staging
DATABASE_URL=postgresql://user:pass@staging-db:5432/cryptoorchestrator
REDIS_URL=redis://staging-redis:6379/0
ENABLE_MOCK_DATA=false
PRODUCTION_MODE=false
LOG_LEVEL=INFO
SENTRY_DSN=<staging-sentry-dsn>
```

### Production

```env
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@prod-db:5432/cryptoorchestrator
REDIS_URL=redis://prod-redis:6379/0
ENABLE_MOCK_DATA=false
PRODUCTION_MODE=true
LOG_LEVEL=WARNING
SENTRY_DSN=<production-sentry-dsn>
ENABLE_SENTRY=true
```

**⚠️ Important Production Checklist:**
- [ ] Change `JWT_SECRET` to a strong random secret (32+ bytes)
- [ ] Change `EXCHANGE_KEY_ENCRYPTION_KEY` to a strong random key (32 bytes)
- [ ] Set `PRODUCTION_MODE=true`
- [ ] Set `ENABLE_MOCK_DATA=false`
- [ ] Configure `SENTRY_DSN` for error tracking
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable Redis for caching and rate limiting
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up automated backups

## Troubleshooting

### Database Connection Issues

**SQLite:**
- Ensure `data/` directory exists: `mkdir -p data`
- Check file permissions

**PostgreSQL:**
- Verify PostgreSQL is running: `pg_isready`
- Check connection string format
- Verify user permissions
- Check firewall rules

### Redis Connection Issues

- Verify Redis is running: `redis-cli ping`
- Check `REDIS_URL` format
- Verify port 6379 is not blocked
- Check Redis logs: `redis-cli monitor`

### Port Conflicts

- Check if port 8000 is in use: `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (Unix)
- Change port in `.env`: `PORT=8001`

### Environment Variable Issues

- Ensure `.env` file is in project root
- Check for typos in variable names
- Verify no extra spaces around `=`
- Use quotes for values with spaces: `KEY="value with spaces"`

## Next Steps

After environment setup:
1. ✅ Run tests: `pytest` and `npm test`
2. ✅ Start development server
3. ✅ Access API docs: http://localhost:8000/docs
4. ✅ Access frontend: http://localhost:5173
5. ✅ Review [Getting Started Guide](GETTING_STARTED.md)
6. ✅ Review [Architecture Documentation](architecture.md)

## Additional Resources

- [API Reference](API_REFERENCE.md)
- [Testing Guide](TESTING_GUIDE.md)
- [Deployment Guide](COMPLETE_DEPLOYMENT_CHECKLIST.md)
- [Security Checklist](SECURITY_HARDENING_CHECKLIST.md)
