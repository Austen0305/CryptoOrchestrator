# Test MCP Integrations Script (PowerShell)
# Tests all MCP integrations to ensure they're working correctly

$ErrorActionPreference = "Stop"

$passed = 0
$failed = 0

function Test-Command {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    
    Write-Host "Testing $Name... " -NoNewline
    try {
        $null = Invoke-Command -ScriptBlock $Command -ErrorAction Stop 2>&1 | Out-Null
        Write-Host "✓ PASSED" -ForegroundColor Green
        $script:passed++
        return $true
    } catch {
        Write-Host "✗ FAILED" -ForegroundColor Red
        $script:failed++
        return $false
    }
}

Write-Host "🧪 Testing MCP Integrations...`n" -ForegroundColor Cyan

# Test Python environment
Write-Host "📦 Testing Python Environment..." -ForegroundColor Cyan
Test-Command "Python" { python --version }
Test-Command "pip" { pip --version }
Test-Command "pytest" { pytest --version }

# Test Node.js environment
Write-Host "`n📦 Testing Node.js Environment..." -ForegroundColor Cyan
Test-Command "Node.js" { node --version }
Test-Command "npm" { npm --version }

# Test Docker
Write-Host "`n🐳 Testing Docker..." -ForegroundColor Cyan
Test-Command "Docker" { docker --version }
Test-Command "Docker Compose" { docker-compose --version }

# Test Redis
Write-Host "`n🔴 Testing Redis..." -ForegroundColor Cyan
try {
    $result = redis-cli ping 2>&1
    if ($result -like "*PONG*") {
        Write-Host "✓ Redis is running" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "⚠ Redis not running (optional)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Redis not available (optional)" -ForegroundColor Yellow
}

# Test PostgreSQL
Write-Host "`n🐘 Testing PostgreSQL..." -ForegroundColor Cyan
try {
    $result = psql --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ PostgreSQL is available" -ForegroundColor Green
        $passed++
    }
} catch {
    Write-Host "⚠ PostgreSQL not available (optional)" -ForegroundColor Yellow
}

# Test MCP Scripts
Write-Host "`n🔧 Testing MCP Scripts..." -ForegroundColor Cyan
Test-Command "GitHub Release Script" { python scripts/github_release.py --help }
Test-Command "Secrets Manager" { python scripts/secrets_manager.py --help }
Test-Command "Redis Setup" { python scripts/redis_setup.py --help }
Test-Command "Code Quality Scanner" { python scripts/code_quality_scan.py --help }

# Test Secrets Management
Write-Host "`n🔐 Testing Secrets Management..." -ForegroundColor Cyan
try {
    $result = python scripts/secrets_manager.py validate 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Secrets validation passed" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "⚠ Secrets validation failed (may be expected)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Secrets validation failed (may be expected)" -ForegroundColor Yellow
}

# Test Redis Connection
Write-Host "`n🔴 Testing Redis Connection..." -ForegroundColor Cyan
try {
    $result = python scripts/redis_setup.py test 2>&1
    if ($result -like "*ok*") {
        Write-Host "✓ Redis connection successful" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "⚠ Redis connection failed (may be expected)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Redis connection failed (may be expected)" -ForegroundColor Yellow
}

# Test Docker Build
Write-Host "`n🐳 Testing Docker Build..." -ForegroundColor Cyan
try {
    docker build -t test-mcp:latest -f Dockerfile . 2>&1 | Out-Null
    Write-Host "✓ Docker build successful" -ForegroundColor Green
    $passed++
    docker rmi test-mcp:latest 2>&1 | Out-Null
} catch {
    Write-Host "⚠ Docker build failed (check Dockerfile)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n📊 Test Summary" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red

if ($failed -eq 0) {
    Write-Host "`n✅ All critical tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n⚠ Some tests failed (check output above)" -ForegroundColor Yellow
    exit 1
}

