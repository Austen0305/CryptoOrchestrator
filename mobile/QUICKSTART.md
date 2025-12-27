# Mobile App Quick Start

## ⚠️ Important: Native Project Initialization Required

The mobile app code is ready, but you need to initialize the native iOS and Android projects using Expo.

## 🚀 Quick Setup (Recommended Method)

### Step 1: Initialize Native Projects

The mobile app uses **Expo** with React Native. Initialize native projects using the automated script:

**Windows (PowerShell):**
```powershell
cd mobile
npm run init:native
```

**macOS/Linux:**
```bash
cd mobile
npm run init:native
```

This script will:
- ✅ Check prerequisites (Node.js, npm, Expo)
- ✅ Install dependencies if needed
- ✅ Generate `ios/` folder (macOS only)
- ✅ Generate `android/` folder
- ✅ Install CocoaPods dependencies (iOS, macOS only)
- ✅ Create `android/local.properties` with SDK path
- ✅ Create `.env` file if missing

**Alternative: Manual Expo Prebuild**
```bash
cd mobile

# Initialize Android
npx expo prebuild --platform android --clean

# Initialize iOS (macOS only)
npx expo prebuild --platform ios --clean

# Install iOS dependencies (macOS only)
cd ios && pod install && cd ..
```

### Step 2: Verify Setup

Check that everything is initialized correctly:

```bash
cd mobile
npm run verify:native
```

### Step 3: Configure Environment

Edit `mobile/.env` with your API URLs:

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

### Step 4: Start the App

**Start Metro Bundler:**
```bash
cd mobile
npm start
```

**In another terminal, run on device:**

**iOS (macOS only):**
```bash
cd mobile
npm run ios
# or
npm run run:ios
```

**Android:**
```bash
cd mobile
npm run android
# or
npm run run:android
```

## 🎯 Alternative Methods

### Option A: Expo Go (No Build Required)

Test the app without building native projects:

```bash
cd mobile
npm start
# Scan QR code with Expo Go app on your phone
```

**Note:** Some features (biometric auth, push notifications) require native builds.

### Option B: Web (Instant Testing)

Test the app logic in a browser:

```bash
cd mobile
npm run web
```

**Note:** Native features won't work on web.

## 📱 Current Mobile App Features

✅ **Implemented:**
- Biometric authentication (Face ID, Touch ID, Fingerprint)
- Bottom tab navigation (Dashboard, Portfolio, Trading, Settings)
- Real-time WebSocket connection
- React Query data fetching
- API service with axios
- TypeScript type definitions
- Dark theme UI

✅ **Dashboard Screen:**
- Portfolio value display
- 24h performance chart
- Recent trades list
- Market data cards
- Pull-to-refresh
- Real-time updates via WebSocket

⏳ **To Be Completed:**
- Portfolio screen (detailed holdings)
- Trading screen (place orders)
- Settings screen (preferences, security)
- Push notifications
- Background data fetching
- More charts and analytics

## 🔧 Configuration Files Created

✅ All essential files are ready:
- `index.js` - Entry point
- `App.tsx` - Main app with navigation
- `babel.config.js` - Babel configuration
- `metro.config.js` - Metro bundler config
- `tsconfig.json` - TypeScript config
- `.env` - Environment variables
- `src/services/BiometricAuth.ts` - Biometric auth
- `src/services/api.ts` - API client
- `src/services/WebSocketService.ts` - Real-time data
- `src/screens/DashboardScreen.tsx` - Dashboard UI
- `src/types/index.ts` - Type definitions

## 🎯 Recommended Next Steps

1. **Initialize Native Projects** (Option 1 above)
2. **Test on Simulator/Emulator**
3. **Connect to Backend API**
4. **Test Biometric Authentication**
5. **Implement Remaining Screens**

## 📖 Full Documentation

See `mobile/README.md` for complete setup instructions, troubleshooting, and platform-specific details.

## 💡 Tips

- **iOS:** Requires macOS with Xcode
- **Android:** Works on Windows, macOS, Linux
- **Expo:** Easiest for testing on physical devices
- **Backend:** Must be running on `http://localhost:8000` (or update `.env`)

## 🆘 Need Help?

1. Check `mobile/README.md` for detailed instructions
2. Review React Native docs: https://reactnative.dev
3. The backend API must be running: `npm run dev:fastapi`

---

**Status: ✅ Code Ready | ⏳ Native Projects Need Initialization**
