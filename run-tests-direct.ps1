# Direct test execution script
$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running E2E Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment
$env:BASE_URL = "http://localhost:5173"
$env:API_URL = "http://localhost:8000"

# Check Puppeteer
Write-Host "Checking Puppeteer..." -ForegroundColor Yellow
if (Test-Path "node_modules\puppeteer\package.json") {
    Write-Host "[OK] Puppeteer found" -ForegroundColor Green
    Write-Host "`nRunning Puppeteer tests..." -ForegroundColor Cyan
    node scripts/testing/run-puppeteer-tests.js
} else {
    Write-Host "[SKIP] Puppeteer not installed" -ForegroundColor Yellow
    Write-Host "Installing Puppeteer..." -ForegroundColor Yellow
    npm install puppeteer@latest --save-dev --legacy-peer-deps --no-save 2>&1 | Out-Null
    if (Test-Path "node_modules\puppeteer\package.json") {
        Write-Host "[OK] Puppeteer installed" -ForegroundColor Green
        Write-Host "Running Puppeteer tests..." -ForegroundColor Cyan
        node scripts/testing/run-puppeteer-tests.js
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Checking Playwright..." -ForegroundColor Yellow

# Check Playwright
if (Test-Path "node_modules\@playwright\test\package.json") {
    Write-Host "[OK] Playwright found" -ForegroundColor Green
    Write-Host "`nRunning Playwright tests..." -ForegroundColor Cyan
    npx playwright test --reporter=list --timeout=60000 --max-failures=20
} else {
    Write-Host "[SKIP] Playwright not installed" -ForegroundColor Yellow
    Write-Host "Installing Playwright..." -ForegroundColor Yellow
    npm install @playwright/test@latest playwright@latest --save-dev --legacy-peer-deps --no-save 2>&1 | Out-Null
    if (Test-Path "node_modules\@playwright\test\package.json") {
        Write-Host "[OK] Playwright installed" -ForegroundColor Green
        Write-Host "Installing Chromium..." -ForegroundColor Yellow
        npx playwright install chromium 2>&1 | Out-Null
        Write-Host "Running Playwright tests..." -ForegroundColor Cyan
        npx playwright test --reporter=list --timeout=60000 --max-failures=20
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Tests Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

