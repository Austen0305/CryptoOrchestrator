# CryptoOrchestrator Quick Start Script (PowerShell)
# Automates the complete setup process

Write-Host "🚀 CryptoOrchestrator Quick Start" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check if .env exists
Write-Host "`nChecking environment..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file exists" -ForegroundColor Green
} else {
    Write-Host "⚠ .env file not found, creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ .env file created" -ForegroundColor Green
    } else {
        Write-Host "✗ .env.example not found" -ForegroundColor Red
        exit 1
    }
}

# Install Python dependencies
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt --quiet
    Write-Host "✓ Python dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Some Python dependencies may have failed (continuing...)" -ForegroundColor Yellow
}

# Install Node.js dependencies
Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
try {
    npm install --legacy-peer-deps --silent
    Write-Host "✓ Node.js dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Some Node.js dependencies may have failed (continuing...)" -ForegroundColor Yellow
}

# Initialize database
Write-Host "`nInitializing database..." -ForegroundColor Yellow
try {
    # Create data directory if it doesn't exist
    if (-not (Test-Path "data")) {
        New-Item -ItemType Directory -Path "data" | Out-Null
    }
    
    # Run migrations
    alembic upgrade head
    Write-Host "✓ Database initialized" -ForegroundColor Green
} catch {
    Write-Host "⚠ Database initialization had issues (you may need to run 'alembic upgrade head' manually)" -ForegroundColor Yellow
}

# Verify installation
Write-Host "`nVerifying installation..." -ForegroundColor Yellow
try {
    python scripts/verification/startup_verification.py
    Write-Host "✓ Verification complete" -ForegroundColor Green
} catch {
    Write-Host "⚠ Verification had warnings (check output above)" -ForegroundColor Yellow
}

Write-Host "`n✅ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start services: npm run start:all" -ForegroundColor White
Write-Host "  2. Access frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  3. Access API docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

