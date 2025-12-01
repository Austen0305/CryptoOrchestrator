# Initialize native iOS and Android projects for CryptoOrchestrator mobile app (Windows)

Write-Host "🚀 Initializing native mobile projects..." -ForegroundColor Cyan

# Check if we're in the mobile directory
if (-not (Test-Path "package.json")) {
    Write-Host "❌ Error: Please run this script from the mobile directory" -ForegroundColor Red
    exit 1
}

# Check for Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js is required but not installed. Aborting." -ForegroundColor Red
    exit 1
}

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Initialize Android project (Windows can only do Android)
Write-Host "🤖 Initializing Android project..." -ForegroundColor Cyan
if (-not (Test-Path "android")) {
    npx expo prebuild --platform android
    Write-Host "✅ Android project initialized" -ForegroundColor Green
} else {
    Write-Host "⚠️  Android directory already exists, skipping..." -ForegroundColor Yellow
}

Write-Host "⚠️  iOS initialization requires macOS. Skipping..." -ForegroundColor Yellow

Write-Host "✅ Native projects initialized successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  - Android: Open android/ in Android Studio"
Write-Host "  - Run: npm run android"

