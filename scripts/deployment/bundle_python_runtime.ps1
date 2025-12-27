# Bundle Python Runtime for Electron Desktop App
# Creates a portable Python runtime that can be bundled with the Electron app

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "=== Python Runtime Bundling Script ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$PythonVersion = "3.12"  # Use Python 3.12 for compatibility
$RuntimeDir = "python-runtime"
$VenvDir = Join-Path $RuntimeDir "venv"

# Check if runtime already exists
if (Test-Path $RuntimeDir -ErrorAction SilentlyContinue) {
    if (-not $Force) {
        Write-Host "Python runtime directory already exists: $RuntimeDir" -ForegroundColor Yellow
        Write-Host "Use -Force to overwrite" -ForegroundColor Yellow
        exit 0
    }
    else {
        Write-Host "Removing existing runtime directory..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $RuntimeDir
    }
}

# Check for Python installation
Write-Host "Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "Python not found. Please install Python $PythonVersion or later." -ForegroundColor Red
    exit 1
}

# Create runtime directory
Write-Host "Creating runtime directory: $RuntimeDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Cyan
python -m venv $VenvDir

if (-not (Test-Path $VenvDir)) {
    Write-Host "Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
$activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Host "Virtual environment activation script not found" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
$pipPath = Join-Path $VenvDir "Scripts\pip.exe"
& $pipPath install --upgrade pip setuptools wheel
& $pipPath install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Copy server_fastapi directory
Write-Host "Copying server_fastapi directory..." -ForegroundColor Cyan
if (Test-Path "server_fastapi") {
    Copy-Item -Recurse -Force "server_fastapi" (Join-Path $RuntimeDir "server_fastapi")
}
else {
    Write-Host "Warning: server_fastapi directory not found" -ForegroundColor Yellow
}

# Copy shared directory
Write-Host "Copying shared directory..." -ForegroundColor Cyan
if (Test-Path "shared") {
    Copy-Item -Recurse -Force "shared" (Join-Path $RuntimeDir "shared")
}
else {
    Write-Host "Warning: shared directory not found" -ForegroundColor Yellow
}

# Copy requirements.txt
Write-Host "Copying requirements.txt..." -ForegroundColor Cyan
if (Test-Path "requirements.txt") {
    Copy-Item -Force "requirements.txt" (Join-Path $RuntimeDir "requirements.txt")
}

# Create startup script
Write-Host "Creating startup scripts..." -ForegroundColor Cyan

# Windows startup script
$startScript = @"
@echo off
setlocal

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%venv
set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe

REM Check if Python executable exists
if not exist "%PYTHON_EXE%" (
    echo Python runtime not found in %VENV_DIR%
    exit /b 1
)

REM Set Python path
set PYTHONPATH=%SCRIPT_DIR%

REM Run FastAPI server
"%PYTHON_EXE%" -m uvicorn server_fastapi.main:app --host 127.0.0.1 --port 8000

endlocal
"@

$startScriptPath = Join-Path $RuntimeDir "start_server.bat"
$startScript | Out-File -FilePath $startScriptPath -Encoding ASCII

# Create Python version info file
$versionInfo = @{
    python_version = $pythonVersion
    bundled_date   = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    platform       = "windows"
}

$versionInfo | ConvertTo-Json | Out-File -FilePath (Join-Path $RuntimeDir "version.json") -Encoding UTF8

Write-Host ""
Write-Host "=== Python Runtime Bundling Complete ===" -ForegroundColor Green
Write-Host "Runtime directory: $RuntimeDir" -ForegroundColor Green
Write-Host "Virtual environment: $VenvDir" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Build Electron app: npm run build:electron" -ForegroundColor White
Write-Host "2. The Python runtime will be bundled automatically" -ForegroundColor White
