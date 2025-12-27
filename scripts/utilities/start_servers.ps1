# Start Servers Script for Testing
# Starts both backend and frontend servers for E2E testing

Write-Host "Starting CryptoOrchestrator servers for testing..." -ForegroundColor Green

# Set environment variables
$env:DATABASE_URL = "sqlite+aiosqlite:///./test_e2e.db"
$env:TESTING = "true"
$env:PYTHONUNBUFFERED = "1"

# Start backend server
Write-Host "Starting FastAPI backend on http://localhost:8000..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location server_fastapi
    $env:DATABASE_URL = "sqlite+aiosqlite:///../test_e2e.db"
    $env:TESTING = "true"
    $env:PYTHONUNBUFFERED = "1"
    python -m uvicorn main:app --port 8000 --host 127.0.0.1 --reload
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
    Write-Host "Warning: Backend may not be ready yet. Check backend logs." -ForegroundColor Yellow
}

# Start frontend server
Write-Host "Starting Vite frontend on http://localhost:5173..." -ForegroundColor Yellow
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
    Write-Host "Warning: Frontend may not be ready yet. Check frontend logs." -ForegroundColor Yellow
}

Write-Host "`nServers started! Press Ctrl+C to stop." -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
        # Check if jobs are still running
        if ($backendJob.State -eq "Failed" -or $frontendJob.State -eq "Failed") {
            Write-Host "One or more servers have failed. Check job output:" -ForegroundColor Red
            Receive-Job $backendJob
            Receive-Job $frontendJob
            break
        }
    }
}
finally {
    Write-Host "`nStopping servers..." -ForegroundColor Yellow
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
}
