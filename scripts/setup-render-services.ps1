# Setup Render Services using Blueprint
# This script helps you deploy using render.yaml blueprint

Write-Host "🚀 Render Blueprint Deployment Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will help you deploy using Render's Blueprint feature." -ForegroundColor Yellow
Write-Host ""

# Check if render.yaml exists
if (-not (Test-Path "render.yaml")) {
    Write-Host "❌ render.yaml not found!" -ForegroundColor Red
    Write-Host "The render.yaml file should exist in the project root." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ render.yaml found" -ForegroundColor Green
Write-Host ""

Write-Host "To deploy using the Blueprint:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Go to https://dashboard.render.com" -ForegroundColor White
Write-Host "2. Click 'New +' → 'Blueprint'" -ForegroundColor White
Write-Host "3. Connect your GitHub account (if not already connected)" -ForegroundColor White
Write-Host "4. Select your repository: Crypto-Orchestrator" -ForegroundColor White
Write-Host "5. Render will automatically detect render.yaml" -ForegroundColor White
Write-Host "6. Review the services it will create:" -ForegroundColor White
Write-Host "   - PostgreSQL Database (crypto-orchestrator-db)" -ForegroundColor Gray
Write-Host "   - Redis Cache (crypto-orchestrator-redis)" -ForegroundColor Gray
Write-Host "   - FastAPI Backend (crypto-orchestrator-backend)" -ForegroundColor Gray
Write-Host "   - React Frontend (crypto-orchestrator-frontend)" -ForegroundColor Gray
Write-Host "7. Click 'Apply' to create all services" -ForegroundColor White
Write-Host "8. Wait for deployment (5-10 minutes)" -ForegroundColor White
Write-Host ""

Write-Host "After deployment:" -ForegroundColor Cyan
Write-Host "1. Run database migrations:" -ForegroundColor White
Write-Host "   - Go to backend service → Shell tab" -ForegroundColor Gray
Write-Host "   - Run: alembic upgrade head" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Set up Uptime Robot to keep services alive:" -ForegroundColor White
Write-Host "   - Go to https://uptimerobot.com" -ForegroundColor Gray
Write-Host "   - Add monitor for: https://crypto-orchestrator-backend.onrender.com/health" -ForegroundColor Gray
Write-Host "   - Interval: 5 minutes" -ForegroundColor Gray
Write-Host ""

Write-Host "Alternative: Manual Deployment" -ForegroundColor Cyan
Write-Host "If you prefer manual setup, follow QUICK_START_FREE_HOSTING.md" -ForegroundColor Yellow
Write-Host ""

$choice = Read-Host "Would you like to open Render dashboard now? (y/n)"
if ($choice -eq "y" -or $choice -eq "Y") {
    Start-Process "https://dashboard.render.com/blueprints"
}

Write-Host ""
Write-Host "✓ Setup instructions displayed" -ForegroundColor Green

