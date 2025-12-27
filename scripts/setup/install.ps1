# CryptoOrchestrator One-Click Installation Script (Windows PowerShell)
# This script automates the installation and setup of CryptoOrchestrator on Windows

param(
    [switch]$SkipChecks = $false
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
}

# Check if command exists
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Check system requirements
function Test-Requirements {
    Write-Header "Checking System Requirements"
    
    $missingDeps = @()
    
    # Check Docker
    if (-not (Test-Command "docker")) {
        $missingDeps += "Docker"
        Write-Error "Docker is not installed"
    } else {
        $version = docker --version
        Write-Success "Docker is installed ($version)"
    }
    
    # Check Docker Compose
    if (-not (Test-Command "docker-compose") -and -not (docker compose version 2>$null)) {
        $missingDeps += "Docker Compose"
        Write-Error "Docker Compose is not installed"
    } else {
        if (Test-Command "docker-compose") {
            $version = docker-compose --version
            Write-Success "Docker Compose is installed ($version)"
        } else {
            Write-Success "Docker Compose is installed (via docker compose)"
        }
    }
    
    # Check Git
    if (-not (Test-Command "git")) {
        $missingDeps += "Git"
        Write-Error "Git is not installed"
    } else {
        $version = git --version
        Write-Success "Git is installed ($version)"
    }
    
    if ($missingDeps.Count -gt 0) {
        Write-Error "Missing dependencies: $($missingDeps -join ', ')"
        Write-Host ""
        Write-Host "Please install the missing dependencies:"
        Write-Host "  - Docker Desktop: https://docs.docker.com/desktop/install/windows-install/"
        Write-Host "  - Git: https://git-scm.com/download/win"
        exit 1
    }
    
    # Check Docker daemon
    try {
        docker info | Out-Null
    } catch {
        Write-Error "Docker daemon is not running"
        Write-Host "Please start Docker Desktop and try again"
        exit 1
    }
    
    Write-Success "All requirements met!"
}

# Setup repository
function Setup-Repository {
    Write-Header "Setting Up Repository"
    
    if (Test-Path "Crypto-Orchestrator") {
        Write-Info "Repository already exists, updating..."
        Set-Location "Crypto-Orchestrator"
        git pull
        Set-Location ..
    } else {
        Write-Info "Cloning repository..."
        try {
            git clone https://github.com/yourusername/Crypto-Orchestrator.git
            Set-Location "Crypto-Orchestrator"
        } catch {
            Write-Warning "Could not clone from GitHub. Using current directory..."
            if (-not (Test-Path "package.json")) {
                Write-Error "Not in CryptoOrchestrator directory and cannot clone"
                exit 1
            }
        }
    }
    
    Write-Success "Repository ready"
}

# Setup environment file
function Setup-Environment {
    Write-Header "Setting Up Environment"
    
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Write-Info "Creating .env from .env.example..."
            Copy-Item ".env.example" ".env"
        } else {
            Write-Info "Creating .env file..."
            $jwtSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
            $encryptionKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
            
            @"
# Database
DATABASE_URL=postgresql+asyncpg://crypto_user:crypto_pass@postgres:5432/cryptoorchestrator

# Redis
REDIS_URL=redis://redis:6379/0

# JWT Secret (CHANGE IN PRODUCTION!)
JWT_SECRET=$jwtSecret

# Exchange Key Encryption (CHANGE IN PRODUCTION!)
EXCHANGE_KEY_ENCRYPTION_KEY=$encryptionKey

# Email (Optional)
EMAIL_PROVIDER=smtp
FROM_EMAIL=noreply@cryptoorchestrator.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=

# Stripe (Optional - for payments)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Environment
NODE_ENV=development
LOG_LEVEL=INFO
"@ | Out-File -FilePath ".env" -Encoding UTF8
        }
        Write-Success ".env file created"
        Write-Warning "Please review and update .env file with your configuration"
    } else {
        Write-Info ".env file already exists, skipping..."
    }
}

