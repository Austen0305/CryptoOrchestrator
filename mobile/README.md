# CryptoOrchestrator Mobile App Setup Guide

## 📱 Overview

This guide will help you set up and run the CryptoOrchestrator mobile app on iOS and Android devices.

## 🔧 Prerequisites

### Required Software

1. **Node.js** (v18 or later)
   ```bash
   node --version  # Should be v18+
   ```

2. **React Native CLI**
   ```bash
   npm install -g react-native-cli
   ```

3. **Watchman** (macOS only - recommended)
   ```bash
   brew install watchman
   ```

### iOS Requirements

4. **Xcode** (14.0 or later) - macOS only
   - Install from Mac App Store
   - Install Xcode Command Line Tools:
     ```bash
     xcode-select --install
     ```

5. **CocoaPods**
   ```bash
   sudo gem install cocoapods
   ```

### Android Requirements

6. **Android Studio**
   - Download from https://developer.android.com/studio
   - Install Android SDK (API 33 or later)
   - Install Android SDK Platform-Tools
   - Install Android SDK Build-Tools

7. **Java Development Kit (JDK 17)**
   ```bash
   # Check Java version
   java -version  # Should be 17
   ```

8. **Environment Variables** (Add to ~/.bashrc or ~/.zshrc):
   ```bash
   export ANDROID_HOME=$HOME/Library/Android/sdk  # macOS
   # OR
   export ANDROID_HOME=$HOME/Android/Sdk  # Linux
   # OR
   export ANDROID_HOME=C:\Users\YourUsername\AppData\Local\Android\Sdk  # Windows

   export PATH=$PATH:$ANDROID_HOME/emulator
   export PATH=$PATH:$ANDROID_HOME/platform-tools
   ```

## 🚀 Initial Setup

### 1. Install Dependencies

```bash
cd mobile
npm install
```

### 2. Configure Environment

Edit `.env` file with your settings:

```env
# For iOS Simulator
API_BASE_URL=http://localhost:8000
WS_BASE_URL=ws://localhost:8000

# For Android Emulator
# API_BASE_URL=http://10.0.2.2:8000
# WS_BASE_URL=ws://10.0.2.2:8000

# For Physical Device (use your computer's IP)
# API_BASE_URL=http://192.168.1.100:8000
# WS_BASE_URL=ws://192.168.1.100:8000
```

### 3. iOS Setup (macOS only)

```bash
cd ios
pod install
cd ..
```

**Troubleshooting iOS Pod Install:**
```bash
# If pod install fails, try:
cd ios
pod deintegrate
pod cache clean --all
pod install
cd ..
```

### 4. Android Setup

No additional setup needed - Gradle will handle dependencies automatically.

**Troubleshooting Android:**
```bash
# Clean Gradle cache if needed
cd android
./gradlew clean
cd ..
```

## 📱 Running the App

### Start Metro Bundler (Required First)

```bash
cd mobile
npm start
```

Keep this terminal running while you develop.

### iOS Simulator

**Option 1: Using npm script**
```bash
npm run ios
```

**Option 2: Specific simulator**
```bash
npm run ios -- --simulator="iPhone 15 Pro"
```

**Option 3: From Xcode**
1. Open `ios/CryptoOrchestratorMobile.xcworkspace` in Xcode
2. Select your target device/simulator
3. Click the Run button (▶️)

### Android Emulator

**Option 1: Using npm script**
```bash
npm run android
```

**Option 2: Specific device**
```bash
# List available devices
adb devices

# Run on specific device
npm run android -- --deviceId=<device-id>
```

**Option 3: From Android Studio**
1. Open `android/` folder in Android Studio
2. Select your target device/emulator
3. Click the Run button (▶️)

### Physical Device

#### iOS Device

1. Connect iPhone via USB
2. Open `ios/CryptoOrchestratorMobile.xcworkspace` in Xcode
3. Select your device from the dropdown
4. Update bundle identifier and signing certificate
5. Click Run (▶️)

