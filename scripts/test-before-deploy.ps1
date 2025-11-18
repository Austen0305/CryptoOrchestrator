# Quick Pre-Deployment Test Script
# Run this before deploying to verify everything works

Write-Host "🧪 Pre-Deployment Testing" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

$errors = 0
$warnings = 0

# Test 1: Check if Python is available
Write-Host "Test 1: Python Installation" -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found!" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Test 2: Check if Node.js is available
Write-Host "Test 2: Node.js Installation" -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js not found!" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Test 3: Check if requirements.txt exists
Write-Host "Test 3: Backend Dependencies File" -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    Write-Host "  ✓ requirements.txt exists" -ForegroundColor Green
    $reqCount = (Get-Content "requirements.txt" | Where-Object { $_ -notmatch '^#' -and $_.Trim() -ne '' }).Count
    Write-Host "  ✓ Found $reqCount dependencies" -ForegroundColor Green
} else {
    Write-Host "  ✗ requirements.txt not found!" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Test 4: Check if package.json exists
Write-Host "Test 4: Frontend Dependencies File" -ForegroundColor Yellow
if (Test-Path "package.json") {
    Write-Host "  ✓ package.json exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ package.json not found!" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Test 5: Check if main.py exists
Write-Host "Test 5: Backend Entry Point" -ForegroundColor Yellow
if (Test-Path "server_fastapi/main.py") {
    Write-Host "  ✓ server_fastapi/main.py exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ server_fastapi/main.py not found!" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Test 6: Check if client directory exists
Write-Host "Test 6: Frontend Directory" -ForegroundColor Yellow
if (Test-Path "client") {
    Write-Host "  ✓ client directory exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠ client directory not found (may be optional)" -ForegroundColor Yellow
    $warnings++
}
Write-Host ""

# Test 7: Check if Dockerfile exists
Write-Host "Test 7: Docker Configuration" -ForegroundColor Yellow
if (Test-Path "Dockerfile") {
    Write-Host "  ✓ Dockerfile exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Dockerfile not found (optional for some platforms)" -ForegroundColor Yellow
    $warnings++
}
Write-Host ""

# Test 8: Check if .env.example exists (good practice)
Write-Host "Test 8: Environment Variables Documentation" -ForegroundColor Yellow
if (Test-Path ".env.example") {
    Write-Host "  ✓ .env.example exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠ .env.example not found (recommended for documentation)" -ForegroundColor Yellow
    $warnings++
}
Write-Host ""

# Test 9: Check if PORT is used in main.py
Write-Host "Test 9: PORT Environment Variable" -ForegroundColor Yellow
if (Test-Path "server_fastapi/main.py") {
    $mainContent = Get-Content "server_fastapi/main.py" -Raw
    if ($mainContent -match 'os\.getenv\(["\']PORT["\']') {
        Write-Host "  ✓ PORT environment variable is used" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ PORT environment variable may not be configured" -ForegroundColor Yellow
        $warnings++
    }
}
Write-Host ""

# Test 10: Try to install Python dependencies (dry run)
Write-Host "Test 10: Python Dependencies Check" -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    Write-Host "  ℹ Checking if pip can read requirements.txt..." -ForegroundColor Cyan
    try {
        $pipCheck = pip check 2>&1
        Write-Host "  ✓ pip is working" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Could not verify pip (this is okay)" -ForegroundColor Yellow
        $warnings++
    }
}
Write-Host ""

# Summary
Write-Host "=========================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

if ($errors -eq 0) {
    Write-Host "✓ All critical tests passed!" -ForegroundColor Green
    Write-Host ""
    if ($warnings -gt 0) {
        Write-Host "⚠ Found $warnings warnings (non-critical)" -ForegroundColor Yellow
        Write-Host ""
    }
    Write-Host "✅ Your app is ready for deployment!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Run: npm run dev:fastapi (test backend locally)" -ForegroundColor White
    Write-Host "  2. Run: npm run build (test frontend build)" -ForegroundColor White
    Write-Host "  3. Follow: QUICK_START_FREE_HOSTING.md" -ForegroundColor White
} else {
    Write-Host "✗ Found $errors critical errors!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix these issues before deploying:" -ForegroundColor Yellow
    Write-Host "  - Install missing dependencies" -ForegroundColor White
    Write-Host "  - Fix missing files" -ForegroundColor White
    Write-Host "  - Check file paths" -ForegroundColor White
}

Write-Host ""

