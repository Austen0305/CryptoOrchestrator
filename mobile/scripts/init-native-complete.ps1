# Complete Native Project Initialization Script for CryptoOrchestrator Mobile
# This script initializes both iOS and Android native projects using Expo

param(
    [switch]$Force = $false,
    [switch]$AndroidOnly = $false,
    [switch]$IOSOnly = $false
)

Write-Host "🚀 CryptoOrchestrator Mobile - Native Project Initialization" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the mobile directory
if (-not (Test-Path "package.json")) {
    Write-Host "❌ Error: Please run this script from the mobile directory" -ForegroundColor Red
    Write-Host "   cd mobile" -ForegroundColor Yellow
    exit 1
}

# Check for Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js is required but not installed." -ForegroundColor Red
    Write-Host "   Install from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

$nodeVersion = node --version
Write-Host "✅ Node.js version: $nodeVersion" -ForegroundColor Green

# Check for npm
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "❌ npm is required but not installed." -ForegroundColor Red
    exit 1
}

# Install dependencies if needed
if (-not (Test-Path "node_modules") -or $Force) {
    Write-Host ""
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

# Check for Expo
Write-Host ""
Write-Host "🔍 Checking Expo installation..." -ForegroundColor Yellow

# Check if expo is in package.json dependencies
$packageJson = Get-Content "package.json" | ConvertFrom-Json
$expoInDeps = $packageJson.dependencies.PSObject.Properties.Name -contains "expo"

if (-not $expoInDeps) {
    Write-Host "⚠️  Expo not found in dependencies. Installing..." -ForegroundColor Yellow
    npm install expo
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install Expo" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Expo installed" -ForegroundColor Green
} else {
    Write-Host "✅ Expo found in dependencies" -ForegroundColor Green
}

# Check if npx is available
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Write-Host "❌ npx is required but not installed." -ForegroundColor Red
    exit 1
}
Write-Host "✅ npx available" -ForegroundColor Green

# Initialize Android project
if (-not $IOSOnly) {
    Write-Host ""
    Write-Host "🤖 Initializing Android project..." -ForegroundColor Cyan
    
    if (Test-Path "android") {
        if ($Force) {
            Write-Host "⚠️  Android directory exists. Removing..." -ForegroundColor Yellow
            Remove-Item -Recurse -Force android
        }
        else {
            Write-Host "⚠️  Android directory already exists. Use -Force to overwrite." -ForegroundColor Yellow
            $skipAndroid = $true
        }
    }
    
    if (-not $skipAndroid) {
        Write-Host "   Running: npx expo prebuild --platform android" -ForegroundColor Gray
        npx expo prebuild --platform android --clean
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Android project initialized successfully" -ForegroundColor Green
            
            # Create local.properties if it doesn't exist
            $localPropsPath = "android\local.properties"
            if (-not (Test-Path $localPropsPath)) {
                Write-Host "   Creating android/local.properties..." -ForegroundColor Gray
                $androidSdkPath = $env:ANDROID_HOME
                if (-not $androidSdkPath) {
                    $androidSdkPath = "$env:LOCALAPPDATA\Android\Sdk"
                }
                
                if (Test-Path $androidSdkPath) {
                    "sdk.dir=$androidSdkPath" | Out-File -FilePath $localPropsPath -Encoding ASCII
                    Write-Host "✅ Created local.properties with SDK path: $androidSdkPath" -ForegroundColor Green
                }
                else {
                    Write-Host "⚠️  Android SDK not found. Please set ANDROID_HOME or create android/local.properties manually." -ForegroundColor Yellow
                }
            }
        }
        else {
            Write-Host "❌ Failed to initialize Android project" -ForegroundColor Red
            Write-Host "   Make sure Expo is properly installed: npm install -g expo-cli" -ForegroundColor Yellow
        }
    }
}

# Initialize iOS project (macOS only)
if (-not $AndroidOnly) {
    Write-Host ""
    if ($IsMacOS -or (Get-Command uname -ErrorAction SilentlyContinue)) {
        Write-Host "🍎 Initializing iOS project..." -ForegroundColor Cyan
        
        if (Test-Path "ios") {
            if ($Force) {
                Write-Host "⚠️  iOS directory exists. Removing..." -ForegroundColor Yellow
                Remove-Item -Recurse -Force ios
            }
            else {
                Write-Host "⚠️  iOS directory already exists. Use -Force to overwrite." -ForegroundColor Yellow
                $skipIOS = $true
            }
        }
        
        if (-not $skipIOS) {
            Write-Host "   Running: npx expo prebuild --platform ios" -ForegroundColor Gray
            npx expo prebuild --platform ios --clean
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ iOS project initialized successfully" -ForegroundColor Green
                
                # Install CocoaPods dependencies
                if (Get-Command pod -ErrorAction SilentlyContinue) {
                    Write-Host "   Installing CocoaPods dependencies..." -ForegroundColor Gray
                    Push-Location ios
                    pod install
                    Pop-Location
                    Write-Host "✅ CocoaPods dependencies installed" -ForegroundColor Green
                }
                else {
                    Write-Host "⚠️  CocoaPods not found. Install with: sudo gem install cocoapods" -ForegroundColor Yellow
                    Write-Host "   Then run: cd ios && pod install" -ForegroundColor Yellow
                }
            }
            else {
                Write-Host "❌ Failed to initialize iOS project" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host "⚠️  iOS initialization requires macOS. Skipping..." -ForegroundColor Yellow
        Write-Host "   To initialize iOS on macOS, run this script there." -ForegroundColor Gray
    }
}

# Create .env file if it doesn't exist
Write-Host ""
Write-Host "📝 Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "   Copying .env.example to .env..." -ForegroundColor Gray
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env file from .env.example" -ForegroundColor Green
        Write-Host "   ⚠️  Please edit .env with your API URLs" -ForegroundColor Yellow
    }
    else {
        Write-Host "⚠️  .env.example not found. Creating default .env..." -ForegroundColor Yellow
        @"
# API Configuration
API_BASE_URL=http://localhost:8000
WS_BASE_URL=ws://localhost:8000

# Environment
NODE_ENV=development
"@ | Out-File -FilePath ".env" -Encoding ASCII
        Write-Host "✅ Created default .env file" -ForegroundColor Green
    }
}
else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Native project initialization complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "android") {
    Write-Host "🤖 Android:" -ForegroundColor Yellow
    Write-Host "   1. Open android/ in Android Studio" -ForegroundColor Gray
    Write-Host "   2. Wait for Gradle sync to complete" -ForegroundColor Gray
    Write-Host "   3. Run: npm run android" -ForegroundColor Gray
    Write-Host ""
}

if (Test-Path "ios") {
    Write-Host "🍎 iOS:" -ForegroundColor Yellow
    Write-Host "   1. Open ios/CryptoOrchestrator.xcworkspace in Xcode" -ForegroundColor Gray
    Write-Host "   2. Select your development team in Signing & Capabilities" -ForegroundColor Gray
    Write-Host "   3. Run: npm run ios" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "📱 Start Metro bundler:" -ForegroundColor Yellow
Write-Host "   npm start" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 Configure API URL in .env:" -ForegroundColor Yellow
Write-Host "   - iOS Simulator: http://localhost:8000" -ForegroundColor Gray
Write-Host "   - Android Emulator: http://10.0.2.2:8000" -ForegroundColor Gray
Write-Host "   - Physical Device: http://YOUR_COMPUTER_IP:8000" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 Documentation: See README.md for detailed setup instructions" -ForegroundColor Cyan
Write-Host ""