**Update `.env` with your computer's IP:**
```env
API_BASE_URL=http://192.168.1.100:8000
WS_BASE_URL=ws://192.168.1.100:8000
```

#### Android Device

1. Enable Developer Options on Android:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times
   
2. Enable USB Debugging:
   - Settings → Developer Options → USB Debugging

3. Connect device via USB

4. Verify device is connected:
   ```bash
   adb devices
   ```

5. Run the app:
   ```bash
   npm run android
   ```

**Update `.env` with your computer's IP:**
```env
API_BASE_URL=http://192.168.1.100:8000
WS_BASE_URL=ws://192.168.1.100:8000
```

## 🔑 Biometric Authentication Setup

### iOS

Biometric authentication (Face ID / Touch ID) works automatically on physical devices.

**Testing on Simulator:**
1. Go to Features → Face ID / Touch ID
2. Toggle "Enrolled" to enable
3. When prompted in app, select "Matching Face/Touch"

### Android

**Testing on Emulator:**
1. Open Extended Controls (⋮ button)
2. Go to Fingerprint section
3. Add a fingerprint
4. When prompted in app, click "Touch the sensor"

## 🐛 Common Issues & Solutions

### Metro Bundler Issues

**Error: "Metro Bundler is already running"**
```bash
lsof -ti:8081 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8081   # Windows (then kill the process)
```

**Error: "Unable to resolve module"**
```bash
# Clear Metro cache
npm start -- --reset-cache

# OR
rm -rf node_modules
npm install
```

### iOS Build Errors

**Error: "Signing for targets failed"**
- Open Xcode
- Select the project
- Go to Signing & Capabilities
- Select your development team

**Error: "CocoaPods not found"**
```bash
sudo gem install cocoapods
```

**Error: "Library not found"**
```bash
cd ios
pod deintegrate
pod install
cd ..
```

### Android Build Errors

**Error: "SDK location not found"**
Create `android/local.properties`:
```properties
sdk.dir=/Users/YourUsername/Library/Android/sdk  # macOS
# OR
sdk.dir=C:\\Users\\YourUsername\\AppData\\Local\\Android\\Sdk  # Windows
```

**Error: "Execution failed for task ':app:validateSigningDebug'"**
```bash
cd android
./gradlew clean
cd ..
```

**Error: "INSTALL_FAILED_INSUFFICIENT_STORAGE"**
- Free up space on your device/emulator
- Or uninstall the app first: `adb uninstall com.cryptoorchestratomobile`

### API Connection Issues

**Error: "Network request failed"**

1. Ensure backend is running:
   ```bash
   # In main project directory
   npm run dev:fastapi
   ```

2. Check `.env` file has correct API URL:
   - iOS Simulator: `http://localhost:8000`
   - Android Emulator: `http://10.0.2.2:8000`
   - Physical Device: `http://YOUR_COMPUTER_IP:8000`

