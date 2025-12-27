# Secret Rotation Script for Production
# Generates new cryptographic secrets for security
# Uses the SecretRotationService for consistency

Write-Host "🔐 CryptoOrchestrator Secret Rotation" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.8+." -ForegroundColor Red
    exit 1
}

Write-Host "Generating new secrets using SecretRotationService..." -ForegroundColor Yellow
Write-Host ""

# Get script directory and project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Generate secrets using the SecretRotationService
$secrets = python -c @"
import sys
from pathlib import Path

# Add server_fastapi to path
project_root = Path(r'$projectRoot')
sys.path.insert(0, str(project_root / 'server_fastapi'))

from server_fastapi.services.secret_rotation import SecretRotationService

service = SecretRotationService()
secrets = service.generate_all_secrets()

# Add encryption key
secrets['EXCHANGE_KEY_ENCRYPTION_KEY'] = service.generate_encryption_key(32)

# Print in .env format
for key, value in secrets.items():
    print(f'{key}={value}')
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to generate secrets" -ForegroundColor Red
    Write-Host "   Make sure you're running from the project root" -ForegroundColor Yellow
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
Write-Host "  2. Update SENTRY_DSN if not already configured:" -ForegroundColor Yellow
Write-Host "     - Backend: SENTRY_DSN=https://your-dsn@sentry.io/project-id" -ForegroundColor Gray
Write-Host "     - Frontend: VITE_SENTRY_DSN=https://your-dsn@sentry.io/project-id" -ForegroundColor Gray
Write-Host "  3. Restart all services (backend, frontend, workers)" -ForegroundColor Yellow
Write-Host "  4. Store these secrets securely (do NOT commit to git)" -ForegroundColor Yellow
Write-Host "  5. Old secrets will stop working immediately" -ForegroundColor Yellow
Write-Host "  6. Users will need to log in again (JWT tokens invalidated)" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔄 Next rotation recommended in 90 days" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 See docs/SECRET_ROTATION_GUIDE.md for detailed instructions" -ForegroundColor Cyan
