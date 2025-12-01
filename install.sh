#!/bin/bash

###############################################################################
# CryptoOrchestrator One-Click Installation Script
# This script automates the installation and setup of CryptoOrchestrator
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    print_header "Checking System Requirements"
    
    local missing_deps=()
    
    # Check Docker
    if ! command_exists docker; then
        missing_deps+=("docker")
        print_error "Docker is not installed"
    else
        print_success "Docker is installed ($(docker --version))"
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        missing_deps+=("docker-compose")
        print_error "Docker Compose is not installed"
    else
        if command_exists docker-compose; then
            print_success "Docker Compose is installed ($(docker-compose --version))"
        else
            print_success "Docker Compose is installed (via docker compose)"
        fi
    fi
    
    # Check Git
    if ! command_exists git; then
        missing_deps+=("git")
        print_error "Git is not installed"
    else
        print_success "Git is installed ($(git --version))"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install the missing dependencies:"
        echo "  - Docker: https://docs.docker.com/get-docker/"
        echo "  - Docker Compose: https://docs.docker.com/compose/install/"
        echo "  - Git: https://git-scm.com/downloads"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        echo "Please start Docker and try again"
        exit 1
    fi
    
    print_success "All requirements met!"
}

# Clone or update repository
setup_repository() {
    print_header "Setting Up Repository"
    
    if [ -d "Crypto-Orchestrator" ]; then
        print_info "Repository already exists, updating..."
        cd Crypto-Orchestrator
        git pull
        cd ..
    else
        print_info "Cloning repository..."
        git clone https://github.com/yourusername/Crypto-Orchestrator.git || {
            print_warning "Could not clone from GitHub. Using current directory..."
            if [ ! -f "package.json" ]; then
                print_error "Not in CryptoOrchestrator directory and cannot clone"
                exit 1
            fi
        }
        if [ -d "Crypto-Orchestrator" ]; then
            cd Crypto-Orchestrator
        fi
    fi
    
    print_success "Repository ready"
}

# Setup environment file
setup_environment() {
    print_header "Setting Up Environment"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_info "Creating .env from .env.example..."
            cp .env.example .env
        else
            print_info "Creating .env file..."
            cat > .env << EOF
# Database
DATABASE_URL=postgresql+asyncpg://crypto_user:crypto_pass@postgres:5432/cryptoorchestrator

# Redis
REDIS_URL=redis://redis:6379/0

# JWT Secret (CHANGE IN PRODUCTION!)
JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || echo "change-me-in-production-$(date +%s)")

# Exchange Key Encryption (CHANGE IN PRODUCTION!)
EXCHANGE_KEY_ENCRYPTION_KEY=$(openssl rand -hex 32 2>/dev/null || echo "change-me-in-production-$(date +%s)")

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
EOF
        fi
        print_success ".env file created"
        print_warning "Please review and update .env file with your configuration"
    else
        print_info ".env file already exists, skipping..."
    fi
}

# Start Docker services
start_services() {
    print_header "Starting Docker Services"
    
    print_info "Starting PostgreSQL, Redis, and Backend services..."
    docker-compose up -d postgres redis || docker compose up -d postgres redis
    
    print_info "Waiting for services to be ready..."
    sleep 10
    
    # Wait for PostgreSQL
    print_info "Waiting for PostgreSQL..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T postgres pg_isready -U crypto_user >/dev/null 2>&1 || \
           docker compose exec -T postgres pg_isready -U crypto_user >/dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "PostgreSQL failed to start"
        exit 1
    fi
    
    # Wait for Redis
    print_info "Waiting for Redis..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1 || \
           docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
            print_success "Redis is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_warning "Redis failed to start (optional, continuing anyway)"
    fi
    
    print_success "Services started"
}

# Run database migrations
run_migrations() {
    print_header "Running Database Migrations"
    
    print_info "Running Alembic migrations..."
    docker-compose exec -T backend alembic upgrade head || \
    docker compose exec -T backend alembic upgrade head || {
        print_warning "Migrations failed (backend may not be built yet)"
        print_info "You can run migrations manually later with:"
        echo "  docker-compose exec backend alembic upgrade head"
    }
    
    print_success "Migrations completed"
}

# Build and start backend
build_backend() {
    print_header "Building Backend"
    
    print_info "Building Docker images (this may take a few minutes)..."
    docker-compose build backend || docker compose build backend
    
    print_info "Starting backend service..."
    docker-compose up -d backend || docker compose up -d backend
    
    print_success "Backend built and started"
}

# Install frontend dependencies
install_frontend() {
    print_header "Installing Frontend Dependencies"
    
    if [ -f "package.json" ]; then
        print_info "Installing npm packages (this may take a few minutes)..."
        npm install || {
            print_warning "npm install failed, you may need to run it manually"
        }
        print_success "Frontend dependencies installed"
    else
        print_warning "package.json not found, skipping frontend setup"
    fi
}

# Final summary
show_summary() {
    print_header "Installation Complete! 🎉"
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  CryptoOrchestrator is now installed and running!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "📍 Access Points:"
    echo "   • Frontend:  http://localhost:3000"
    echo "   • Backend API:  http://localhost:8000"
    echo "   • API Docs:  http://localhost:8000/docs"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Review and update .env file with your configuration"
    echo "   2. Visit http://localhost:3000 to access the platform"
    echo "   3. Create an account or login"
    echo "   4. Add your exchange API keys in Settings"
    echo ""
    echo "🛠️  Useful Commands:"
    echo "   • View logs:     docker-compose logs -f"
    echo "   • Stop services: docker-compose down"
    echo "   • Restart:       docker-compose restart"
    echo "   • Run migrations: docker-compose exec backend alembic upgrade head"
    echo ""
    echo -e "${YELLOW}⚠  Remember to change JWT_SECRET and EXCHANGE_KEY_ENCRYPTION_KEY in .env for production!${NC}"
    echo ""
}

# Main installation flow
main() {
    print_header "CryptoOrchestrator One-Click Installation"
    
    echo "This script will:"
    echo "  1. Check system requirements"
    echo "  2. Clone/update the repository"
    echo "  3. Set up environment configuration"
    echo "  4. Start Docker services"
    echo "  5. Run database migrations"
    echo "  6. Build and start the backend"
    echo "  7. Install frontend dependencies"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi
    
    check_requirements
    setup_repository
    setup_environment
    start_services
    build_backend
    run_migrations
    install_frontend
    show_summary
}

# Run main function
main

