#!/bin/bash

# CryptoOrchestrator - Free Vercel Deployment Script
# This script automates the entire deployment process for free

set -e

echo "🚀 CryptoOrchestrator Free Deployment Script"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo ""

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi
print_success "Node.js is installed ($(node --version))"

if ! command_exists npm; then
    print_error "npm is not installed"
    exit 1
fi
print_success "npm is installed ($(npm --version))"

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.10+ from https://python.org"
    exit 1
fi
print_success "Python 3 is installed ($(python3 --version))"

if ! command_exists git; then
    print_error "Git is not installed. Please install Git from https://git-scm.com"
    exit 1
fi
print_success "Git is installed ($(git --version))"

echo ""

# Step 2: Check if Vercel CLI is installed
echo "Step 2: Checking Vercel CLI..."
echo ""

if ! command_exists vercel; then
    print_warning "Vercel CLI not found. Installing..."
    npm install -g vercel
    print_success "Vercel CLI installed"
else
    print_success "Vercel CLI is installed ($(vercel --version))"
fi

echo ""

# Step 3: Login to Vercel
echo "Step 3: Logging into Vercel..."
echo ""
print_info "Please login to Vercel (use GitHub login for free tier)"
vercel login

echo ""

# Step 4: Collect database credentials
echo "Step 4: Setting up database and Redis..."
echo ""

print_info "You need to create free accounts and get credentials:"
print_info ""
print_info "1. Supabase (Database): https://supabase.com"
print_info "   - Sign in with GitHub"
print_info "   - Create new project"
print_info "   - Copy DATABASE_URL from Settings → Database"
print_info ""
print_info "2. Upstash (Redis): https://upstash.com"
print_info "   - Sign in with GitHub"
print_info "   - Create Redis database"
print_info "   - Copy REDIS_URL from dashboard"
print_info ""

read -p "Press ENTER when you have your credentials ready..."

echo ""
read -p "Enter Supabase DATABASE_URL: " DATABASE_URL
read -p "Enter Upstash REDIS_URL: " REDIS_URL

echo ""

# Step 5: Generate secrets
echo "Step 5: Generating security secrets..."
echo ""

if command_exists python3; then
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    JWT_REFRESH_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    WALLET_ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    print_success "Secrets generated successfully"
else
    print_error "Python 3 not found. Cannot generate secrets."
    exit 1
fi

echo ""

# Step 6: Create .env file for local testing
echo "Step 6: Creating .env file..."
echo ""

cat > .env << EOF
# CryptoOrchestrator Environment Variables
# Generated: $(date)

# Database
DATABASE_URL=$DATABASE_URL

# Redis
REDIS_URL=$REDIS_URL

# Security Secrets
JWT_SECRET=$JWT_SECRET
JWT_REFRESH_SECRET=$JWT_REFRESH_SECRET
EXCHANGE_KEY_ENCRYPTION_KEY=$ENCRYPTION_KEY
WALLET_ENCRYPTION_KEY=$WALLET_ENCRYPTION_KEY

# App Configuration
NODE_ENV=production
PRODUCTION_MODE=true

# Optional (add later if you have them)
# STRIPE_SECRET_KEY=
# TWILIO_ACCOUNT_SID=
# TWILIO_AUTH_TOKEN=
# TWILIO_FROM_NUMBER=
# SENTRY_DSN=
EOF

print_success ".env file created"

# Copy to client directory
cp .env client/.env.local
print_success "Client .env.local created"

echo ""

# Step 7: Install dependencies
echo "Step 7: Installing dependencies..."
echo ""

print_info "Installing backend dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    print_success "Backend dependencies installed"
else
    print_warning "requirements.txt not found, skipping..."
fi

print_info "Installing frontend dependencies..."
cd client
npm install --legacy-peer-deps
cd ..
print_success "Frontend dependencies installed"

echo ""

# Step 8: Build frontend
echo "Step 8: Building frontend..."
echo ""

cd client
npm run build
cd ..
print_success "Frontend built successfully"

echo ""

# Step 9: Create Vercel configuration
echo "Step 9: Creating Vercel configuration..."
echo ""

cat > vercel.json << EOF
{
  "version": 2,
  "builds": [
    {
      "src": "server_fastapi/main.py",
      "use": "@vercel/python"
    },
    {
      "src": "client/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "client/dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "server_fastapi/main.py"
    },
    {
      "src": "/(.*)",
      "dest": "client/dist/\$1"
    }
  ],
  "env": {
    "NODE_ENV": "production",
    "PRODUCTION_MODE": "true"
  }
}
EOF

