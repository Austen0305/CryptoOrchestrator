# Complete Setup Script for Windows
# One-command setup for CryptoOrchestrator

$ErrorActionPreference = "Stop"

Write-Host "🚀 CryptoOrchestrator Complete Setup (Windows)" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Check Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
  exit 1
}
Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green

# Check Node.js
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
  exit 1
}
Write-Host "✅ Found: $nodeVersion" -ForegroundColor Green

# Run Python setup script
Write-Host "`n📦 Running complete setup..." -ForegroundColor Cyan
python scripts/setup/complete_setup.py

if ($LASTEXITCODE -ne 0) {
  Write-Host "`n❌ Setup failed. Check errors above." -ForegroundColor Red
  exit 1
}

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Start services: npm run start:all" -ForegroundColor White
Write-Host "  2. Verify health: npm run setup:health" -ForegroundColor White
Write-Host "  3. Verify features: npm run setup:verify" -ForegroundColor White
