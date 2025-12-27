#!/bin/bash
# Bash script to prepare mobile app for App Store/Play Store submission
# This script helps verify all requirements are met before submission

set -e

echo "🚀 CryptoOrchestrator App Store Submission Preparation"
echo "============================================================"
echo ""

# Check if in mobile directory
if [ ! -f "app.json" ]; then
    echo "❌ Error: Must run from mobile/ directory"
    echo "   Please run: cd mobile && ./scripts/prepare-submission.sh"
    exit 1
fi

echo "📋 Checking Prerequisites..."
echo ""

# Check Node.js
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ $NODE_VERSION"
else
    echo "❌ Not installed"
    exit 1
fi

# Check npm
echo -n "Checking npm... "
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ $NPM_VERSION"
else
    echo "❌ Not installed"
    exit 1
fi

# Check EAS CLI
echo -n "Checking EAS CLI... "
if command -v eas &> /dev/null; then
    EAS_VERSION=$(eas --version 2>/dev/null || echo "installed")
    echo "✅ $EAS_VERSION"
else
    echo "⚠️  Not installed"
    echo "   Install with: npm install -g eas-cli"
fi

echo ""
echo "📦 Checking Configuration Files..."
echo ""

# Check app.json
echo -n "Checking app.json... "
if [ -f "app.json" ]; then
    if grep -q "your-project-id-here" app.json; then
        echo "⚠️  Project ID not set"
        echo "   Run: eas init"
    else
        echo "✅ Configured"
    fi
else
    echo "❌ Not found"
    exit 1
fi

# Check eas.json
echo -n "Checking eas.json... "
if [ -f "eas.json" ]; then
    echo "✅ Found"
else
    echo "⚠️  Not found"
    echo "   Create with: eas build:configure"
fi

echo ""
echo "🖼️  Checking Assets..."
echo ""

# Check app icon
echo -n "Checking app icon... "
if [ -f "assets/icon.png" ]; then
    echo "✅ Found"
else
    echo "❌ Missing"
    echo "   Required: assets/icon.png (1024x1024 PNG)"
fi

# Check adaptive icon
echo -n "Checking Android adaptive icon... "
if [ -f "assets/adaptive-icon.png" ]; then
    echo "✅ Found"
else
    echo "❌ Missing"
    echo "   Required: assets/adaptive-icon.png (1024x1024 PNG)"
fi

# Check splash screen
echo -n "Checking splash screen... "
if [ -f "assets/splash.png" ]; then
    echo "✅ Found"
else
    echo "❌ Missing"
    echo "   Required: assets/splash.png (2048x2048 PNG)"
fi

# Check feature graphic
echo -n "Checking Android feature graphic... "
if [ -f "assets/feature-graphic.png" ]; then
    echo "✅ Found"
else
    echo "⚠️  Missing (recommended)"
    echo "   Recommended: assets/feature-graphic.png (1024x500 PNG)"
fi

echo ""
echo "📸 Checking Screenshots..."
echo ""

# Check iOS screenshots
IOS_SCREENSHOTS=0
if [ -d "assets/screenshots/ios" ]; then
    IOS_SCREENSHOTS=$(find assets/screenshots/ios -name "*.png" 2>/dev/null | wc -l)
fi
echo "iOS screenshots: $IOS_SCREENSHOTS found"
if [ "$IOS_SCREENSHOTS" -eq 0 ]; then
    echo "   ⚠️  No screenshots found"
    echo "   Required: At least 1 screenshot per device size"
fi

# Check Android screenshots
ANDROID_SCREENSHOTS=0
if [ -d "assets/screenshots/android" ]; then
    ANDROID_SCREENSHOTS=$(find assets/screenshots/android -name "*.png" 2>/dev/null | wc -l)
fi
echo "Android screenshots: $ANDROID_SCREENSHOTS found"
if [ "$ANDROID_SCREENSHOTS" -lt 2 ]; then
    echo "   ⚠️  Less than 2 screenshots found"
    echo "   Required: Minimum 2 screenshots"
fi

echo ""
echo "🔐 Checking Credentials..."
echo ""

# Check Google service account
echo -n "Checking Google service account... "
if [ -f "google-service-account.json" ]; then
    echo "✅ Found"
else
    echo "⚠️  Not found"
    echo "   Required for automated Android submission"
    echo "   See: docs/MOBILE_APP_STORE_SUBMISSION.md"
fi

# Check environment variables
echo -n "Checking iOS submission credentials... "
if [ -n "$APPLE_ID" ] && [ -n "$ASC_APP_ID" ] && [ -n "$APPLE_TEAM_ID" ]; then
    echo "✅ Environment variables set"
else
    echo "⚠️  Environment variables not set"
    echo "   Set: APPLE_ID, ASC_APP_ID, APPLE_TEAM_ID"
fi

echo ""
echo "📚 Checking Documentation..."
echo ""

# Check privacy policy
echo -n "Checking privacy policy... "
if [ -f "../docs/PRIVACY_POLICY.md" ]; then
    echo "✅ Found"
else
    echo "⚠️  Not found"
    echo "   Required: Privacy policy URL for stores"
fi

# Check terms of service
echo -n "Checking terms of service... "
if [ -f "../docs/TERMS_OF_SERVICE.md" ]; then
    echo "✅ Found"
else
    echo "⚠️  Not found (optional)"
fi

echo ""
echo "============================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Create missing assets (icons, screenshots)"
echo "2. Set up Apple Developer and Google Play accounts"
echo "3. Initialize EAS project: eas init"
echo "4. Configure eas.json with your credentials"
echo "5. Create production builds: eas build --platform all --profile production"
echo "6. Test builds on physical devices"
echo "7. Submit to stores: eas submit --platform all --profile production"
echo ""
echo "📖 See docs/MOBILE_APP_STORE_SUBMISSION.md for complete guide"
echo ""

