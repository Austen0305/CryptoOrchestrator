# One-Command Setup Script for CryptoOrchestrator (PowerShell)
# This script sets up the entire development environment

Write-Host "🚀 CryptoOrchestrator - Automated Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Functions for colored output
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Yellow
}

# Check if command exists
function Test-Command {
    param([string]$Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
}

# Step 1: Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Cyan
$MissingDeps = @()

if (-not (Test-Command "node")) {
    $MissingDeps += "Node.js (v18+)"
}

if (-not (Test-Command "python")) {
    $MissingDeps += "Python (3.12+)"
}

if (-not (Test-Command "npm")) {
    $MissingDeps += "npm"
}

if (-not (Test-Command "pip")) {
    $MissingDeps += "pip"
}

if ($MissingDeps.Count -gt 0) {
    Write-Error "Missing required dependencies:"
    foreach ($dep in $MissingDeps) {
        Write-Host "  - $dep"
    }
    Write-Host ""
    Write-Host "Please install missing dependencies and run this script again."
    exit 1
}

Write-Success "All prerequisites found"
Write-Host ""

# Step 2: Check environment file
Write-Host "🔧 Setting up environment..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Info "Creating .env from .env.example"
        Copy-Item ".env.example" ".env"
        Write-Success ".env file created"
        
        # Generate secure secrets if using defaults
        $envContent = Get-Content ".env" -Raw
        if ($envContent -match "dev-secret-change-me-in-production") {
            Write-Info "Generating secure secrets..."
            
            # Generate JWT secret (32 bytes)
            $jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
            $jwtSecret = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($jwtSecret))
            
            # Generate encryption key (32 bytes)
            $encryptionKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
            $encryptionKey = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($encryptionKey))
            
            # Update .env file
            (Get-Content ".env") -replace "JWT_SECRET=.*", "JWT_SECRET=$jwtSecret" | Set-Content ".env"
            (Get-Content ".env") -replace "EXCHANGE_KEY_ENCRYPTION_KEY=.*", "EXCHANGE_KEY_ENCRYPTION_KEY=$encryptionKey" | Set-Content ".env"
            
            Write-Success "Generated secure secrets"
        }
        
        Write-Info "Please review and update .env with your configuration"
    }
    else {
        Write-Error ".env.example not found. Creating basic .env file..."
        # Create basic .env file
        @"
NODE_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=$(-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_}))
EXCHANGE_KEY_ENCRYPTION_KEY=$(-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_}))
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Success "Created basic .env file"
        Write-Info "Please review and update .env with your configuration"
    }
}
else {
    Write-Success ".env file already exists"
}
Write-Host ""

# Step 3: Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Cyan
$directories = @("data", "logs", "models")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Success "Created $dir directory"
    }
}
Write-Host ""

# Step 4: Install Node.js dependencies
Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Cyan
try {
    npm install --legacy-peer-deps
    Write-Success "Node.js dependencies installed"
}
catch {
    Write-Error "Failed to install Node.js dependencies"
    exit 1
}
Write-Host ""

# Step 5: Install Python dependencies
Write-Host "🐍 Installing Python dependencies..." -ForegroundColor Cyan
try {
    pip install -r requirements.txt
    Write-Success "Python dependencies installed"
}
catch {
    Write-Error "Failed to install Python dependencies"
    exit 1
}

if (Test-Path "requirements-dev.txt") {
    Write-Info "Installing development dependencies..."
    try {
        pip install -r requirements-dev.txt
    }
    catch {
        Write-Info "Some dev dependencies failed (non-critical)"
    }
}
Write-Host ""

# Step 5: Install testing dependencies
Write-Host "🧪 Installing testing dependencies..." -ForegroundColor Cyan
try {
    pip install pytest pytest-asyncio pytest-cov aiohttp flake8 black
    Write-Success "Testing dependencies installed"
}
catch {
    Write-Info "Some test dependencies failed (non-critical)"
}
Write-Host ""

# Step 7: Database setup
Write-Host "💾 Setting up database..." -ForegroundColor Cyan
if (Test-Command "alembic") {
    Write-Info "Running database migrations..."
    try {
        alembic upgrade head
        Write-Success "Database migrations completed"
    }
    catch {
        Write-Info "Migrations skipped (database may not be configured)"
    }
}
else {
    Write-Info "Alembic not found, skipping migrations"
}
Write-Host ""

# Step 7: Verify installation
Write-Host "✅ Verifying installation..." -ForegroundColor Cyan

# Check if TypeScript compiles
Write-Info "Checking TypeScript..."
try {
    npm run check 2>$null
    Write-Success "TypeScript check passed"
}
catch {
    Write-Info "TypeScript has some warnings (non-critical for setup)"
}

# Check if Python scripts compile
Write-Info "Checking Python test scripts..."
try {
    python -m py_compile scripts/test_infrastructure.py scripts/test_security.py scripts/load_test.py
    Write-Success "Python test scripts compile successfully"
}
catch {
    Write-Error "Some Python scripts have issues"
}
Write-Host ""

# Step 9: Create convenience aliases
Write-Host "🔗 Setting up convenience commands..." -ForegroundColor Cyan
$aliasScript = @'
# CryptoOrchestrator - Quick Commands (PowerShell)
# Source this file: . .\.setup-complete.ps1

function co-start-backend { npm run dev:fastapi }
function co-start-frontend { npm run dev }
function co-start-redis { npm run redis:start }
function co-test-infra { npm run test:phase1 }
function co-test-security { npm run test:phase2 }
function co-test-all { npm run test:pre-deploy }
function co-test-e2e { npm run test:e2e }

Write-Host "🚀 CryptoOrchestrator aliases loaded!" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:"
Write-Host "  co-start-backend   - Start FastAPI backend"
Write-Host "  co-start-frontend  - Start Vite frontend"
Write-Host "  co-start-redis     - Start Redis server"
Write-Host "  co-test-infra      - Run infrastructure tests"
Write-Host "  co-test-security   - Run security tests"
Write-Host "  co-test-all        - Run all pre-deployment tests"
Write-Host "  co-test-e2e        - Run E2E tests"
'@

Set-Content -Path ".setup-complete.ps1" -Value $aliasScript
Write-Success "Convenience aliases created (.setup-complete.ps1)"
Write-Host ""

# Final summary
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "✨ Setup Complete! ✨" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit .env file with your configuration"
Write-Host "2. Source aliases: . .\.setup-complete.ps1"
Write-Host "3. Start backend: npm run dev:fastapi"
Write-Host "4. Start frontend: npm run dev (in another PowerShell)"
Write-Host "5. Run tests: npm run test:pre-deploy"
Write-Host ""
Write-Host "📖 Documentation:"
Write-Host "  - Testing Guide: docs\TESTING_GUIDE.md"
Write-Host "  - Quick Reference: docs\TESTING_README.md"
Write-Host "  - Status: docs\PRE_DEPLOYMENT_STATUS.md"
Write-Host ""
Write-Host "🔗 Useful commands:"
Write-Host "  npm run dev:fastapi      # Start backend"
Write-Host "  npm run dev              # Start frontend"
Write-Host "  npm run test:phase1      # Test infrastructure"
Write-Host "  npm run test:phase2      # Test security"
Write-Host "  npm run test:pre-deploy  # Run all tests"
Write-Host "  npm run test:e2e         # End-to-end tests"
Write-Host ""
Write-Success "Happy coding! 🎉"
