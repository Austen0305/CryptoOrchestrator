# Install and Run All E2E Tests (Playwright + Puppeteer)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing and Running All E2E Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install Puppeteer
Write-Host "Step 1: Installing Puppeteer..." -ForegroundColor Yellow
npm install puppeteer --save-dev --legacy-peer-deps --ignore-scripts 2>&1 | Out-Null
if (Test-Path "node_modules/puppeteer") {
    Write-Host "✓ Puppeteer installed" -ForegroundColor Green
} else {
    Write-Host "✗ Puppeteer installation failed" -ForegroundColor Red
}

# Step 2: Install Playwright
Write-Host "`nStep 2: Installing Playwright..." -ForegroundColor Yellow
npm install @playwright/test@1.57.0 playwright@1.57.0 --save-dev --legacy-peer-deps --ignore-scripts --force 2>&1 | Out-Null
if (Test-Path "node_modules/@playwright/test") {
    Write-Host "✓ Playwright installed" -ForegroundColor Green
    Write-Host "Installing Chromium browser..." -ForegroundColor Yellow
    npx playwright install chromium 2>&1 | Out-Null
    Write-Host "✓ Chromium installed" -ForegroundColor Green
} else {
    Write-Host "✗ Playwright installation failed" -ForegroundColor Red
}

# Step 3: Check servers
Write-Host "`nStep 3: Checking servers..." -ForegroundColor Yellow
$backendRunning = $false
$frontendRunning = $false

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    $backendRunning = $true
    Write-Host "✓ Backend server is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Backend server is not running" -ForegroundColor Red
    Write-Host "  Starting backend server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; `$env:TESTING='true'; python -m uvicorn server_fastapi.main:app --port 8000 --host 127.0.0.1" -WindowStyle Minimized
    Start-Sleep -Seconds 8
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        $backendRunning = $true
        Write-Host "✓ Backend server started" -ForegroundColor Green
    } catch {
        Write-Host "✗ Backend server failed to start" -ForegroundColor Red
    }
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction Stop
    $frontendRunning = $true
    Write-Host "✓ Frontend server is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Frontend server is not running" -ForegroundColor Red
    Write-Host "  Starting frontend server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev" -WindowStyle Minimized
    Start-Sleep -Seconds 10
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction Stop
        $frontendRunning = $true
        Write-Host "✓ Frontend server started" -ForegroundColor Green
    } catch {
        Write-Host "✗ Frontend server failed to start" -ForegroundColor Red
    }
}

if (-not $backendRunning -or -not $frontendRunning) {
    Write-Host "`n⚠️  Servers not ready. Please start them manually:" -ForegroundColor Yellow
    Write-Host "  Backend: npm run dev:fastapi" -ForegroundColor Yellow
    Write-Host "  Frontend: npm run dev" -ForegroundColor Yellow
    exit 1
}

# Step 4: Run Puppeteer tests
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Running Puppeteer Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$env:BASE_URL = "http://localhost:5173"
$env:API_URL = "http://localhost:8000"

if (Test-Path "node_modules/puppeteer") {
    node scripts/testing/run-puppeteer-tests.js
} else {
    Write-Host "⚠️  Puppeteer not installed, skipping Puppeteer tests" -ForegroundColor Yellow
}

# Step 5: Run Playwright tests
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Running Playwright Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "node_modules/@playwright/test") {
    npx playwright test --reporter=list --timeout=60000 --max-failures=20
} else {
    Write-Host "⚠️  Playwright not installed, skipping Playwright tests" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "All Tests Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nCheck test results:" -ForegroundColor Yellow
Write-Host "  - Playwright HTML Report: playwright-report/index.html" -ForegroundColor Yellow
Write-Host "  - Screenshots: test-results/" -ForegroundColor Yellow
Write-Host "  - Puppeteer Screenshots: tests/puppeteer/screenshots/" -ForegroundColor Yellow
Write-Host ""

