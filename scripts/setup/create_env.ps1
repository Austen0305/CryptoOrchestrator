# Create .env file for local development
$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot ".env"

Write-Host "🔐 Generating .env file for local development..." -ForegroundColor Cyan

# Generate secrets using Python
$jwtSecret = python -c "import secrets; print(secrets.token_urlsafe(64))" 2>&1 | Out-String
$encKey = python -c "import secrets; print(secrets.token_urlsafe(32))" 2>&1 | Out-String

$jwtSecret = $jwtSecret.Trim()
$encKey = $encKey.Trim()

# Create .env content
$envContent = @"
# CryptoOrchestrator Local Development Environment
# Generated automatically - DO NOT COMMIT TO GIT
# This file contains sensitive information

# Application Environment
NODE_ENV=development
PORT=8000
HOST=0.0.0.0

# Database Configuration (SQLite for local development)
DATABASE_URL=sqlite+aiosqlite:///./crypto_orchestrator.db

# Security Secrets (Generated securely)
JWT_SECRET=$jwtSecret
EXCHANGE_KEY_ENCRYPTION_KEY=$encKey

# Redis Configuration (Optional - app works without it)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# Trading Configuration
DEFAULT_TRADING_MODE=paper
ENABLE_MOCK_DATA=true
PRODUCTION_MODE=false

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000

# Optional: Exchange Testnet API Keys (add when ready)
# BINANCE_TESTNET_API_KEY=
# BINANCE_TESTNET_API_SECRET=
# BINANCE_TESTNET_BASE_URL=https://testnet.binancefuture.com
# COINBASE_SANDBOX_API_KEY=
# COINBASE_SANDBOX_API_SECRET=
# COINBASE_SANDBOX_BASE_URL=https://api-public.sandbox.exchange.coinbase.com

# Optional: CoinGecko API (free tier, no key required)
# COINGECKO_API_KEY=

# Optional: Stripe (for payment testing)
# STRIPE_SECRET_KEY=
# STRIPE_PUBLISHABLE_KEY=
# STRIPE_WEBHOOK_SECRET=

# Optional: Email Configuration
# SMTP_HOST=
# SMTP_PORT=587
# SMTP_USER=
# SMTP_PASSWORD=
# SMTP_FROM=

# Optional: Monitoring
# SENTRY_DSN=
# ENABLE_SENTRY=false
"@

# Write .env file
try {
    $envContent | Out-File -FilePath $envFile -Encoding utf8 -NoNewline
    Write-Host "✅ Created .env file at: $envFile" -ForegroundColor Green
    Write-Host "✅ Generated secure secrets" -ForegroundColor Green
    Write-Host "⚠️  IMPORTANT: Keep these secrets secure and never commit .env to git!" -ForegroundColor Yellow
}
catch {
    Write-Host "❌ Error creating .env file: $_" -ForegroundColor Red
    exit 1
}
    Write-Host "⚠️  IMPORTANT: Keep these secrets secure and never commit .env to git!" -ForegroundColor Yellow
}
catch {
    Write-Host "❌ Error creating .env file: $_" -ForegroundColor Red
    exit 1
}
