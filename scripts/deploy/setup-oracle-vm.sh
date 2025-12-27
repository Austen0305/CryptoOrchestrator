#!/bin/bash

# CryptoOrchestrator - Oracle Cloud VM Setup Script
# This script sets up the complete application on Oracle Cloud Always Free VMs

set -e

echo "🚀 CryptoOrchestrator Oracle Cloud Setup"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Detect VM type (backend or frontend)
if [ "$1" == "backend" ]; then
    VM_TYPE="backend"
    echo "Setting up BACKEND VM (API + Database + Redis)"
elif [ "$1" == "frontend" ]; then
    VM_TYPE="frontend"
    echo "Setting up FRONTEND VM (React + Nginx)"
else
    print_error "Usage: $0 [backend|frontend]"
    exit 1
fi

echo ""

# Update system
print_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated"

# Install common dependencies
print_info "Installing common dependencies..."
sudo apt install -y curl wget git build-essential software-properties-common
print_success "Common dependencies installed"

if [ "$VM_TYPE" == "backend" ]; then
    # ============================================
    # BACKEND VM SETUP
    # ============================================
    
    print_info "Installing Python 3.12..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip
    print_success "Python 3.12 installed"
    
    print_info "Installing PostgreSQL..."
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
    print_success "PostgreSQL installed"
    
    print_info "Installing Redis..."
    sudo apt install -y redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    print_success "Redis installed"
    
    print_info "Installing Nginx (reverse proxy)..."
    sudo apt install -y nginx
    sudo systemctl enable nginx
    print_success "Nginx installed"
    
    # Configure PostgreSQL
    print_info "Configuring PostgreSQL..."
    sudo -u postgres psql << EOF
CREATE DATABASE cryptoorchestrator;
CREATE USER cryptouser WITH PASSWORD 'CHANGE_THIS_PASSWORD_123!';
GRANT ALL PRIVILEGES ON DATABASE cryptoorchestrator TO cryptouser;
\q
EOF
    print_success "PostgreSQL configured"
    
    # Configure Redis
    print_info "Configuring Redis..."
    sudo sed -i 's/^bind 127.0.0.1 ::1/bind 127.0.0.1/' /etc/redis/redis.conf
    sudo systemctl restart redis-server
    print_success "Redis configured"
    
    # Clone repository
    print_info "Cloning CryptoOrchestrator repository..."
    cd /home/ubuntu
    if [ -d "CryptoOrchestrator" ]; then
        cd CryptoOrchestrator
        git pull origin main
    else
        read -p "Enter GitHub repository URL: " REPO_URL
        git clone $REPO_URL
        cd CryptoOrchestrator
    fi
    cd Crypto-Orchestrator
    print_success "Repository ready"
    
    # Setup Python environment
    print_info "Setting up Python virtual environment..."
    python3.12 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Python environment ready"
    
    # Create .env file
    print_info "Creating environment configuration..."
    cat > .env << 'ENVEOF'
# CryptoOrchestrator Production Environment
# Oracle Cloud Backend VM

# Database
DATABASE_URL=postgresql+asyncpg://cryptouser:CHANGE_THIS_PASSWORD_123!@localhost:5432/cryptoorchestrator

# Redis
REDIS_URL=redis://localhost:6379/0

# Security Secrets (CHANGE THESE!)
JWT_SECRET=GENERATE_WITH_PYTHON_SECRETS
JWT_REFRESH_SECRET=GENERATE_WITH_PYTHON_SECRETS
EXCHANGE_KEY_ENCRYPTION_KEY=GENERATE_WITH_PYTHON_SECRETS
WALLET_ENCRYPTION_KEY=GENERATE_WITH_PYTHON_SECRETS

# App Configuration
NODE_ENV=production
PRODUCTION_MODE=true
PORT=8000
HOST=0.0.0.0

# CORS (Update with your frontend VM IP)
ALLOWED_ORIGINS=http://FRONTEND_VM_IP,https://yourdomain.com

# Optional (add when ready)
# STRIPE_SECRET_KEY=
# TWILIO_ACCOUNT_SID=
# TWILIO_AUTH_TOKEN=
# SENTRY_DSN=
ENVEOF
    print_success ".env file created"
    
    print_warning "IMPORTANT: Edit .env and update:"
    print_warning "  1. Database password"
    print_warning "  2. Generate secrets (see instructions below)"
    print_warning "  3. Update ALLOWED_ORIGINS with frontend VM IP"
    echo ""
    
    # Generate secrets
    print_info "Generating security secrets..."
    print_info "Run these commands and update .env:"
    echo ""
    echo "JWT_SECRET:"
    python3 -c "import secrets; print(secrets.token_urlsafe(64))"
    echo ""
    echo "JWT_REFRESH_SECRET:"
    python3 -c "import secrets; print(secrets.token_urlsafe(64))"
    echo ""
    echo "EXCHANGE_KEY_ENCRYPTION_KEY:"
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
    echo ""
    echo "WALLET_ENCRYPTION_KEY:"
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
    echo ""
    
    read -p "Press ENTER after you've updated .env..."
    
    # Run migrations
    print_info "Running database migrations..."
    source venv/bin/activate
    alembic upgrade head
    print_success "Migrations complete"
    
    # Create systemd service
    print_info "Creating systemd service..."
    sudo tee /etc/systemd/system/cryptoorchestrator.service > /dev/null << SERVICEEOF
