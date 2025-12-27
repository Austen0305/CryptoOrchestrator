# CryptoOrchestrator - Start All Services Script
# This script starts all services in separate PowerShell windows

Write-Host "🚀 Starting CryptoOrchestrator Services..." -ForegroundColor Green
Write-Host ""

# Get the project root directory
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# 1. Start Backend (FastAPI)
Write-Host "Starting Backend API Server..." -ForegroundColor Cyan
# Configure a sensible request timeout for local/dev runs
$backendCmd = "cd '$projectRoot\server_fastapi'; $env:REQUEST_TIMEOUT='30'; Write-Host 'Backend API Server (Port 8000) (REQUEST_TIMEOUT=30)' -ForegroundColor Green; uvicorn main:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 2

# 2. Start Frontend (React/Vite)
Write-Host "Starting Frontend Development Server..." -ForegroundColor Cyan
$frontendCmd = "cd '$projectRoot'; Write-Host 'Frontend Server (Port 5173)' -ForegroundColor Green; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Start-Sleep -Seconds 2

# 3. Start Celery Worker
Write-Host "Starting Celery Worker..." -ForegroundColor Cyan
$workerCmd = "cd '$projectRoot\server_fastapi'; Write-Host 'Celery Worker' -ForegroundColor Green; python -m celery -A celery_app worker --loglevel=info"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $workerCmd

Start-Sleep -Seconds 2

# 4. Start Celery Beat (Scheduler)
Write-Host "Starting Celery Beat Scheduler..." -ForegroundColor Cyan
$beatCmd = "cd '$projectRoot\server_fastapi'; Write-Host 'Celery Beat Scheduler' -ForegroundColor Green; python -m celery -A celery_app beat --loglevel=info"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $beatCmd

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Service Status:" -ForegroundColor Yellow
Write-Host "  • Backend API:     http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs:        http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Frontend:        http://localhost:5173" -ForegroundColor White
Write-Host "  • Celery Worker:   Running (background)" -ForegroundColor White
Write-Host "  • Celery Beat:     Running (background)" -ForegroundColor White
Write-Host ""
Write-Host "💡 Each service runs in its own PowerShell window." -ForegroundColor Cyan
Write-Host "💡 Close the windows or press Ctrl+C to stop services." -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 Ready to trade! Open http://localhost:5173 in your browser." -ForegroundColor Green