print_success "vercel.json created"

echo ""

# Step 10: Deploy to Vercel
echo "Step 10: Deploying to Vercel..."
echo ""

print_info "Deploying application..."
vercel --prod

echo ""
print_success "Application deployed to Vercel!"

echo ""

# Step 11: Set environment variables
echo "Step 11: Setting environment variables..."
echo ""

print_info "Setting environment variables on Vercel..."

# Get project name
PROJECT_NAME=$(vercel ls | grep -m 1 'https://' | awk '{print $2}')

vercel env add DATABASE_URL production <<< "$DATABASE_URL"
vercel env add REDIS_URL production <<< "$REDIS_URL"
vercel env add JWT_SECRET production <<< "$JWT_SECRET"
vercel env add JWT_REFRESH_SECRET production <<< "$JWT_REFRESH_SECRET"
vercel env add EXCHANGE_KEY_ENCRYPTION_KEY production <<< "$ENCRYPTION_KEY"
vercel env add WALLET_ENCRYPTION_KEY production <<< "$WALLET_ENCRYPTION_KEY"
vercel env add NODE_ENV production <<< "production"
vercel env add PRODUCTION_MODE production <<< "true"

print_success "Environment variables set"

echo ""

# Step 12: Redeploy with environment variables
echo "Step 12: Redeploying with environment variables..."
echo ""

vercel --prod

print_success "Redeployment complete"

echo ""

# Step 13: Run database migrations
echo "Step 13: Running database migrations..."
echo ""

print_info "Attempting to run migrations..."

# Check if alembic is available
if command_exists alembic; then
    alembic upgrade head
    print_success "Migrations completed"
else
    print_warning "Alembic not found. Please run migrations manually:"
    print_info "  cd Crypto-Orchestrator"
    print_info "  pip install alembic"
    print_info "  alembic upgrade head"
fi

echo ""

# Step 14: Get deployment URL
echo "Step 14: Getting deployment URL..."
echo ""

DEPLOYMENT_URL=$(vercel ls | grep -m 1 'https://' | awk '{print $1}')

if [ -z "$DEPLOYMENT_URL" ]; then
    print_warning "Could not automatically detect deployment URL"
    print_info "Check your Vercel dashboard: https://vercel.com/dashboard"
else
    print_success "Deployment URL: $DEPLOYMENT_URL"
fi

echo ""

# Final summary
echo "=============================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "=============================================="
echo ""
print_success "Your CryptoOrchestrator is now live!"
echo ""
print_info "Deployment URL: $DEPLOYMENT_URL"
print_info "API Health Check: $DEPLOYMENT_URL/api/health"
print_info ""
print_info "Next steps:"
print_info "1. Visit your deployment URL"
print_info "2. Test user registration"
print_info "3. Create a bot"
print_info "4. Start trading!"
echo ""
print_info "Configuration saved to:"
print_info "  - .env (local)"
print_info "  - client/.env.local (frontend)"
print_info "  - Vercel dashboard (production)"
echo ""
print_warning "IMPORTANT: Add .env to .gitignore to prevent committing secrets!"
echo ""
print_success "Happy Trading! 🚀📈💰"
echo ""

# Save deployment info
cat > deployment-info.txt << EOF
CryptoOrchestrator Deployment Information
=========================================
Deployment Date: $(date)
Deployment URL: $DEPLOYMENT_URL
Platform: Vercel (Free Tier)
Database: Supabase
Redis: Upstash

API Endpoints:
- Health Check: $DEPLOYMENT_URL/api/health
- API Docs: $DEPLOYMENT_URL/api/docs

Next Steps:
1. Test deployment: $DEPLOYMENT_URL
2. Monitor logs: vercel logs
3. Update code: git push (auto-deploys)

Support:
- Vercel Dashboard: https://vercel.com/dashboard
- Supabase Dashboard: https://app.supabase.com
- Upstash Dashboard: https://console.upstash.com
EOF

print_success "Deployment info saved to deployment-info.txt"

# Open browser
if command_exists xdg-open; then
    xdg-open "$DEPLOYMENT_URL"
elif command_exists open; then
    open "$DEPLOYMENT_URL"
elif command_exists start; then
    start "$DEPLOYMENT_URL"
fi

echo ""
echo "Script completed successfully! ✅"
