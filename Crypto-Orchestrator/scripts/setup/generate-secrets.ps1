# ==========================================
# Generate Secrets for Production
# ==========================================
# Generates all required secrets for free stack deployment

Write-Host "🔐 Generating Production Secrets" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.8+ to generate secure secrets." -ForegroundColor Red
    exit 1
}

Write-Host "Generating secure random secrets..." -ForegroundColor Yellow
Write-Host ""

$secrets = python -c @"
import secrets

jwt_secret = secrets.token_urlsafe(64)
jwt_refresh = secrets.token_urlsafe(64)
encryption_key = secrets.token_urlsafe(32)

print(f'JWT_SECRET={jwt_secret}')
print(f'JWT_REFRESH_SECRET={jwt_refresh}')
print(f'EXCHANGE_KEY_ENCRYPTION_KEY={encryption_key}')
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to generate secrets" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Secrets generated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Copy these to your Koyeb environment variables:" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
$secrets | ForEach-Object { Write-Host $_ -ForegroundColor White }
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  IMPORTANT:" -ForegroundColor Red
Write-Host "  - Store these secrets securely" -ForegroundColor Yellow
Write-Host "  - Never commit them to git" -ForegroundColor Yellow
Write-Host "  - Use different secrets for production" -ForegroundColor Yellow
Write-Host "  - Rotate secrets every 90 days" -ForegroundColor Yellow
Write-Host ""
