# CryptoOrchestrator - Free Vercel Deployment Script (PowerShell)
# This script automates the entire deployment process for free

$ErrorActionPreference = "Stop"

Write-Host "🚀 CryptoOrchestrator Free Deployment Script" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Step 1: Check prerequisites
Write-Host "Step 1: Checking prerequisites..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Command "node")) {
    Write-Error "Node.js is not installed. Please install Node.js 18+ from https://nodejs.org"
    exit 1
}
Write-Success "Node.js is installed ($(node --version))"

if (-not (Test-Command "npm")) {
    Write-Error "npm is not installed"
    exit 1
}
Write-Success "npm is installed ($(npm --version))"

if (-not (Test-Command "python")) {
    Write-Error "Python 3 is not installed. Please install Python 3.10+ from https://python.org"
    exit 1
}
Write-Success "Python 3 is installed ($(python --version))"

if (-not (Test-Command "git")) {
    Write-Error "Git is not installed. Please install Git from https://git-scm.com"
    exit 1
}
Write-Success "Git is installed ($(git --version))"

Write-Host ""

# Step 2: Check if Vercel CLI is installed
Write-Host "Step 2: Checking Vercel CLI..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Command "vercel")) {
    Write-Warning "Vercel CLI not found. Installing..."
    npm install -g vercel
    Write-Success "Vercel CLI installed"
} else {
    Write-Success "Vercel CLI is installed"
}

Write-Host ""

# Step 3: Login to Vercel
Write-Host "Step 3: Logging into Vercel..." -ForegroundColor Cyan
Write-Host ""
Write-Info "Please login to Vercel (use GitHub login for free tier)"
vercel login

Write-Host ""

# Step 4: Collect database credentials
Write-Host "Step 4: Setting up database and Redis..." -ForegroundColor Cyan
Write-Host ""

Write-Info "You need to create free accounts and get credentials:"
Write-Info ""
Write-Info "1. Supabase (Database): https://supabase.com"
Write-Info "   - Sign in with GitHub"
Write-Info "   - Create new project"
Write-Info "   - Copy DATABASE_URL from Settings → Database"
Write-Info ""
Write-Info "2. Upstash (Redis): https://upstash.com"
Write-Info "   - Sign in with GitHub"
Write-Info "   - Create Redis database"
Write-Info "   - Copy REDIS_URL from dashboard"
Write-Info ""

Read-Host "Press ENTER when you have your credentials ready"

Write-Host ""
$DATABASE_URL = Read-Host "Enter Supabase DATABASE_URL"
$REDIS_URL = Read-Host "Enter Upstash REDIS_URL"

Write-Host ""

# Step 5: Generate secrets
Write-Host "Step 5: Generating security secrets..." -ForegroundColor Cyan
Write-Host ""

$JWT_SECRET = python -c "import secrets; print(secrets.token_urlsafe(64))"
$JWT_REFRESH_SECRET = python -c "import secrets; print(secrets.token_urlsafe(64))"
$ENCRYPTION_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
$WALLET_ENCRYPTION_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"

Write-Success "Secrets generated successfully"

Write-Host ""

# Step 6: Create .env file
Write-Host "Step 6: Creating .env file..." -ForegroundColor Cyan
Write-Host ""

$envContent = @"
# CryptoOrchestrator Environment Variables
# Generated: $(Get-Date)

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
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Success ".env file created"

# Copy to client directory
Copy-Item ".env" "client\.env.local"
Write-Success "Client .env.local created"

Write-Host ""

# Step 7: Install dependencies
Write-Host "Step 7: Installing dependencies..." -ForegroundColor Cyan
Write-Host ""

Write-Info "Installing backend dependencies..."
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Success "Backend dependencies installed"
} else {
    Write-Warning "requirements.txt not found, skipping..."
}

Write-Info "Installing frontend dependencies..."
Set-Location client
npm install --legacy-peer-deps
Set-Location ..
Write-Success "Frontend dependencies installed"

Write-Host ""

# Step 8: Build frontend
Write-Host "Step 8: Building frontend..." -ForegroundColor Cyan
Write-Host ""

