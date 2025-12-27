# CryptoOrchestrator Cleanup Script
# Removes build artifacts and temporary files

Write-Host "🧹 Cleaning up CryptoOrchestrator..." -ForegroundColor Cyan
Write-Host ""

$removed = 0
$errors = 0

# Function to safely remove items
function Remove-SafeItem {
    param(
        [string]$Path,
        [string]$Description
    )
    
    if (Test-Path $Path) {
        try {
            Remove-Item $Path -Force -Recurse -ErrorAction Stop
            Write-Host "✓ Removed $Description" -ForegroundColor Green
            return 1
        }
        catch {
            Write-Host "✗ Failed to remove $Description : $_" -ForegroundColor Red
            $script:errors++
            return 0
        }
    }
    else {
        Write-Host "  Skipped $Description (not found)" -ForegroundColor Gray
        return 0
    }
}

Write-Host "Removing build artifacts..." -ForegroundColor Yellow
$removed += Remove-SafeItem "dist" "Frontend build (dist/)"
$removed += Remove-SafeItem "dist-electron" "Electron build (dist-electron/)"
$removed += Remove-SafeItem ".vite" "Vite cache (.vite/)"

Write-Host ""
Write-Host "Removing Python artifacts..." -ForegroundColor Yellow
$removed += Remove-SafeItem "htmlcov" "Coverage reports (htmlcov/)"
$removed += Remove-SafeItem ".coverage" "Coverage data (.coverage)"
$removed += Remove-SafeItem ".pytest_cache" "Pytest cache (.pytest_cache/)"

# Remove all __pycache__ directories
Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object {
    $removed += Remove-SafeItem $_.FullName "Python cache ($($_.FullName))"
}

# Remove .pyc files
Get-ChildItem -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object {
    $removed += Remove-SafeItem $_.FullName "Compiled Python ($($_.Name))"
}

Write-Host ""
Write-Host "Removing log files..." -ForegroundColor Yellow
if (Test-Path "logs") {
    Get-ChildItem "logs" -Filter "*.log" -ErrorAction SilentlyContinue | ForEach-Object {
        $removed += Remove-SafeItem $_.FullName "Log file ($($_.Name))"
    }
}

Write-Host ""
Write-Host "Removing temporary files..." -ForegroundColor Yellow
$removed += Remove-SafeItem ".DS_Store" "macOS metadata (.DS_Store)"
$removed += Remove-SafeItem "Thumbs.db" "Windows metadata (Thumbs.db)"

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
if ($errors -eq 0) {
    Write-Host "✨ Cleanup complete! Removed $removed items." -ForegroundColor Green
}
else {
    Write-Host "⚠️  Cleanup finished with $errors errors. Removed $removed items." -ForegroundColor Yellow
}
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tip: Run 'npm run dev' to rebuild the application" -ForegroundColor Gray
