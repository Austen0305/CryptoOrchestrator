#!/bin/bash
# Complete Native Project Initialization Script for CryptoOrchestrator Mobile
# This script initializes both iOS and Android native projects using Expo

set -e

FORCE=false
ANDROID_ONLY=false
IOS_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --android-only)
            ANDROID_ONLY=true
            shift
            ;;
        --ios-only)
            IOS_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🚀 CryptoOrchestrator Mobile - Native Project Initialization"
echo "============================================================"
echo ""

# Check if we're in the mobile directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the mobile directory"
    echo "   cd mobile"
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "   Install from: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js version: $NODE_VERSION"

# Check for npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed."
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ] || [ "$FORCE" = true ]; then
    echo ""
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Check for Expo
echo ""
echo "🔍 Checking Expo installation..."

# Check if expo is in package.json dependencies
if [ -f "package.json" ]; then
    if grep -q '"expo"' package.json; then
        echo "✅ Expo found in dependencies"
    else
        echo "⚠️  Expo not found in dependencies. Installing..."
        npm install expo
        if [ $? -ne 0 ]; then
            echo "❌ Failed to install Expo"
            exit 1
        fi
        echo "✅ Expo installed"
    fi
fi

# Check for npx
if ! command -v npx &> /dev/null; then
    echo "❌ npx is required but not installed."
    exit 1
fi
echo "✅ npx available"

# Initialize Android project
if [ "$IOS_ONLY" = false ]; then
    echo ""
    echo "🤖 Initializing Android project..."
    
    if [ -d "android" ]; then
        if [ "$FORCE" = true ]; then
            echo "⚠️  Android directory exists. Removing..."
            rm -rf android
        else
            echo "⚠️  Android directory already exists. Use --force to overwrite."
            SKIP_ANDROID=true
        fi
    fi
    
    if [ -z "$SKIP_ANDROID" ]; then
        echo "   Running: npx expo prebuild --platform android"
        npx expo prebuild --platform android --clean
        
        if [ $? -eq 0 ]; then
            echo "✅ Android project initialized successfully"
            
            # Create local.properties if it doesn't exist
            if [ ! -f "android/local.properties" ]; then
                echo "   Creating android/local.properties..."
                ANDROID_SDK_PATH="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
                
                if [ -d "$ANDROID_SDK_PATH" ]; then
                    echo "sdk.dir=$ANDROID_SDK_PATH" > android/local.properties
                    echo "✅ Created local.properties with SDK path: $ANDROID_SDK_PATH"
                else
                    echo "⚠️  Android SDK not found. Please set ANDROID_HOME or create android/local.properties manually."
                fi
            fi
        else
            echo "❌ Failed to initialize Android project"
            echo "   Make sure Expo is properly installed: npm install -g expo-cli"
        fi
    fi
fi

# Initialize iOS project (macOS only)
if [ "$ANDROID_ONLY" = false ]; then
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "🍎 Initializing iOS project..."
        
        if [ -d "ios" ]; then
            if [ "$FORCE" = true ]; then
                echo "⚠️  iOS directory exists. Removing..."
                rm -rf ios
            else
                echo "⚠️  iOS directory already exists. Use --force to overwrite."
                SKIP_IOS=true
            fi
        fi
        
        if [ -z "$SKIP_IOS" ]; then
            echo "   Running: npx expo prebuild --platform ios"
            npx expo prebuild --platform ios --clean
            
            if [ $? -eq 0 ]; then
                echo "✅ iOS project initialized successfully"
                
                # Install CocoaPods dependencies
                if command -v pod &> /dev/null; then
                    echo "   Installing CocoaPods dependencies..."
                    cd ios
                    pod install
                    cd ..
                    echo "✅ CocoaPods dependencies installed"
                else
                    echo "⚠️  CocoaPods not found. Install with: sudo gem install cocoapods"
                    echo "   Then run: cd ios && pod install"
                fi
            else
                echo "❌ Failed to initialize iOS project"
            fi
        fi
    else
        echo "⚠️  iOS initialization requires macOS. Skipping..."
        echo "   To initialize iOS on macOS, run this script there."
    fi
fi

# Create .env file if it doesn't exist
echo ""
echo "📝 Checking environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "   Copying .env.example to .env..."
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "   ⚠️  Please edit .env with your API URLs"
    else
        echo "⚠️  .env.example not found. Creating default .env..."
        cat > .env << EOF
# API Configuration
API_BASE_URL=http://localhost:8000
WS_BASE_URL=ws://localhost:8000

# Environment
NODE_ENV=development
EOF
        echo "✅ Created default .env file"
    fi
else
    echo "✅ .env file already exists"
fi

# Summary
echo ""
echo "============================================================"
echo "✅ Native project initialization complete!"
echo ""
echo "Next steps:"
echo ""

if [ -d "android" ]; then
    echo "🤖 Android:"
    echo "   1. Open android/ in Android Studio"
    echo "   2. Wait for Gradle sync to complete"
    echo "   3. Run: npm run android"
    echo ""
fi

if [ -d "ios" ]; then
    echo "🍎 iOS:"
    echo "   1. Open ios/CryptoOrchestrator.xcworkspace in Xcode"
    echo "   2. Select your development team in Signing & Capabilities"
    echo "   3. Run: npm run ios"
    echo ""
fi

echo "📱 Start Metro bundler:"
echo "   npm start"
echo ""
echo "🔧 Configure API URL in .env:"
echo "   - iOS Simulator: http://localhost:8000"
echo "   - Android Emulator: http://10.0.2.2:8000"
echo "   - Physical Device: http://YOUR_COMPUTER_IP:8000"
echo ""
echo "📚 Documentation: See README.md for detailed setup instructions"
echo ""