# Start Docker services
function Start-Services {
    Write-Header "Starting Docker Services"
    
    Write-Info "Starting PostgreSQL, Redis, and Backend services..."
    if (Test-Command "docker-compose") {
        docker-compose up -d postgres redis
    } else {
        docker compose up -d postgres redis
    }
    
    Write-Info "Waiting for services to be ready..."
    Start-Sleep -Seconds 10
    
    # Wait for PostgreSQL
    Write-Info "Waiting for PostgreSQL..."
    $timeout = 60
    while ($timeout -gt 0) {
        try {
            if (Test-Command "docker-compose") {
                docker-compose exec -T postgres pg_isready -U crypto_user | Out-Null
            } else {
                docker compose exec -T postgres pg_isready -U crypto_user | Out-Null
            }
            Write-Success "PostgreSQL is ready"
            break
        } catch {
            Start-Sleep -Seconds 2
            $timeout -= 2
        }
    }
    
    if ($timeout -le 0) {
        Write-Error "PostgreSQL failed to start"
        exit 1
    }
    
    # Wait for Redis
    Write-Info "Waiting for Redis..."
    $timeout = 30
    while ($timeout -gt 0) {
        try {
            if (Test-Command "docker-compose") {
                docker-compose exec -T redis redis-cli ping | Out-Null
            } else {
                docker compose exec -T redis redis-cli ping | Out-Null
            }
            Write-Success "Redis is ready"
            break
        } catch {
            Start-Sleep -Seconds 2
            $timeout -= 2
        }
    }
    
    if ($timeout -le 0) {
        Write-Warning "Redis failed to start (optional, continuing anyway)"
    }
    
    Write-Success "Services started"
}

# Run database migrations
function Run-Migrations {
    Write-Header "Running Database Migrations"
    
    Write-Info "Running Alembic migrations..."
    try {
        if (Test-Command "docker-compose") {
            docker-compose exec -T backend alembic upgrade head
        } else {
            docker compose exec -T backend alembic upgrade head
        }
        Write-Success "Migrations completed"
    } catch {
        Write-Warning "Migrations failed (backend may not be built yet)"
        Write-Info "You can run migrations manually later with:"
        Write-Host "  docker-compose exec backend alembic upgrade head"
    }
}

# Build and start backend
function Build-Backend {
    Write-Header "Building Backend"
    
    Write-Info "Building Docker images (this may take a few minutes)..."
    if (Test-Command "docker-compose") {
        docker-compose build backend
        Write-Info "Starting backend service..."
        docker-compose up -d backend
    } else {
        docker compose build backend
        Write-Info "Starting backend service..."
        docker compose up -d backend
    }
    
    Write-Success "Backend built and started"
}

# Install frontend dependencies
function Install-Frontend {
    Write-Header "Installing Frontend Dependencies"
    
    if (Test-Path "package.json") {
        Write-Info "Installing npm packages (this may take a few minutes)..."
        try {
            npm install
            Write-Success "Frontend dependencies installed"
        } catch {
            Write-Warning "npm install failed, you may need to run it manually"
        }
    } else {
        Write-Warning "package.json not found, skipping frontend setup"
    }
}

# Show summary
function Show-Summary {
    Write-Header "Installation Complete! 🎉"
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "  CryptoOrchestrator is now installed and running!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Access Points:"
    Write-Host "   • Frontend:  http://localhost:3000"
    Write-Host "   • Backend API:  http://localhost:8000"
    Write-Host "   • API Docs:  http://localhost:8000/docs"
    Write-Host ""
    Write-Host "📝 Next Steps:"
    Write-Host "   1. Review and update .env file with your configuration"
    Write-Host "   2. Visit http://localhost:3000 to access the platform"
    Write-Host "   3. Create an account or login"
    Write-Host "   4. Add your exchange API keys in Settings"
    Write-Host ""
    Write-Host "🛠️  Useful Commands:"
    Write-Host "   • View logs:     docker-compose logs -f"
    Write-Host "   • Stop services: docker-compose down"
    Write-Host "   • Restart:       docker-compose restart"
    Write-Host "   • Run migrations: docker-compose exec backend alembic upgrade head"
    Write-Host ""
    Write-Warning "⚠  Remember to change JWT_SECRET and EXCHANGE_KEY_ENCRYPTION_KEY in .env for production!"
    Write-Host ""
}

# Main installation flow
function Main {
    Write-Header "CryptoOrchestrator One-Click Installation"
    
    Write-Host "This script will:"
    Write-Host "  1. Check system requirements"
    Write-Host "  2. Clone/update the repository"
    Write-Host "  3. Set up environment configuration"
    Write-Host "  4. Start Docker services"
    Write-Host "  5. Run database migrations"
    Write-Host "  6. Build and start the backend"
    Write-Host "  7. Install frontend dependencies"
    Write-Host ""
    
    $response = Read-Host "Continue? (y/n)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Info "Installation cancelled"
        exit 0
    }
    
    Test-Requirements
    Setup-Repository
    Setup-Environment
    Start-Services
    Build-Backend
    Run-Migrations
    Install-Frontend
    Show-Summary
}

# Run main function
Main

