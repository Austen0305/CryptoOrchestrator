# PowerShell script to prepare mobile app for App Store/Play Store submission
# This script helps verify all requirements are met before submission

$ErrorActionPreference = "Stop"

Write-Host "🚀 CryptoOrchestrator App Store Submission Preparation"
Write-Host "=" * 60
Write-Host ""

# Check if in mobile directory
if (-not (Test-Path "app.json")) {
    Write-Host "❌ Error: Must run from mobile/ directory" -ForegroundColor Red
    Write-Host "   Please run: cd mobile && .\scripts\prepare-submission.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "📋 Checking Prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check Node.js
Write-Host "Checking Node.js..." -NoNewline
try {
    $nodeVersion = node --version
    Write-Host " ✅ $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host " ❌ Not installed" -ForegroundColor Red
    exit 1
}

# Check npm
Write-Host "Checking npm..." -NoNewline
try {
    $npmVersion = npm --version
    Write-Host " ✅ $npmVersion" -ForegroundColor Green
} catch {
    Write-Host " ❌ Not installed" -ForegroundColor Red
    exit 1
}

# Check EAS CLI
Write-Host "Checking EAS CLI..." -NoNewline
try {
    $easVersion = eas --version 2>$null
    if ($easVersion) {
        Write-Host " ✅ $easVersion" -ForegroundColor Green
    } else {
        Write-Host " ⚠️  Not installed" -ForegroundColor Yellow
        Write-Host "   Install with: npm install -g eas-cli" -ForegroundColor Yellow
    }
} catch {
    Write-Host " ⚠️  Not installed" -ForegroundColor Yellow
    Write-Host "   Install with: npm install -g eas-cli" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 Checking Configuration Files..." -ForegroundColor Yellow
Write-Host ""

# Check app.json
Write-Host "Checking app.json..." -NoNewline
if (Test-Path "app.json") {
    $appJson = Get-Content "app.json" | ConvertFrom-Json
    if ($appJson.expo.extra.eas.projectId -eq "your-project-id-here") {
        Write-Host " ⚠️  Project ID not set" -ForegroundColor Yellow
        Write-Host "   Run: eas init" -ForegroundColor Yellow
    } else {
        Write-Host " ✅ Configured" -ForegroundColor Green
    }
} else {
    Write-Host " ❌ Not found" -ForegroundColor Red
    exit 1
}

# Check eas.json
Write-Host "Checking eas.json..." -NoNewline
if (Test-Path "eas.json") {
    Write-Host " ✅ Found" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Not found" -ForegroundColor Yellow
    Write-Host "   Create with: eas build:configure" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🖼️  Checking Assets..." -ForegroundColor Yellow
Write-Host ""

# Check app icon
Write-Host "Checking app icon..." -NoNewline
if (Test-Path "assets/icon.png") {
    Write-Host " ✅ Found" -ForegroundColor Green
} else {
    Write-Host " ❌ Missing" -ForegroundColor Red
    Write-Host "   Required: assets/icon.png (1024x1024 PNG)" -ForegroundColor Yellow
}

# Check adaptive icon
Write-Host "Checking Android adaptive icon..." -NoNewline
if (Test-Path "assets/adaptive-icon.png") {
    Write-Host " ✅ Found" -ForegroundColor Green
} else {
    Write-Host " ❌ Missing" -ForegroundColor Red
    Write-Host "   Required: assets/adaptive-icon.png (1024x1024 PNG)" -ForegroundColor Yellow
}

# Check splash screen
Write-Host "Checking splash screen..." -NoNewline
if (Test-Path "assets/splash.png") {
    Write-Host " ✅ Found" -ForegroundColor Green
} else {
    Write-Host " ❌ Missing" -ForegroundColor Red
    Write-Host "   Required: assets/splash.png (2048x2048 PNG)" -ForegroundColor Yellow
}

# Check feature graphic
Write-Host "Checking Android feature graphic..." -NoNewline
if (Test-Path "assets/feature-graphic.png") {
    Write-Host " ✅ Found" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Missing (recommended)" -ForegroundColor Yellow
    Write-Host "   Recommended: assets/feature-graphic.png (1024x500 PNG)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📸 Checking Screenshots..." -ForegroundColor Yellow
Write-Host ""

# Check iOS screenshots
$iosScreenshots = 0
if (Test-Path "assets/screenshots/ios") {
    $iosScreenshots = (Get-ChildItem "assets/screenshots/ios" -Recurse -Filter "*.png" -ErrorAction SilentlyContinue).Count
}
Write-Host "iOS screenshots: $iosScreenshots found"
if ($iosScreenshots -eq 0) {
    Write-Host "   ⚠️  No screenshots found" -ForegroundColor Yellow
    Write-Host "   Required: At least 1 screenshot per device size" -ForegroundColor Yellow
}

# Check Android screenshots
$androidScreenshots = 0
if (Test-Path "assets/screenshots/android") {
    $androidScreenshots = (Get-ChildItem "assets/screenshots/android" -Recurse -Filter "*.png" -ErrorAction SilentlyContinue).Count
}
Write-Host "Android screenshots: $androidScreenshots found"
if ($androidScreenshots -lt 2) {
    Write-Host "   ⚠️  Less than 2 screenshots found" -ForegroundColor Yellow
    Write-Host "   Required: Minimum 2 screenshots" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔐 Checking Credentials..." -ForegroundColor Yellow
Write-Host ""

# Check Google service account
Write-Host "Checking Google service account..." -NoNewline
if (Test-Path "google-service-account.json") {
    Write-Host " ✅ Found" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Not found" -ForegroundColor Yellow
    Write-Host "   Required for automated Android submission" -ForegroundColor Yellow
    Write-Host "   See: docs/MOBILE_APP_STORE_SUBMISSION.md" -ForegroundColor Yellow
}

# Check environment variables
Write-Host "Checking iOS submission credentials..." -NoNewline
if ($env:APPLE_ID -and $env:ASC_APP_ID -and $env:APPLE_TEAM_ID) {
    Write-Host " ✅ Environment variables set" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Environment variables not set" -ForegroundColor Yellow
    Write-Host "   Set: APPLE_ID, ASC_APP_ID, APPLE_TEAM_ID" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📚 Checking Documentation..." -ForegroundColor Yellow
Write-Host ""

# Check privacy policy
Write-Host "Checking privacy policy..." -NoNewline
if (Test-Path "../docs/PRIVACY_POLICY.md") {
    Write-Host " ✅ Found" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Not found" -ForegroundColor Yellow
    Write-Host "   Required: Privacy policy URL for stores" -ForegroundColor Yellow
}

# Check terms of service
Write-Host "Checking terms of service..." -NoNewline
if (Test-Path "../docs/TERMS_OF_SERVICE.md") {
    Write-Host " ✅ Found" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Not found (optional)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 60
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create missing assets (icons, screenshots)"
Write-Host "2. Set up Apple Developer and Google Play accounts"
Write-Host "3. Initialize EAS project: eas init"
Write-Host "4. Configure eas.json with your credentials"
Write-Host "5. Create production builds: eas build --platform all --profile production"
Write-Host "6. Test builds on physical devices"
Write-Host "7. Submit to stores: eas submit --platform all --profile production"
Write-Host ""
Write-Host "📖 See docs/MOBILE_APP_STORE_SUBMISSION.md for complete guide"
Write-Host ""