Set-Location client
npm run build
Set-Location ..
Write-Success "Frontend built successfully"

Write-Host ""

# Step 9: Create Vercel configuration
Write-Host "Step 9: Creating Vercel configuration..." -ForegroundColor Cyan
Write-Host ""

$vercelConfig = @"
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
      "dest": "client/dist/`$1"
    }
  ],
  "env": {
    "NODE_ENV": "production",
    "PRODUCTION_MODE": "true"
  }
}
"@

$vercelConfig | Out-File -FilePath "vercel.json" -Encoding UTF8
Write-Success "vercel.json created"

Write-Host ""

# Step 10: Deploy to Vercel
Write-Host "Step 10: Deploying to Vercel..." -ForegroundColor Cyan
Write-Host ""

Write-Info "Deploying application..."
vercel --prod

Write-Host ""
Write-Success "Application deployed to Vercel!"

Write-Host ""

# Step 11: Set environment variables
Write-Host "Step 11: Setting environment variables..." -ForegroundColor Cyan
Write-Host ""

Write-Info "Setting environment variables on Vercel..."

Write-Info "Please set these environment variables manually in Vercel dashboard:"
Write-Info "https://vercel.com/dashboard → Your Project → Settings → Environment Variables"
Write-Info ""
Write-Info "Required variables:"
Write-Host "DATABASE_URL=$DATABASE_URL" -ForegroundColor Yellow
Write-Host "REDIS_URL=$REDIS_URL" -ForegroundColor Yellow
Write-Host "JWT_SECRET=$JWT_SECRET" -ForegroundColor Yellow
Write-Host "JWT_REFRESH_SECRET=$JWT_REFRESH_SECRET" -ForegroundColor Yellow
Write-Host "EXCHANGE_KEY_ENCRYPTION_KEY=$ENCRYPTION_KEY" -ForegroundColor Yellow
Write-Host "WALLET_ENCRYPTION_KEY=$WALLET_ENCRYPTION_KEY" -ForegroundColor Yellow
Write-Info ""

Read-Host "Press ENTER after you've added the environment variables in Vercel dashboard"

Write-Host ""

# Step 12: Redeploy
Write-Host "Step 12: Redeploying with environment variables..." -ForegroundColor Cyan
Write-Host ""

vercel --prod

Write-Success "Redeployment complete"

Write-Host ""

# Step 13: Get deployment URL
Write-Host "Step 13: Getting deployment info..." -ForegroundColor Cyan
Write-Host ""

Write-Info "Check your deployment at: https://vercel.com/dashboard"

Write-Host ""

# Final summary
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Success "Your CryptoOrchestrator is now live!"
Write-Host ""
Write-Info "Next steps:"
Write-Info "1. Visit your deployment URL (check Vercel dashboard)"
Write-Info "2. Test API: https://your-app.vercel.app/api/health"
Write-Info "3. Test user registration"
Write-Info "4. Create a bot"
Write-Info "5. Start trading!"
Write-Host ""
Write-Warning "IMPORTANT: Add .env to .gitignore to prevent committing secrets!"
Write-Host ""
Write-Success "Happy Trading! 🚀📈💰"
Write-Host ""

# Save deployment info
$deploymentInfo = @"
CryptoOrchestrator Deployment Information
=========================================
Deployment Date: $(Get-Date)
Platform: Vercel (Free Tier)
Database: Supabase
Redis: Upstash

Check your deployment at: https://vercel.com/dashboard

Next Steps:
1. Test deployment
2. Monitor logs: vercel logs
3. Update code: git push (auto-deploys)

Support:
- Vercel Dashboard: https://vercel.com/dashboard
- Supabase Dashboard: https://app.supabase.com
- Upstash Dashboard: https://console.upstash.com
"@

$deploymentInfo | Out-File -FilePath "deployment-info.txt" -Encoding UTF8
Write-Success "Deployment info saved to deployment-info.txt"

Write-Host ""
Write-Host "Script completed successfully! ✅" -ForegroundColor Green
