# Setup Modern Stack (uv, ruff, scalar)
# Run this script to modernize the developer experience

Write-Host "Starting Modern Stack Setup..." -ForegroundColor Green

# 1. Install uv (if not present)
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv (Fast Python Package Manager)..." -ForegroundColor Yellow
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path += ";$env:USERPROFILE\.cargo\bin"
}
else {
    Write-Host "uv is already installed" -ForegroundColor Green
}

# 2. Add Scalar & Ruff dependencies
Write-Host "Adding dependencies..." -ForegroundColor Yellow
# Try to install via pip
pip install scalar-fastapi ruff

# 3. Create ruff.toml
Write-Host "Configuring Ruff..." -ForegroundColor Yellow
$configLines = @(
    'target-version = "py312"',
    'line-length = 88',
    '',
    '[lint]',
    'select = ["E", "F", "I", "UP", "B", "SIM"]',
    'ignore = []',
    '',
    '[format]',
    'quote-style = "double"'
)
Set-Content -Path "ruff.toml" -Value $configLines

Write-Host "Setup Complete! Restart your terminal to use 'uv'." -ForegroundColor Green
