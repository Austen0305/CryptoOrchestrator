# Secret Rotation Script for Production
# Generates new cryptographic secrets for security

Write-Host "🔐 CryptoOrchestrator Secret Rotation" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.8+." -ForegroundColor Red
    exit 1
}

Write-Host "Generating new secrets..." -ForegroundColor Yellow
Write-Host ""

# Generate secrets using Python
$secrets = python -c @"
import secrets

# Generate secrets
jwt_secret = secrets.token_urlsafe(64)
db_key = secrets.token_urlsafe(32)
session_secret = secrets.token_urlsafe(32)
webhook_secret = secrets.token_urlsafe(32)

print(f'JWT_SECRET={jwt_secret}')
print(f'DATABASE_ENCRYPTION_KEY={db_key}')
print(f'SESSION_SECRET={session_secret}')
print(f'WEBHOOK_SECRET={webhook_secret}')
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to generate secrets" -ForegroundColor Red
    exit 1
}

Write-Host "✅ New secrets generated:" -ForegroundColor Green
Write-Host ""
Write-Host "Add these to your .env file:" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor Yellow
$secrets | ForEach-Object { Write-Host $_ -ForegroundColor White }
Write-Host ""

# Log rotation
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logEntry = "$timestamp - Secrets rotated"
Add-Content -Path ".secret_rotation_log" -Value $logEntry

Write-Host "📅 Rotation logged to .secret_rotation_log" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  IMPORTANT:" -ForegroundColor Red
Write-Host "  1. Update your .env file with the new secrets above" -ForegroundColor Yellow
Write-Host "  2. Restart all services" -ForegroundColor Yellow
Write-Host "  3. Store these secrets securely (do NOT commit to git)" -ForegroundColor Yellow
Write-Host "  4. Old secrets will stop working immediately" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔄 Next rotation recommended in 90 days" -ForegroundColor Cyan
