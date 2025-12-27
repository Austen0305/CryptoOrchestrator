# Run Playwright E2E Tests
Write-Host "Running Playwright E2E Tests..." -ForegroundColor Green

# Set environment variables
$env:BASE_URL = "http://localhost:5173"
$env:API_URL = "http://localhost:8000"

# Check if servers are running
Write-Host "Checking if servers are running..." -ForegroundColor Yellow

try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "Backend server is running" -ForegroundColor Green
} catch {
    Write-Host "Backend server is not running. Please start it first with: npm run dev:fastapi" -ForegroundColor Red
    exit 1
}

try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "Frontend server is running" -ForegroundColor Green
} catch {
    Write-Host "Frontend server is not running. Please start it first with: npm run dev" -ForegroundColor Red
    exit 1
}

Write-Host "`nRunning comprehensive UI tests..." -ForegroundColor Cyan
npx playwright test tests/e2e/comprehensive-ui-test.spec.ts --project=chromium --reporter=list --timeout=60000

Write-Host "`nE2E testing complete!" -ForegroundColor Green

