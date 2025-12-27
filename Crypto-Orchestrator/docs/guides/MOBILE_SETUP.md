# Mobile App Setup Guide

Complete guide for setting up and building the CryptoOrchestrator mobile app.

## Prerequisites

### For iOS Development (macOS only)
- macOS 12.0 or later
- Xcode 14.0 or later
- CocoaPods (`sudo gem install cocoapods`)
- Apple Developer Account (for device testing and App Store)

### For Android Development
- Android Studio (latest version)
- Android SDK (API level 33+)
- Java Development Kit (JDK 17+)
- Android device or emulator

### Common Requirements
- Node.js 18.x or later
- npm or yarn
- Expo CLI (`npm install -g expo-cli`)

## Quick Start

### 1. Install Dependencies

```bash
cd mobile
npm install
```

### 2. Initialize Native Projects

**On macOS (iOS + Android):**
```bash
npm run init:native
# Or manually:
bash scripts/init-native.sh
```

**On Windows/Linux (Android only):**
```bash
npm run init:native
# Or manually:
powershell -ExecutionPolicy Bypass -File scripts/init-native.ps1
```

### 3. Configure Environment

Create `.env` file in the `mobile` directory:

```env
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_WS_URL=ws://localhost:8000/ws
EXPO_PUBLIC_ENVIRONMENT=development
```

### 4. Run Development Server

```bash
# Start Expo development server
npm start

# Or run on specific platform
npm run ios      # iOS (macOS only)
npm run android  # Android
```

## Building for Production

### iOS Build

1. **Configure App Store Connect:**
   - Create app in App Store Connect
   - Configure bundle identifier in `app.json`
   - Set up certificates and provisioning profiles

2. **Build:**
   ```bash
   npm run build:ios
   ```

3. **Or use EAS Build (Recommended):**
   ```bash
   npm install -g eas-cli
   eas login
   eas build --platform ios
   ```

### Android Build

1. **Configure Google Play Console:**
   - Create app in Google Play Console
   - Configure package name in `app.json`
   - Generate signing key

2. **Build:**
   ```bash
   npm run build:android
   ```

3. **Or use EAS Build (Recommended):**
   ```bash
   eas build --platform android
   ```

## Project Structure

```
mobile/
├── src/
│   ├── screens/          # Screen components
│   │   ├── DashboardScreen.tsx
│   │   ├── LoginScreen.tsx
│   │   ├── PortfolioScreen.tsx
│   │   └── TradingScreen.tsx
│   ├── services/         # API and WebSocket services
│   │   ├── api.ts
│   │   ├── BiometricAuth.ts
│   │   └── WebSocketService.ts
│   ├── hooks/            # Custom React hooks
│   │   └── useWebSocket.ts
│   └── types/            # TypeScript types
│       └── index.ts
├── ios/                  # Native iOS project (generated)
├── android/              # Native Android project (generated)
├── app.json              # Expo configuration
└── package.json
```

## Features

### Implemented
- ✅ Authentication (Login/Register)
- ✅ Dashboard with portfolio overview
- ✅ Portfolio management
- ✅ Trading interface
- ✅ WebSocket real-time updates
- ✅ Biometric authentication

### Planned
- ⏳ Push notifications
- ⏳ Offline mode
- ⏳ Advanced charting
- ⏳ Bot management
- ⏳ Strategy marketplace
- ⏳ Risk management tools

## Testing

### Run Tests
```bash
npm test
```

### Test on Device
```bash
# iOS
npm run ios

# Android
npm run android
```

### Test on Physical Device
1. Install Expo Go app on your device
2. Scan QR code from `npm start`
3. App will load on your device

## Troubleshooting

### iOS Issues

**"No such module" errors:**
```bash
cd ios
pod install
cd ..
```

**Build failures:**
- Clean build folder in Xcode (Product → Clean Build Folder)
- Delete `ios/Pods` and reinstall: `cd ios && pod install`

### Android Issues

**Gradle sync failures:**
- Open `android/` in Android Studio
- Click "Sync Project with Gradle Files"
- Check SDK versions in `build.gradle`

**Build errors:**
- Clean project: `cd android && ./gradlew clean`
- Invalidate caches in Android Studio

### Common Issues

**Metro bundler errors:**
```bash
npm start -- --reset-cache
```

**Node modules issues:**
```bash
rm -rf node_modules
npm install
```

**Expo CLI issues:**
```bash
npm install -g expo-cli@latest
```

## Deployment

### App Store (iOS)

1. Build with EAS:
   ```bash
   eas build --platform ios --profile production
   ```

2. Submit to App Store:
   ```bash
   eas submit --platform ios
   ```

### Google Play (Android)

1. Build with EAS:
   ```bash
   eas build --platform android --profile production
   ```

2. Submit to Google Play:
   ```bash
   eas submit --platform android
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EXPO_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `EXPO_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000/ws` |
| `EXPO_PUBLIC_ENVIRONMENT` | Environment (dev/prod) | `development` |

## Resources

- [Expo Documentation](https://docs.expo.dev/)
- [React Native Documentation](https://reactnative.dev/)
- [EAS Build Documentation](https://docs.expo.dev/build/introduction/)
- [App Store Connect](https://appstoreconnect.apple.com/)
- [Google Play Console](https://play.google.com/console/)

## Support

For issues and questions:
- Check [Troubleshooting](#troubleshooting) section
- Review Expo documentation
- Open an issue on GitHub

---

**Last Updated:** 2025-01-XX

