#!/bin/bash
# Initialize native iOS and Android projects for CryptoOrchestrator mobile app

set -e

echo "🚀 Initializing native mobile projects..."

# Check if we're in the mobile directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the mobile directory"
    exit 1
fi

# Check for required tools
command -v npx >/dev/null 2>&1 || { echo "❌ npx is required but not installed. Aborting." >&2; exit 1; }

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Initialize iOS project (if on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Initializing iOS project..."
    if [ ! -d "ios" ]; then
        npx expo prebuild --platform ios
        echo "✅ iOS project initialized"
    else
        echo "⚠️  iOS directory already exists, skipping..."
    fi
else
    echo "⚠️  Skipping iOS initialization (macOS required)"
fi

# Initialize Android project
echo "🤖 Initializing Android project..."
if [ ! -d "android" ]; then
    npx expo prebuild --platform android
    echo "✅ Android project initialized"
else
    echo "⚠️  Android directory already exists, skipping..."
fi

# Install native dependencies
echo "📦 Installing native dependencies..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    cd ios && pod install && cd ..
    echo "✅ iOS dependencies installed"
fi

echo "✅ Native projects initialized successfully!"
echo ""
echo "Next steps:"
echo "  - iOS: Open ios/CryptoOrchestrator.xcworkspace in Xcode"
echo "  - Android: Open android/ in Android Studio"
echo "  - Run: npm run ios or npm run android"

