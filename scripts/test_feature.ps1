# Feature Testing Script (PowerShell)
# Helps test features systematically

param(
    [Parameter(Mandatory=$true)]
    [string]$FeatureName,
    
    [Parameter(Mandatory=$false)]
    [int]$Phase = 0
)

Write-Host "🧪 Testing Feature: $FeatureName" -ForegroundColor Cyan
Write-Host "📋 Phase: $Phase" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "✅ Backend is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend not running. Starting backend..." -ForegroundColor Yellow
    Start-Process -NoNewWindow npm -ArgumentList "run", "dev:fastapi"
    Start-Sleep -Seconds 5
    Write-Host "✅ Backend started" -ForegroundColor Green
}

# Check if frontend is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "✅ Frontend is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Frontend not running. Starting frontend..." -ForegroundColor Yellow
    Start-Process -NoNewWindow npm -ArgumentList "run", "dev"
    Start-Sleep -Seconds 3
    Write-Host "✅ Frontend started" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Environment ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Testing Checklist:" -ForegroundColor Cyan
Write-Host "  [ ] Feature loads correctly"
Write-Host "  [ ] All interactions work"
Write-Host "  [ ] Error handling works"
Write-Host "  [ ] Loading states work"
Write-Host "  [ ] Responsive design works"
Write-Host "  [ ] Accessibility works"
Write-Host ""
Write-Host "🌐 Open http://localhost:5173 to test" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key when done testing..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

