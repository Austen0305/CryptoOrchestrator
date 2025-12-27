# Quick Start Script - Run All Tests
# Run this from the project root directory

Write-Host "🚀 CryptoOrchestrator - Quick Test Start" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (Test-Path "package.json") {
    Write-Host "✓ Found package.json - in project root" -ForegroundColor Green
}
else {
    Write-Host "✗ Not in project root. Please run from project root directory." -ForegroundColor Red
    Write-Host "  Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Running Playwright E2E tests..." -ForegroundColor Cyan
Write-Host ""

# Run Playwright tests
npm run test:e2e

Write-Host ""
Write-Host "✅ Test execution complete!" -ForegroundColor Green
Write-Host ""
Write-Host "For more options, see: tests/QUICK_START.md" -ForegroundColor Gray
