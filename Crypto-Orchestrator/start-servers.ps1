# PowerShell script to start both servers
Write-Host "Starting CryptoOrchestrator servers..." -ForegroundColor Green

# Check if ports are available
$port5173 = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($port5173) {
    Write-Host "Port 5173 is already in use!" -ForegroundColor Red
    Write-Host "Please close the process using port 5173" -ForegroundColor Yellow
} else {
    Write-Host "Port 5173 is available" -ForegroundColor Green
}

if ($port8000) {
    Write-Host "Port 8000 is already in use!" -ForegroundColor Red
    Write-Host "Please close the process using port 8000" -ForegroundColor Yellow
} else {
    Write-Host "Port 8000 is available" -ForegroundColor Green
}

Write-Host "`nStarting FastAPI backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev:fastapi" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host "Starting Vite frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev" -WindowStyle Normal

Write-Host "`nServers are starting in separate windows." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "Backend: http://localhost:8000" -ForegroundColor Yellow
Write-Host "`nCheck the PowerShell windows for any errors." -ForegroundColor Cyan

