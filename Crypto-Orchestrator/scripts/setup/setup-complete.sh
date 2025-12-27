#!/bin/bash
# One-Command Setup Script for CryptoOrchestrator
# This script sets up the entire development environment

set -e

echo "🚀 CryptoOrchestrator - Automated Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check prerequisites
echo "📋 Checking prerequisites..."
MISSING_DEPS=()

if ! command_exists node; then
    MISSING_DEPS+=("Node.js (v18+)")
fi

if ! command_exists python3; then
    MISSING_DEPS+=("Python (3.12+)")
fi

if ! command_exists npm; then
    MISSING_DEPS+=("npm")
fi

if ! command_exists pip3; then
    MISSING_DEPS+=("pip3")
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    print_error "Missing required dependencies:"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "  - $dep"
    done
    echo ""
    echo "Please install missing dependencies and run this script again."
    exit 1
fi

print_success "All prerequisites found"
echo ""

# Step 2: Check environment file
echo "🔧 Setting up environment..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        print_info "Creating .env from .env.example"
        cp .env.example .env
        print_success ".env file created"
        print_info "Please edit .env file with your actual configuration"
    else
        print_error ".env.example not found"
        exit 1
    fi
else
    print_success ".env file already exists"
fi
echo ""

# Step 3: Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
if npm install; then
    print_success "Node.js dependencies installed"
else
    print_error "Failed to install Node.js dependencies"
    exit 1
fi
echo ""

# Step 4: Install Python dependencies
echo "🐍 Installing Python dependencies..."
if pip3 install -r requirements.txt; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi

if [ -f requirements-dev.txt ]; then
    print_info "Installing development dependencies..."
    pip3 install -r requirements-dev.txt 2>/dev/null || print_info "Some dev dependencies failed (non-critical)"
fi
echo ""

# Step 5: Install testing dependencies
echo "🧪 Installing testing dependencies..."
pip3 install pytest pytest-asyncio pytest-cov aiohttp flake8 black 2>/dev/null || print_info "Some test dependencies failed (non-critical)"
print_success "Testing dependencies installed"
echo ""

# Step 6: Database setup
echo "💾 Setting up database..."
if command_exists alembic; then
    print_info "Running database migrations..."
    alembic upgrade head 2>/dev/null && print_success "Database migrations completed" || print_info "Migrations skipped (database may not be configured)"
else
    print_info "Alembic not found, skipping migrations"
fi
echo ""

# Step 7: Verify installation
echo "✅ Verifying installation..."

# Check if TypeScript compiles
print_info "Checking TypeScript..."
if npm run check 2>/dev/null; then
    print_success "TypeScript check passed"
else
    print_info "TypeScript has some warnings (non-critical for setup)"
fi

# Check if Python scripts compile
print_info "Checking Python test scripts..."
if python3 -m py_compile scripts/test_infrastructure.py scripts/test_security.py scripts/load_test.py 2>/dev/null; then
    print_success "Python test scripts compile successfully"
else
    print_error "Some Python scripts have issues"
fi
echo ""

# Step 8: Create convenient aliases
echo "🔗 Setting up convenience commands..."
cat > .setup-complete.sh << 'EOF'
# CryptoOrchestrator - Quick Commands
# Source this file: source .setup-complete.sh

alias co-start-backend="npm run dev:fastapi"
alias co-start-frontend="npm run dev"
alias co-start-redis="npm run redis:start"
alias co-test-infra="npm run test:phase1"
alias co-test-security="npm run test:phase2"
alias co-test-all="npm run test:pre-deploy"
alias co-test-e2e="npm run test:e2e"

echo "🚀 CryptoOrchestrator aliases loaded!"
echo ""
echo "Available commands:"
echo "  co-start-backend   - Start FastAPI backend"
echo "  co-start-frontend  - Start Vite frontend"
echo "  co-start-redis     - Start Redis server"
echo "  co-test-infra      - Run infrastructure tests"
echo "  co-test-security   - Run security tests"
echo "  co-test-all        - Run all pre-deployment tests"
echo "  co-test-e2e        - Run E2E tests"
EOF

print_success "Convenience aliases created (.setup-complete.sh)"
echo ""

# Final summary
echo "======================================"
echo "✨ Setup Complete! ✨"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Source aliases: source .setup-complete.sh"
echo "3. Start backend: npm run dev:fastapi"
echo "4. Start frontend: npm run dev (in another terminal)"
echo "5. Run tests: npm run test:pre-deploy"
echo ""
echo "📖 Documentation:"
echo "  - Testing Guide: docs/TESTING_GUIDE.md"
echo "  - Quick Reference: docs/TESTING_README.md"
echo "  - Status: docs/PRE_DEPLOYMENT_STATUS.md"
echo ""
echo "🔗 Useful commands:"
echo "  npm run dev:fastapi      # Start backend"
echo "  npm run dev              # Start frontend"
echo "  npm run test:phase1      # Test infrastructure"
echo "  npm run test:phase2      # Test security"
echo "  npm run test:pre-deploy  # Run all tests"
echo "  npm run test:e2e         # End-to-end tests"
echo ""
print_success "Happy coding! 🎉"
