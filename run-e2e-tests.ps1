# PowerShell script to start servers and run E2E tests
Write-Host "Starting CryptoOrchestrator E2E Testing..." -ForegroundColor Green

# Check if ports are available
$port5173 = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($port5173) {
    Write-Host "Port 5173 is already in use - will use existing server" -ForegroundColor Yellow
} else {
    Write-Host "Port 5173 is available" -ForegroundColor Green
}

if ($port8000) {
    Write-Host "Port 8000 is already in use - will use existing server" -ForegroundColor Yellow
} else {
    Write-Host "Port 8000 is available" -ForegroundColor Green
}

# Set environment variables
$env:TESTING = "true"
$env:DATABASE_URL = "sqlite+aiosqlite:///./test_e2e.db"
$env:PYTHONUNBUFFERED = "1"
$env:NODE_ENV = "test"

Write-Host "`nStarting FastAPI backend..." -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    $env:TESTING = "true"
    $env:DATABASE_URL = "sqlite+aiosqlite:///./test_e2e.db"
    $env:PYTHONUNBUFFERED = "1"
    python -m uvicorn server_fastapi.main:app --port 8000 --host 127.0.0.1
}

# Wait for backend to be ready
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "Backend is ready!" -ForegroundColor Green
            break
        }
    }
    catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $backendReady) {
    Write-Host "Warning: Backend may not be ready yet. Continuing anyway..." -ForegroundColor Yellow
}

# Start frontend server
Write-Host "Starting Vite frontend..." -ForegroundColor Cyan
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    npm run dev
}

# Wait for frontend to be ready
Write-Host "Waiting for frontend to start..." -ForegroundColor Yellow
$frontendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $frontendReady = $true
            Write-Host "Frontend is ready!" -ForegroundColor Green
            break
        }
    }
    catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $frontendReady) {
    Write-Host "Warning: Frontend may not be ready yet. Continuing anyway..." -ForegroundColor Yellow
}

Start-Sleep -Seconds 3

Write-Host "`nRunning Playwright E2E tests..." -ForegroundColor Cyan
Write-Host "This will test the application by clicking through the UI" -ForegroundColor Yellow

# Run Playwright tests
$env:BASE_URL = "http://localhost:5173"
$env:API_URL = "http://localhost:8000"
npx playwright test --headed

# Cleanup
Write-Host "`nStopping servers..." -ForegroundColor Yellow
Stop-Job $backendJob -ErrorAction SilentlyContinue
Stop-Job $frontendJob -ErrorAction SilentlyContinue
Remove-Job $backendJob -ErrorAction SilentlyContinue
Remove-Job $frontendJob -ErrorAction SilentlyContinue

Write-Host "E2E testing complete!" -ForegroundColor Green

