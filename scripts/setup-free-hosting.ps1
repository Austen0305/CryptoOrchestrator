# PowerShell script for free hosting deployment setup
# This script helps generate secrets and prepare environment variables

Write-Host "🚀 CryptoOrchestrator Free Hosting Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to generate random string
function Generate-RandomString {
    param([int]$Length = 32)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    $random = New-Object System.Random
    $result = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $result += $chars[$random.Next(0, $chars.Length)]
    }
    return $result
}

# Function to generate hex string
function Generate-HexString {
    param([int]$Length = 64)
    $bytes = New-Object byte[] ($Length / 2)
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    return ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
}

Write-Host "Generating secrets..." -ForegroundColor Yellow
Write-Host ""

# Generate secrets
$JWT_SECRET = Generate-HexString -Length 64
$JWT_REFRESH_SECRET = Generate-HexString -Length 64
$ENCRYPTION_KEY = Generate-HexString -Length 64

Write-Host "✓ Secrets generated" -ForegroundColor Green
Write-Host ""

# Create .env.production file
$envContent = @"
# CryptoOrchestrator Production Environment Variables
# Generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

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
"@

$envContent | Out-File -FilePath ".env.production" -Encoding UTF8

Write-Host "✓ Created .env.production file" -ForegroundColor Green
Write-Host ""
Write-Host "⚠  Remember to:" -ForegroundColor Yellow
Write-Host "  1. Update DATABASE_URL with your actual database connection string"
Write-Host "  2. Update REDIS_URL with your actual Redis connection string"
Write-Host "  3. Update VITE_API_URL with your backend URL after deployment"
Write-Host ""
Write-Host "Done! Your .env.production file is ready." -ForegroundColor Green
Write-Host ""