[Unit]
Description=CryptoOrchestrator API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/CryptoOrchestrator/Crypto-Orchestrator
Environment="PATH=/home/ubuntu/CryptoOrchestrator/Crypto-Orchestrator/venv/bin"
ExecStart=/home/ubuntu/CryptoOrchestrator/Crypto-Orchestrator/venv/bin/uvicorn server_fastapi.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable cryptoorchestrator
    sudo systemctl start cryptoorchestrator
    print_success "Systemd service created and started"
    
    # Configure Nginx reverse proxy
    print_info "Configuring Nginx reverse proxy..."
    BACKEND_IP=$(curl -s ifconfig.me)
    sudo tee /etc/nginx/sites-available/cryptoorchestrator > /dev/null << NGINXEOF
server {
    listen 80;
    server_name $BACKEND_IP api.yourdomain.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /health {
        proxy_pass http://localhost:8000/api/health;
    }
}
NGINXEOF
    
    sudo ln -sf /etc/nginx/sites-available/cryptoorchestrator /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    print_success "Nginx configured"
    
    print_success "Backend VM setup complete!"
    echo ""
    print_info "Your backend API is running at:"
    print_info "  http://$BACKEND_IP/api/health"
    echo ""
    print_info "Next steps:"
    print_info "  1. Test API: curl http://$BACKEND_IP/api/health"
    print_info "  2. Setup frontend VM with this backend IP: $BACKEND_IP"
    print_info "  3. Configure firewall to allow ports 80, 443"
    print_info "  4. (Optional) Setup SSL with Let's Encrypt"
    
elif [ "$VM_TYPE" == "frontend" ]; then
    # ============================================
    # FRONTEND VM SETUP
    # ============================================
    
    print_info "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    print_success "Node.js installed ($(node --version))"
    
    print_info "Installing Nginx..."
    sudo apt install -y nginx
    sudo systemctl enable nginx
    print_success "Nginx installed"
    
    # Clone repository
    print_info "Cloning CryptoOrchestrator repository..."
    cd /home/ubuntu
    if [ -d "CryptoOrchestrator" ]; then
        cd CryptoOrchestrator
        git pull origin main
    else
        read -p "Enter GitHub repository URL: " REPO_URL
        git clone $REPO_URL
        cd CryptoOrchestrator
    fi
    cd Crypto-Orchestrator
    print_success "Repository ready"
    
    # Get backend IP
    print_info "Enter your BACKEND VM IP address:"
    read -p "Backend IP: " BACKEND_IP
    
    # Create production .env
    print_info "Creating production environment..."
    cat > client/.env.production << ENVEOF
VITE_API_URL=http://$BACKEND_IP/api
VITE_WS_URL=ws://$BACKEND_IP/ws
ENVEOF
    print_success "Environment configured"
    
    # Install dependencies and build
    print_info "Installing dependencies..."
    cd client
    npm install --legacy-peer-deps
    print_success "Dependencies installed"
    
    print_info "Building frontend..."
    npm run build
    print_success "Frontend built"
    
    # Configure Nginx
    print_info "Configuring Nginx..."
    FRONTEND_IP=$(curl -s ifconfig.me)
    sudo tee /etc/nginx/sites-available/default > /dev/null << NGINXEOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /home/ubuntu/CryptoOrchestrator/Crypto-Orchestrator/client/dist;
    index index.html;
    
    server_name $FRONTEND_IP yourdomain.com www.yourdomain.com;
    
    # Frontend
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # Proxy API requests to backend
    location /api {
        proxy_pass http://$BACKEND_IP:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    # Proxy WebSocket to backend
    location /ws {
        proxy_pass http://$BACKEND_IP:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
NGINXEOF
    
    sudo nginx -t
    sudo systemctl restart nginx
    print_success "Nginx configured"
    
    print_success "Frontend VM setup complete!"
    echo ""
    print_info "Your application is live at:"
    print_info "  http://$FRONTEND_IP"
    echo ""
    print_info "Next steps:"
    print_info "  1. Visit: http://$FRONTEND_IP"
    print_info "  2. Test API connection"
    print_info "  3. Configure firewall to allow ports 80, 443"
    print_info "  4. (Optional) Setup custom domain"
    print_info "  5. (Optional) Setup SSL with Let's Encrypt"
fi

echo ""
print_success "Setup complete! 🎉"
