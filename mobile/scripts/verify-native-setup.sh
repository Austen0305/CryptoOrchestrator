#!/bin/bash
# Verify Native Project Setup Script
# Checks if iOS and Android native projects are properly initialized

echo "🔍 Verifying Native Project Setup..."
echo ""

ALL_GOOD=true

# Check Android
echo "🤖 Checking Android project..."
if [ -d "android" ]; then
    echo "   ✅ android/ directory exists"
    
    if [ -d "android/app" ]; then
        echo "   ✅ android/app/ directory exists"
    else
        echo "   ❌ android/app/ directory missing"
        ALL_GOOD=false
    fi
    
    if [ -f "android/build.gradle" ]; then
        echo "   ✅ android/build.gradle exists"
    else
        echo "   ❌ android/build.gradle missing"
        ALL_GOOD=false
    fi
    
    if [ -f "android/local.properties" ]; then
        echo "   ✅ android/local.properties exists"
    else
        echo "   ⚠️  android/local.properties missing (create manually or run init script)"
    fi
else
    echo "   ❌ android/ directory not found"
    echo "      Run: npm run init:native:android"
    ALL_GOOD=false
fi

echo ""

# Check iOS (macOS only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Checking iOS project..."
    if [ -d "ios" ]; then
        echo "   ✅ ios/ directory exists"
        
        if [ -d "ios/CryptoOrchestrator.xcworkspace" ]; then
            echo "   ✅ iOS workspace exists"
        else
            echo "   ❌ iOS workspace missing"
            ALL_GOOD=false
        fi
        
        if [ -f "ios/Podfile" ]; then
            echo "   ✅ Podfile exists"
        else
            echo "   ❌ Podfile missing"
            ALL_GOOD=false
        fi
        
        if [ -d "ios/Pods" ]; then
            echo "   ✅ CocoaPods dependencies installed"
        else
            echo "   ⚠️  CocoaPods dependencies not installed"
            echo "      Run: cd ios && pod install"
        fi
    else
        echo "   ❌ ios/ directory not found"
        echo "      Run: npm run init:native:ios"
        ALL_GOOD=false
    fi
else
    echo "🍎 iOS check skipped (requires macOS)"
fi

echo ""

# Check configuration files
echo "📝 Checking configuration files..."
if [ -f "app.json" ]; then
    echo "   ✅ app.json exists"
else
    echo "   ❌ app.json missing"
    ALL_GOOD=false
fi

if [ -f ".env" ]; then
    echo "   ✅ .env exists"
else
    echo "   ⚠️  .env missing (copy from .env.example)"
fi

if [ -f "eas.json" ]; then
    echo "   ✅ eas.json exists"
else
    echo "   ⚠️  eas.json missing (optional, for EAS builds)"
fi

echo ""

# Summary
if [ "$ALL_GOOD" = true ]; then
    echo "✅ All native projects are properly initialized!"
    echo ""
    echo "Next steps:"
    echo "  1. Start Metro: npm start"
    echo "  2. Run on device: npm run ios (or npm run android)"
else
    echo "❌ Some native projects are missing or incomplete"
    echo ""
    echo "To fix:"
    echo "  Run: npm run init:native"
    echo "  Or: npm run init:native:force (to overwrite existing)"
fi

echo ""
