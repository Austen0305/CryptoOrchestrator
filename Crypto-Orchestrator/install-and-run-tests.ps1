# Install and Run All Tests (Playwright + Puppeteer)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing and Running All E2E Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install Playwright
Write-Host "Step 1: Installing Playwright..." -ForegroundColor Yellow
npm install @playwright/test@1.57.0 --save-dev --legacy-peer-deps --force --no-audit 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Playwright installed" -ForegroundColor Green
} else {
    Write-Host "Playwright installation had issues" -ForegroundColor Red
}

# Step 2: Install Puppeteer
Write-Host "Step 2: Installing Puppeteer..." -ForegroundColor Yellow
npm install puppeteer@latest --save-dev --legacy-peer-deps --force --no-audit 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Puppeteer installed" -ForegroundColor Green
} else {
    Write-Host "Puppeteer installation had issues" -ForegroundColor Red
}

# Step 3: Install Playwright browsers
Write-Host "Step 3: Installing Playwright browsers..." -ForegroundColor Yellow
npx playwright install chromium --with-deps 2>&1 | Out-Null
Write-Host "Browser installation attempted" -ForegroundColor Green

# Step 4: Check servers
Write-Host ""
Write-Host "Step 4: Checking servers..." -ForegroundColor Yellow
$backendRunning = $false
$frontendRunning = $false

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    $backendRunning = $true
    Write-Host "Backend server is running" -ForegroundColor Green
} catch {
    Write-Host "Backend server is not running" -ForegroundColor Red
    Write-Host "Starting backend server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; `$env:TESTING='true'; python -m uvicorn server_fastapi.main:app --port 8000 --host 127.0.0.1" -WindowStyle Minimized
    Start-Sleep -Seconds 10
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction Stop
    $frontendRunning = $true
    Write-Host "Frontend server is running" -ForegroundColor Green
} catch {
    Write-Host "Frontend server is not running" -ForegroundColor Red
    Write-Host "Starting frontend server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev" -WindowStyle Minimized
    Start-Sleep -Seconds 12
}

Write-Host ""
Write-Host "Step 5: Running Playwright tests..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
$env:BASE_URL = "http://localhost:5173"
$env:API_URL = "http://localhost:8000"
npx playwright test --reporter=list,html --timeout=60000 --max-failures=50

Write-Host ""
Write-Host "Step 6: Running Puppeteer tests..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
node scripts/testing/run-puppeteer-tests.js

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Execution Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Check playwright-report/index.html for Playwright results" -ForegroundColor Yellow
Write-Host "Check test-results/puppeteer-results.json for Puppeteer results" -ForegroundColor Yellow
