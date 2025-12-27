# Setup Testing Dependencies (PowerShell)
# Installs all dependencies needed for testing scripts

Write-Host "🔧 Setting up testing dependencies..." -ForegroundColor Cyan

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
  Write-Host "⚠️  Warning: Virtual environment not detected." -ForegroundColor Yellow
  Write-Host "   Activate your virtual environment first:" -ForegroundColor Yellow
  Write-Host "   .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
  Write-Host ""
  $response = Read-Host "Continue anyway? (y/n)"
  if ($response -ne "y" -and $response -ne "Y") {
    exit 1
  }
}

# Install requirements
Write-Host "📦 Installing requirements..." -ForegroundColor Cyan
pip install -r requirements.txt

# Install dev requirements (includes testing tools)
Write-Host "📦 Installing dev requirements..." -ForegroundColor Cyan
pip install -r requirements-dev.txt

# Verify critical packages
Write-Host "✅ Verifying critical packages..." -ForegroundColor Green
try {
  $web3Version = python -c "import web3; print(web3.__version__)" 2>&1
  Write-Host "  ✅ web3 $web3Version" -ForegroundColor Green
}
catch {
  Write-Host "  ❌ web3 not installed" -ForegroundColor Red
}

try {
  $httpxVersion = python -c "import httpx; print(httpx.__version__)" 2>&1
  Write-Host "  ✅ httpx $httpxVersion" -ForegroundColor Green
}
catch {
  Write-Host "  ❌ httpx not installed" -ForegroundColor Red
}

try {
  $pytestVersion = python -c "import pytest; print(pytest.__version__)" 2>&1
  Write-Host "  ✅ pytest $pytestVersion" -ForegroundColor Green
}
catch {
  Write-Host "  ❌ pytest not installed" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run:" -ForegroundColor Cyan
Write-Host "  python scripts/testing/testnet_verification.py --network sepolia"
Write-Host "  python scripts/monitoring/set_performance_baseline.py"
Write-Host "  python scripts/security/security_audit.py"
Write-Host "  python scripts/testing/load_test.py"
