#!/bin/bash
# One-Command Setup Script for CryptoOrchestrator (Unix/Linux/macOS)
# This script sets up the entire development environment

set -e  # Exit on error

echo "🚀 CryptoOrchestrator - Automated Setup"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Functions for colored output
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

section() {
    echo -e "${CYAN}$1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check prerequisites
section "📋 Checking prerequisites..."
MISSING_DEPS=()

if ! command_exists node; then
    MISSING_DEPS+=("Node.js (v18+)")
fi

if ! command_exists python3 && ! command_exists python; then
    MISSING_DEPS+=("Python (3.12+)")
fi

if ! command_exists npm; then
    MISSING_DEPS+=("npm")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    error "Missing prerequisites:"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "  - $dep"
    done
    echo ""
    echo "Please install missing dependencies and run this script again."
    exit 1
fi

# Check versions
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    error "Node.js version 18+ required. Current: $(node --version)"
    exit 1
fi

PYTHON_CMD="python3"
if ! command_exists python3; then
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    error "Python 3.12+ required. Current: $PYTHON_VERSION"
    exit 1
fi

success "All prerequisites met"
echo ""

# Step 2: Create .env file if it doesn't exist
section "📝 Setting up environment variables..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        success "Created .env file from .env.example"
        info "Please review and update .env with your configuration"
    else
        error ".env.example not found. Cannot create .env file."
        exit 1
    fi
else
    info ".env file already exists, skipping creation"
fi
echo ""

# Step 3: Install Python dependencies
section "🐍 Installing Python dependencies..."
if [ -f requirements.txt ]; then
    $PYTHON_CMD -m pip install --upgrade pip
    $PYTHON_CMD -m pip install -r requirements.txt
    success "Python dependencies installed"
else
    error "requirements.txt not found"
    exit 1
fi
echo ""

# Step 4: Install Node.js dependencies
section "📦 Installing Node.js dependencies..."
if [ -f package.json ]; then
    npm install --legacy-peer-deps
    success "Node.js dependencies installed"
else
    error "package.json not found"
    exit 1
fi
echo ""

# Step 5: Create necessary directories
section "📁 Creating necessary directories..."
mkdir -p data
mkdir -p logs
mkdir -p models
success "Directories created"
echo ""

# Step 6: Initialize database
section "🗄️  Setting up database..."
if command_exists alembic; then
    # Check if database exists
    if [ -f data/app.db ]; then
        info "Database file already exists"
    else
        info "Creating database..."
    fi
    
    # Run migrations
    alembic upgrade head
    success "Database migrations applied"
else
    error "Alembic not found. Install it with: pip install alembic"
    exit 1
fi
echo ""

# Step 7: Generate secrets if needed
section "🔐 Checking security configuration..."
if grep -q "dev-secret-change-me-in-production" .env 2>/dev/null; then
    info "Generating secure secrets..."
    
    # Generate JWT secret
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
    
    # Generate encryption key
    ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
    
    # Update .env file (works on both Linux and macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" .env
        sed -i '' "s|EXCHANGE_KEY_ENCRYPTION_KEY=.*|EXCHANGE_KEY_ENCRYPTION_KEY=$ENCRYPTION_KEY|" .env
    else
        # Linux
        sed -i "s|JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" .env
        sed -i "s|EXCHANGE_KEY_ENCRYPTION_KEY=.*|EXCHANGE_KEY_ENCRYPTION_KEY=$ENCRYPTION_KEY|" .env
    fi
    
    success "Generated secure secrets"
else
    info "Secrets already configured"
fi
echo ""

# Step 8: Verify setup
section "✅ Verifying setup..."
if [ -f .env ] && [ -f requirements.txt ] && [ -d node_modules ]; then
    success "Setup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Review .env file and update any necessary values"
    echo "  2. Start the backend: npm run dev:fastapi"
    echo "  3. Start the frontend: npm run dev"
    echo "  4. Or start both with Electron: npm run electron"
    echo ""
    echo "For more information, see README.md"
else
    error "Setup verification failed"
    exit 1
fi
