#!/bin/bash
# Setup script for free hosting deployment
# This script helps generate secrets and prepare environment variables

set -e

echo "🚀 CryptoOrchestrator Free Hosting Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if openssl is available
if command -v openssl &> /dev/null; then
    echo -e "${GREEN}✓${NC} OpenSSL found"
    GENERATE_SECRET="openssl rand -hex 32"
else
    echo -e "${YELLOW}⚠${NC} OpenSSL not found, using alternative method"
    GENERATE_SECRET="python -c 'import secrets; print(secrets.token_hex(32))'"
fi

echo ""
echo "Generating secrets..."
echo ""

# Generate secrets
JWT_SECRET=$(eval $GENERATE_SECRET)
JWT_REFRESH_SECRET=$(eval $GENERATE_SECRET)
ENCRYPTION_KEY=$(eval $GENERATE_SECRET | cut -c1-32)

echo -e "${GREEN}✓${NC} Secrets generated"
echo ""

# Create .env.production file
cat > .env.production << EOF
# CryptoOrchestrator Production Environment Variables
# Generated on $(date)

# Database (Update with your database URL)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database

# Redis (Update with your Redis URL)
REDIS_URL=redis://:password@host:6379/0

# JWT Secrets
JWT_SECRET=$JWT_SECRET
JWT_REFRESH_SECRET=$JWT_REFRESH_SECRET

# Encryption Key
EXCHANGE_KEY_ENCRYPTION_KEY=$ENCRYPTION_KEY

# Application
PORT=8000
ENVIRONMENT=production
NODE_ENV=production

# Frontend API URL (Update with your backend URL)
VITE_API_URL=https://your-backend-url.onrender.com

# Optional: Stripe (if using payments)
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_PUBLISHABLE_KEY=pk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...

# Optional: Email (if using SMTP)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# SMTP_FROM_EMAIL=your-email@gmail.com

# Optional: Sentry (error tracking)
# SENTRY_DSN=https://...
EOF

echo -e "${GREEN}✓${NC} Created .env.production file"
echo ""
echo -e "${YELLOW}⚠${NC}  Remember to:"
echo "  1. Update DATABASE_URL with your actual database connection string"
echo "  2. Update REDIS_URL with your actual Redis connection string"
echo "  3. Update VITE_API_URL with your backend URL after deployment"
echo ""
echo -e "${GREEN}Done!${NC} Your .env.production file is ready."
echo ""

