# Mobile App Quick Start

## ⚠️ Important: React Native Project Initialization Required

The mobile app code is ready, but you need to initialize the native iOS and Android projects.

## 🚀 Quick Setup (Choose ONE option)

### Option 1: Initialize Fresh React Native Project (Recommended)

This will create the ios/ and android/ folders properly:

```bash
# 1. Go to parent directory
cd "c:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator"

# 2. Create a temporary React Native project
npx react-native@latest init CryptoOrchestratorMobileTemp

# 3. Copy the native folders to our mobile directory
# On Windows PowerShell:
Copy-Item -Recurse .\CryptoOrchestratorMobileTemp\ios .\mobile\ios
Copy-Item -Recurse .\CryptoOrchestratorMobileTemp\android .\mobile\android

# 4. Clean up temp project
Remove-Item -Recurse -Force .\CryptoOrchestratorMobileTemp

# 5. Install iOS pods (macOS only)
cd mobile/ios
pod install
cd ..

# 6. Start the app
npm start
# In another terminal:
npm run ios     # For iOS
# OR
npm run android # For Android
```

### Option 2: Use Expo (Easier, No Native Setup)

If you want a simpler approach without Xcode/Android Studio:

```bash
cd mobile

# Install Expo
npm install expo

# Update package.json scripts to use expo
# Replace "start" script with: "expo start"

# Start Expo
npm start

# Then scan QR code with Expo Go app on your phone
```

### Option 3: Test on Web First (Instant)

You can test the app logic on web while setting up native:

```bash
cd mobile

# Install web dependencies
npm install react-dom react-native-web

# Add web script to package.json:
# "web": "expo start --web"

# Start on web
npm run web
```

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
