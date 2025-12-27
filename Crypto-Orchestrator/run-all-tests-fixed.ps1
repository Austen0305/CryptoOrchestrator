# Run All Tests - Fixed Version
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running All E2E Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:BASE_URL = "http://localhost:5173"
$env:API_URL = "http://localhost:8000"

# Check if packages are installed
Write-Host "Verifying package installation..." -ForegroundColor Yellow
$playwrightInstalled = Test-Path "node_modules\@playwright\test\package.json"
$puppeteerInstalled = Test-Path "node_modules\puppeteer\package.json"

if ($playwrightInstalled) {
    Write-Host "Playwright: INSTALLED" -ForegroundColor Green
} else {
    Write-Host "Playwright: NOT INSTALLED - Installing..." -ForegroundColor Red
    npm install @playwright/test@1.57.0 --save-dev --legacy-peer-deps --force 2>&1 | Out-Null
    npx playwright install chromium --with-deps 2>&1 | Out-Null
}

if ($puppeteerInstalled) {
    Write-Host "Puppeteer: INSTALLED" -ForegroundColor Green
} else {
    Write-Host "Puppeteer: NOT INSTALLED - Installing..." -ForegroundColor Red
    npm install puppeteer@latest --save-dev --legacy-peer-deps --force 2>&1 | Out-Null
}

Write-Host ""
Write-Host "Checking servers..." -ForegroundColor Yellow

# Check backend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "Backend: RUNNING" -ForegroundColor Green
} catch {
    Write-Host "Backend: NOT RUNNING - Starting..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; `$env:TESTING='true'; python -m uvicorn server_fastapi.main:app --port 8000 --host 127.0.0.1" -WindowStyle Minimized
    Start-Sleep -Seconds 10
}

# Check frontend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "Frontend: RUNNING" -ForegroundColor Green
} catch {
    Write-Host "Frontend: NOT RUNNING - Starting..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev" -WindowStyle Minimized
    Start-Sleep -Seconds 12
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Playwright Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run Playwright tests
npx playwright test --reporter=list,html --timeout=60000 --max-failures=50

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Puppeteer Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run Puppeteer tests
node scripts/testing/run-puppeteer-tests.js

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Execution Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results:" -ForegroundColor Yellow
Write-Host "- Playwright: playwright-report/index.html" -ForegroundColor Cyan
Write-Host "- Puppeteer: test-results/puppeteer-results.json" -ForegroundColor Cyan
Write-Host "- Screenshots: test-results/" -ForegroundColor Cyan

