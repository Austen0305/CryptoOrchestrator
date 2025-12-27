# Run All Playwright E2E Tests
Write-Host "Running All Playwright E2E Tests..." -ForegroundColor Green

# Set environment variables
$env:BASE_URL = "http://localhost:5173"
$env:API_URL = "http://localhost:8000"

# Check if servers are running
Write-Host "`nChecking servers..." -ForegroundColor Yellow

try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Backend server is running" -ForegroundColor Green
}
catch {
    Write-Host "✗ Backend server is not running" -ForegroundColor Red
    Write-Host "Please start it with: npm run dev:fastapi" -ForegroundColor Yellow
    exit 1
}

try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Frontend server is running" -ForegroundColor Green
}
catch {
    Write-Host "✗ Frontend server is not running" -ForegroundColor Red
    Write-Host "Please start it with: npm run dev" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nRunning all Playwright tests..." -ForegroundColor Cyan
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

# Run all tests
npx playwright test --reporter=list --timeout=60000

Write-Host "`nTests complete!" -ForegroundColor Green
Write-Host "Check playwright-report/ for detailed results" -ForegroundColor Cyan

