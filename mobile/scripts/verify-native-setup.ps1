# Verify Native Project Setup Script
# Checks if iOS and Android native projects are properly initialized

Write-Host "🔍 Verifying Native Project Setup..." -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check Android
Write-Host "🤖 Checking Android project..." -ForegroundColor Yellow
if (Test-Path "android") {
    Write-Host "   ✅ android/ directory exists" -ForegroundColor Green
    
    if (Test-Path "android/app") {
        Write-Host "   ✅ android/app/ directory exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ android/app/ directory missing" -ForegroundColor Red
        $allGood = $false
    }
    
    if (Test-Path "android/build.gradle") {
        Write-Host "   ✅ android/build.gradle exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ android/build.gradle missing" -ForegroundColor Red
        $allGood = $false
    }
    
    if (Test-Path "android/local.properties") {
        Write-Host "   ✅ android/local.properties exists" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  android/local.properties missing (create manually or run init script)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ android/ directory not found" -ForegroundColor Red
    Write-Host "      Run: npm run init:native:android" -ForegroundColor Gray
    $allGood = $false
}

Write-Host ""

# Check iOS (macOS only)
if ($IsMacOS -or (Get-Command uname -ErrorAction SilentlyContinue)) {
    Write-Host "🍎 Checking iOS project..." -ForegroundColor Yellow
    if (Test-Path "ios") {
        Write-Host "   ✅ ios/ directory exists" -ForegroundColor Green
        
        if (Test-Path "ios/CryptoOrchestrator.xcworkspace") {
            Write-Host "   ✅ iOS workspace exists" -ForegroundColor Green
        } else {
            Write-Host "   ❌ iOS workspace missing" -ForegroundColor Red
            $allGood = $false
        }
        
        if (Test-Path "ios/Podfile") {
            Write-Host "   ✅ Podfile exists" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Podfile missing" -ForegroundColor Red
            $allGood = $false
        }
        
        if (Test-Path "ios/Pods") {
            Write-Host "   ✅ CocoaPods dependencies installed" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  CocoaPods dependencies not installed" -ForegroundColor Yellow
            Write-Host "      Run: cd ios && pod install" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ❌ ios/ directory not found" -ForegroundColor Red
        Write-Host "      Run: npm run init:native:ios" -ForegroundColor Gray
        $allGood = $false
    }
} else {
    Write-Host "🍎 iOS check skipped (requires macOS)" -ForegroundColor Gray
}

Write-Host ""

# Check configuration files
Write-Host "📝 Checking configuration files..." -ForegroundColor Yellow
if (Test-Path "app.json") {
    Write-Host "   ✅ app.json exists" -ForegroundColor Green
} else {
    Write-Host "   ❌ app.json missing" -ForegroundColor Red
    $allGood = $false
}

if (Test-Path ".env") {
    Write-Host "   ✅ .env exists" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  .env missing (copy from .env.example)" -ForegroundColor Yellow
}

if (Test-Path "eas.json") {
    Write-Host "   ✅ eas.json exists" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  eas.json missing (optional, for EAS builds)" -ForegroundColor Yellow
}

Write-Host ""

# Summary
if ($allGood) {
    Write-Host "✅ All native projects are properly initialized!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Start Metro: npm start" -ForegroundColor Gray
    Write-Host "  2. Run on device: npm run ios (or npm run android)" -ForegroundColor Gray
} else {
    Write-Host "❌ Some native projects are missing or incomplete" -ForegroundColor Red
    Write-Host ""
    Write-Host "To fix:" -ForegroundColor Cyan
    Write-Host "  Run: npm run init:native" -ForegroundColor Gray
    Write-Host "  Or: npm run init:native:force (to overwrite existing)" -ForegroundColor Gray
}

Write-Host ""
