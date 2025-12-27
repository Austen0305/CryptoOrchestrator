# Installation Guide

Complete step-by-step installation guide for CryptoOrchestrator.

## Prerequisites

### Required Software

- **Node.js** 18+ ([Download](https://nodejs.org/))
- **npm** or **yarn** (included with Node.js)
- **Python** 3.8+ ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))

### Optional Software

- **PostgreSQL** 15+ (recommended for production)
- **Redis** 6.0+ (for caching and session management)
- **Docker** & **Docker Compose** (for containerized deployment)

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/CryptoOrchestrator.git
cd CryptoOrchestrator
```

### 2. Install Node.js Dependencies

```bash
npm install --legacy-peer-deps
```

This installs all frontend dependencies including React, Electron, and build tools.

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Windows:
notepad .env
# Linux/Mac:
nano .env
```

**Required environment variables:**
- `JWT_SECRET` - Secret key for JWT tokens (generate a random string)
- `DATABASE_URL` - Database connection string (see below)
- `REDIS_URL` - Redis connection string (optional)

**Example .env configuration:**

```env
# Server
NODE_ENV=development
PORT=8000

# Security
JWT_SECRET=your-super-secret-jwt-key-change-this
EXCHANGE_KEY_ENCRYPTION_KEY=your-encryption-key-change-this

# Database (SQLite for development)
DATABASE_URL=sqlite:///./crypto_orchestrator.db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
```

### 5. Set Up Database

#### Option A: SQLite (Development - Default)

No setup required! SQLite is automatically used if no PostgreSQL connection is provided.

#### Option B: PostgreSQL (Production)

1. **Install PostgreSQL:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib

   # macOS (with Homebrew)
   brew install postgresql
   brew services start postgresql

   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Create Database:**
   ```bash
   # Connect to PostgreSQL
   psql -U postgres

   # Create database and user
   CREATE DATABASE cryptoorchestrator;
   CREATE USER crypto_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE cryptoorchestrator TO crypto_user;
   \q
   ```

3. **Update .env:**
   ```env
   DATABASE_URL=postgresql+asyncpg://crypto_user:your_password@localhost:5432/cryptoorchestrator
   ```

4. **Run Migrations:**
   ```bash
   alembic upgrade head
   ```

### 6. Set Up Redis (Optional)

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Windows
# Download from https://redis.io/download or use Docker
docker run -d -p 6379:6379 redis:alpine
```

### 7. Install Exchange API Keys (Optional)

For live trading, add your exchange API keys to `.env`:

```env
# Kraken (Primary)
KRAKEN_API_KEY=your_api_key
KRAKEN_SECRET_KEY=your_secret_key

# Other exchanges (optional)
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
# ... etc
```

**⚠️ Important:** Never commit `.env` to version control!

## Verification

### Check Installation

```bash
# Verify Python dependencies
python -c "import fastapi; print('FastAPI installed')"

# Verify Node.js dependencies
npm list --depth=0

# Check database connection
python scripts/check_db.py
```

### Start Development Server

```bash
# Terminal 1: Start FastAPI backend
npm run dev:fastapi

# Terminal 2: Start React frontend
npm run dev
```

Visit:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Troubleshooting

### Common Issues

#### Python Dependencies Fail to Install

```bash
# Upgrade pip
pip install --upgrade pip

# Try installing with --no-cache-dir
pip install --no-cache-dir -r requirements.txt
```

#### Node.js Dependencies Fail

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

#### Database Connection Errors

- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check connection string format in `.env`
- Ensure database and user exist
- Check firewall settings

#### Port Already in Use

```bash
# Find process using port 8000
# Linux/Mac:
lsof -i :8000
# Windows:
netstat -ano | findstr :8000

# Kill process or change PORT in .env
```

### Getting Help

- Check [troubleshooting/common_issues.md](troubleshooting/common_issues.md)
- Review [troubleshooting/faq.md](troubleshooting/faq.md)
- Open an issue on GitHub

## Next Steps

- Read the [User Guide](USER_GUIDE.md)
- Explore the [API Documentation](api.md)
- Review the [Architecture Guide](architecture.md)
- Set up [Deployment](deployment.md) for production

