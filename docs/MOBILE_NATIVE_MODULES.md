# Mobile Native Modules Configuration

## Status: ✅ Ready for Prebuild

All native modules are configured and ready for initialization.

## Native Services Configured

### 1. Push Notifications (`expo-notifications`)
- **Service**: `mobile/src/services/PushNotificationService.ts`
- **Configuration**: `mobile/app.json` (expo-notifications plugin)
- **Features**:
  - Push token registration
  - Backend subscription management
  - Local notifications
  - Badge management
  - Notification categories

### 2. Biometric Authentication (`react-native-biometrics`, `react-native-keychain`)
- **Service**: `mobile/src/services/BiometricAuth.ts`
- **Configuration**: `mobile/app.json` (expo-secure-store plugin)
- **Features**:
  - Face ID / Touch ID / Fingerprint
  - Secure credential storage
  - Biometric signatures
  - PIN/password fallback

### 3. Offline Mode (`@react-native-async-storage/async-storage`, `@react-native-community/netinfo`)
- **Service**: `mobile/src/services/OfflineService.ts`
- **Features**:
  - Action queuing
  - Network status monitoring
  - Automatic sync when online
  - Data caching with TTL

## Prebuild Process

### Prerequisites
- Node.js 18+
- npm or yarn
- Expo CLI (installed via npx)
- For iOS: Xcode and CocoaPods (macOS only)
- For Android: Android Studio and Android SDK

### Initialization Steps

#### Option 1: Use Provided Scripts (Recommended)

**Windows:**
```powershell
cd mobile
npm run init:native
# Or for force rebuild:
npm run init:native:force
```

**macOS/Linux:**
```bash
cd mobile
npm run init:native
# Or for force rebuild:
npm run init:native:force
```

#### Option 2: Manual Prebuild

**Both Platforms:**
```bash
cd mobile
npx expo prebuild --clean
```

**iOS Only:**
```bash
cd mobile
npx expo prebuild --platform ios --clean
cd ios && pod install
```

**Android Only:**
```bash
cd mobile
npx expo prebuild --platform android --clean
```

### Build Verification

#### iOS Build
```bash
cd mobile
npm run build:ios:local
# Or for EAS build:
npm run build:ios
```

#### Android Build
```bash
cd mobile
npm run build:android:local
# Or for EAS build:
npm run build:android
```

### Verification Script

Run the verification script to check native setup:
```bash
cd mobile
npm run verify:native
```

## Native Module Dependencies

All required native modules are in `mobile/package.json`:

- `expo-notifications` - Push notifications
- `expo-secure-store` - Secure storage
- `react-native-biometrics` - Biometric authentication
- `react-native-keychain` - Keychain access
- `@react-native-async-storage/async-storage` - Offline storage
- `@react-native-community/netinfo` - Network detection
- `expo-device` - Device information

## Configuration Files

### `mobile/app.json`
- iOS bundle identifier: `com.cryptoorchestrator.mobile`
- Android package: `com.cryptoorchestrator.mobile`
- Permissions configured for both platforms
- Native plugins configured

### Native Service Files
- `mobile/src/services/PushNotificationService.ts` - Complete implementation
- `mobile/src/services/BiometricAuth.ts` - Complete implementation
- `mobile/src/services/OfflineService.ts` - Complete implementation

## Testing Native Features

### Push Notifications
1. Run app on physical device (notifications don't work on simulator)
2. Grant notification permissions
3. Test registration and receiving notifications

### Biometric Auth
1. Test on device with Face ID / Touch ID / Fingerprint
2. Test credential storage and retrieval
3. Test authentication flow

### Offline Mode
1. Disable network connection
2. Queue actions (trades, bot actions)
3. Re-enable network
4. Verify automatic sync

## Troubleshooting

### Prebuild Errors
- Ensure all dependencies are installed: `npm install`
- Check Node.js version: `node --version` (should be 18+)
- Clear Expo cache: `npx expo start -c`

### iOS Build Errors
- Run `pod install` in `ios/` directory
- Check Xcode version (13.0+)
- Verify CocoaPods is installed: `pod --version`

### Android Build Errors
- Check Android SDK is installed
- Verify `ANDROID_HOME` environment variable
- Check Gradle version compatibility

## Next Steps

1. Run `npm run init:native` to initialize native projects
2. Test builds: `npm run build:ios:local` and `npm run build:android:local`
3. Test native features on physical devices
4. Configure EAS for production builds

## Status

- ✅ Native services implemented
- ✅ Configuration files ready
- ✅ Prebuild scripts available
- ⏳ Prebuild execution (requires local environment)
- ⏳ Build verification (requires local environment)
