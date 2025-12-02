# 🚀 CryptoOrchestrator - Command Reference

Quick reference for all available commands and scripts.

## 📦 Installation

```powershell
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

## 🏃 Running the Application

### Development Mode

```powershell
# Start FastAPI backend (recommended)
npm run dev:fastapi
# or
python -m uvicorn server_fastapi.main:app --reload --host 0.0.0.0 --port 8000

# Start Node.js backend (alternative)
npm run dev

# Start React frontend (in separate terminal)
cd client
npm run dev

# Start Electron desktop app
npm run electron
```

### Production Mode

```powershell
# Build application
npm run build

# Build Electron app
npm run build:electron

# Start production server
npm start
```

## 🧪 Testing

```powershell
# Run all tests with coverage
npm run test
# or
pytest tests/ -v --cov=server_fastapi --cov-report=html

# Run tests in watch mode
npm run test:watch

# View coverage report
start htmlcov/index.html
```

## 🔍 Code Quality

```powershell
# TypeScript type checking
npm run check
# or
tsc --noEmit

# Python linting
npm run lint:py
# or
python -m flake8 server_fastapi/ tests/

# Python formatting
npm run format:py
# or
python -m black server_fastapi/ tests/

# Python type checking
python -m mypy server_fastapi/
```

## 📊 Monitoring & Health

```powershell
# Check application health
npm run health
# or
curl http://localhost:8000/health

# View Prometheus metrics
curl http://localhost:8000/metrics

# View API documentation
start http://localhost:8000/docs

# View ReDoc documentation
start http://localhost:8000/redoc
```

## 🗄️ Database

```powershell
# Push database schema
npm run db:push

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check database connection
python -c "from server_fastapi.database.connection_pool import db_pool; import asyncio; print('✅ Connected' if asyncio.run(db_pool.health_check()) else '❌ Failed')"
```

## 📝 Logging

```powershell
# View logs
type logs\\fastapi.log

# Clear logs (Windows)
del logs\\*.log

# Export client logs (in browser console)
logger.exportLogs()

# Clear client logs (in browser console)
logger.clearLogs()
```

## 🔧 Development Utilities

```powershell
# Install pre-commit hooks
pre-commit install

# Run pre-commit checks
pre-commit run --all-files

# Update dependencies
npm update
pip list --outdated

# Security audit
npm audit
safety check
```

## 🐳 Docker (if configured)

```powershell
# Build Docker image
docker build -t crypto-orchestrator .

# Run container
docker run -p 8000:8000 crypto-orchestrator

# Docker Compose
docker-compose up -d
docker-compose down
docker-compose logs -f
```

## 📦 Build & Distribution

```powershell
# Build Electron installer
npm run electron:dist

# Build for specific platform
npm run electron:dist -- --win
npm run electron:dist -- --mac
npm run electron:dist -- --linux

# Pack without installer
npm run electron:pack
```

## 🔐 Security

```powershell
# Check for vulnerabilities
npm audit
pip-audit

# Security scan
bandit -r server_fastapi/

# Update vulnerable packages
npm audit fix
pip install --upgrade package-name
```

## 🌐 API Testing

```powershell
# Test authentication
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"user\",\"password\":\"pass\"}"

# Test market data
curl http://localhost:8000/api/markets

# Test bot status
curl http://localhost:8000/api/bots
```

## 📊 Performance Testing

```powershell
# Run performance tests
python performance_test.py

# Memory profiling
python -m memory_profiler script.py

# Load testing with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health
```

## 🧹 Cleanup

```powershell
# Remove node_modules
rmdir /s /q node_modules

# Remove Python cache
for /d /r . %d in (__pycache__) do @if exist "%d" rmdir /s /q "%d"

# Remove build artifacts
rmdir /s /q dist
rmdir /s /q build
rmdir /s /q htmlcov

# Clean all
npm run clean  # if configured
```

## 🔄 Git Operations

```powershell
# Commit changes
git add .
git commit -m "Description"
git push

# Create branch
git checkout -b feature/new-feature

# View status
git status
git log --oneline
```

## 🎯 Common Workflows

### Starting Fresh Development

```powershell
# Terminal 1: Backend
npm run dev:fastapi

# Terminal 2: Frontend
cd client && npm run dev

# Terminal 3: Logs
type logs\\fastapi.log
```

### Running Full Test Suite

```powershell
# Run all checks
npm run check
npm run lint:py
npm run test

# View results
start htmlcov/index.html
```

### Deploying to Production

```powershell
# Build application
npm run build
npm run build:electron

# Run tests
npm run test

# Check health after deployment
npm run health
```

### Debugging Issues

```powershell
# Check logs
type logs\\fastapi.log

# Check health
npm run health

# View metrics
curl http://localhost:8000/metrics

# Run specific test
pytest tests/test_specific.py -v
```

## 📱 Environment Variables

```powershell
# View current environment
echo %NODE_ENV%

# Set environment (PowerShell)
$env:NODE_ENV="production"

# Set environment (CMD)
set NODE_ENV=production
```

## 🆘 Emergency Commands

```powershell
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Reset database
alembic downgrade base
alembic upgrade head

# Clear all caches
del /s /q *.pyc
rmdir /s /q __pycache__
npm cache clean --force
```

## 📚 Documentation

```powershell
# Generate API docs
python -m mkdocs build

# Serve documentation locally
python -m mkdocs serve

# View documentation
start http://localhost:8001
```

## 🎨 Useful Aliases (Add to PowerShell Profile)

```powershell
# Edit profile
notepad $PROFILE

# Add these aliases:
function dev { npm run dev:fastapi }
function test { npm run test }
function health { npm run health }
function logs { type logs\fastapi.log }
```

## 🔗 Important URLs

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics
- Frontend: http://localhost:5173 (Vite) or http://localhost:3000 (React)

---

**Tip**: Bookmark this file for quick reference! 📑