3. Find your computer's IP:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet "
   
   # Windows
   ipconfig
   ```

4. Ensure firewall allows connections on port 8000

### Biometric Authentication Not Working

**iOS:**
- Simulator: Enable Face ID/Touch ID in Features menu
- Device: Check Settings → Face ID & Passcode

**Android:**
- Emulator: Add fingerprint in Extended Controls
- Device: Check Settings → Security → Fingerprint

## 📦 Building for Production

### iOS Production Build

1. **Update version and build number** in `ios/CryptoOrchestratorMobile/Info.plist`

2. **Create Archive in Xcode:**
   ```bash
   # OR via command line
   cd ios
   xcodebuild archive \
     -workspace CryptoOrchestratorMobile.xcworkspace \
     -scheme CryptoOrchestratorMobile \
     -archivePath ./build/CryptoOrchestratorMobile.xcarchive
   ```

3. **Export IPA:**
   - Open Xcode
   - Window → Organizer
   - Select your archive
   - Click "Distribute App"
   - Follow wizard for App Store or Ad Hoc distribution

### Android Production Build

1. **Generate signing key** (first time only):
   ```bash
   keytool -genkeypair -v -storetype PKCS12 \
     -keystore android/app/release.keystore \
     -alias cryptoorchestrator \
     -keyalg RSA -keysize 2048 -validity 10000
   ```

2. **Configure signing** in `android/gradle.properties`:
   ```properties
   MYAPP_RELEASE_STORE_FILE=release.keystore
   MYAPP_RELEASE_KEY_ALIAS=cryptoorchestrator
   MYAPP_RELEASE_STORE_PASSWORD=your_password
   MYAPP_RELEASE_KEY_PASSWORD=your_password
   ```

3. **Build APK:**
   ```bash
   cd android
   ./gradlew assembleRelease
   # Output: android/app/build/outputs/apk/release/app-release.apk
   ```

4. **Build AAB (for Play Store):**
   ```bash
   cd android
   ./gradlew bundleRelease
   # Output: android/app/build/outputs/bundle/release/app-release.aab
   ```

## 🔍 Debugging

### React Native Debugger

1. Install standalone debugger:
   ```bash
   brew install --cask react-native-debugger  # macOS
   ```

2. Open React Native Debugger app

3. In app, shake device or press:
   - iOS: Cmd+D (simulator) or shake device
   - Android: Cmd+M (emulator) or shake device

4. Select "Debug"

### Chrome DevTools

1. In app, open developer menu (see above)
2. Select "Debug"
3. Chrome will open at `http://localhost:8081/debugger-ui`
4. Open Chrome DevTools (F12)

### View Logs

**iOS:**
```bash
# View all logs
xcrun simctl spawn booted log stream

# Filter for your app
xcrun simctl spawn booted log stream --predicate 'processImagePath endswith "CryptoOrchestratorMobile"'
```

**Android:**
```bash
# View all logs
adb logcat

# Filter for React Native
adb logcat *:S ReactNative:V ReactNativeJS:V
```

### Performance Profiling

1. Open developer menu
2. Select "Perf Monitor"
3. Monitor FPS, memory, and JS thread usage

## 📚 Development Resources

- **React Native Docs:** https://reactnative.dev/docs/getting-started
- **React Navigation:** https://reactnavigation.org/
- **React Query:** https://tanstack.com/query/latest
- **React Native Biometrics:** https://github.com/SelfLender/react-native-biometrics

## 🎯 Next Steps

1. ✅ Complete initial setup (install dependencies)
2. ✅ Configure environment variables
3. ✅ Run on iOS simulator/Android emulator
4. ⏳ Test biometric authentication
5. ⏳ Test API connectivity
6. ⏳ Test WebSocket real-time updates
7. ⏳ Build and test on physical device
8. ⏳ Customize app icons and splash screen
9. ⏳ Implement additional features (Portfolio, Trading, Settings screens)
10. ⏳ Prepare production builds

## 🆘 Getting Help

If you encounter issues not covered here:

1. Check React Native documentation
2. Search GitHub issues
3. Check Stack Overflow
4. Review logs carefully for error messages

## 📄 File Structure

```
mobile/
├── android/              # Android native code
├── ios/                  # iOS native code
├── src/
│   ├── screens/         # Screen components
│   │   └── DashboardScreen.tsx
│   ├── services/        # API and authentication services
│   │   ├── api.ts
│   │   ├── BiometricAuth.ts
│   │   └── WebSocketService.ts
│   ├── types/           # TypeScript type definitions
│   │   └── index.ts
│   └── App.tsx          # Main app component
├── .env                 # Environment configuration
├── babel.config.js      # Babel configuration
├── metro.config.js      # Metro bundler configuration
├── package.json         # Dependencies
└── tsconfig.json        # TypeScript configuration
```

---

**Ready to Trade on the Go! 🚀📱**
