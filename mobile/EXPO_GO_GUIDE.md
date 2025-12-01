# 🚀 Expo Go Quick Start - Test Your App NOW!

## ✨ Why Expo Go?
Test your mobile app **instantly** on your phone without building anything. No Xcode, no Android Studio needed!

---

## 📱 Step 1: Install Expo Go App

**On your phone:**
- **iOS:** App Store → Search "Expo Go" → Install
- **Android:** Play Store → Search "Expo Go" → Install

---

## 🔧 Step 2: Setup (Already Done! ✅)

✅ Expo installed
✅ Configuration created
✅ Environment configured with your IP: **10.0.0.22**

---

## 🌐 Step 3: Ensure Same WiFi Network

**CRITICAL:** Your phone and computer must be on the **same WiFi network**!

- Computer WiFi: Check your WiFi settings
- Phone WiFi: Settings → WiFi → Connect to same network

---

## 🚀 Step 4: Start the Backend

Open a **new terminal** and run:

```powershell
cd "c:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator"
npm run dev:fastapi
```

**Wait for:** "Application startup complete" message

---

## 📱 Step 5: Start Expo

In **another terminal**, run:

```powershell
cd "c:\Users\William Walker\OneDrive\Desktop\CryptoOrchestrator\mobile"
npm start
```

This will:
1. Start Metro bundler
2. Show a QR code in the terminal
3. Open a web page with the QR code

---

## 📸 Step 6: Scan QR Code

**On your phone:**

**iOS:**
1. Open **Camera app** (not Expo Go)
2. Point at the QR code
3. Tap the notification that appears
4. It will open in Expo Go

**Android:**
1. Open **Expo Go app**
2. Tap "Scan QR Code"
3. Point at the QR code on your computer screen

---

## 🎉 Step 7: Watch the Magic!

Your app will:
1. Download the JavaScript bundle
2. Show loading screen
3. Prompt for biometric authentication (Face ID/Fingerprint)
4. Load the dashboard with live data!

---

## ✅ What You'll See

- 🔐 **Biometric prompt** on first launch
- 📊 **Dashboard** with portfolio value
- 📈 **Charts** showing performance
- 🔄 **Pull down** to refresh data
- 🎯 **Bottom tabs** for navigation

---

## 🐛 Troubleshooting

### "Cannot connect to Metro bundler"
- **Fix:** Make sure both devices are on same WiFi
- **Check:** Run `ipconfig` to verify IP hasn't changed

### "Network request failed"
- **Fix 1:** Ensure backend is running (`npm run dev:fastapi`)
- **Fix 2:** Check Windows Firewall allows port 8000
- **Fix 3:** Verify .env has correct IP (10.0.0.22)

### "Unable to resolve module"
- **Fix:** Press `r` in the terminal to reload
- **Or:** Stop (Ctrl+C) and run `npm start` again

### Blank/White Screen
- **Fix:** Shake your phone → "Reload"
- **Or:** Press `r` in terminal to reload

### Biometric Auth Not Working
- **iOS:** Settings → Face ID & Passcode → Enable for Expo Go
- **Android:** Settings → Security → Fingerprint → Ensure enrolled

---

## 🎨 Customization

### Change App Icon (Later)
Replace `mobile/assets/icon.png` with your own 1024x1024 PNG

### Change Splash Screen (Later)
Replace `mobile/assets/splash.png` with your own design

---

## 📊 Testing Features

Once the app loads, test:

1. **Biometric Auth** ✅
   - Should prompt on first launch
   - Tap to authenticate

2. **Dashboard** ✅
   - Shows portfolio value
   - Displays charts
   - Lists recent trades

3. **Pull to Refresh** ✅
   - Swipe down on dashboard
   - Data should reload

4. **Navigation** ✅
   - Tap bottom tabs
   - Switch between screens

5. **Live Updates** ✅
   - Data updates every 5 seconds
   - WebSocket connection active

---

## 🔥 Hot Reload is Active!

When you save changes to any `.tsx` or `.ts` file:
- App automatically reloads
- See changes instantly
- No need to rebuild!

---

## 💡 Development Tips

### View Logs
Shake your phone → "Show Developer Menu" → "Enable Fast Refresh"

### Debug Menu
Shake phone → Developer Menu:
- Reload
- Debug Remote JS
- Show Performance Monitor
- Enable Hot Reloading

### Console Logs
Check the terminal where you ran `npm start` - all `console.log()` statements appear there!

---

## 🎯 Quick Commands

```powershell
# Start Expo
npm start

# Start with cache cleared
npm start --clear

# Start and open in Expo Go automatically (if connected before)
npm start --dev-client

# Stop
Ctrl+C in terminal
```

---

## 📱 Later: Build Standalone App

When you're ready to build a real app:

```powershell
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Build for Android
eas build --platform android

# Build for iOS (needs Mac)
eas build --platform ios
```

But for now, **Expo Go is perfect for testing!**

---

## ✨ What's Next?

After testing with Expo Go:

1. ✅ Verify all features work
2. ✅ Test on multiple devices
3. ✅ Implement remaining screens
4. ✅ Add push notifications
5. ✅ Build standalone apps (later)

---

## 🎊 You're Ready!

Run these two commands:

**Terminal 1:**
```powershell
npm run dev:fastapi
```

**Terminal 2:**
```powershell
cd mobile
npm start
```

Then **scan the QR code** with your phone!

---

**🚀 Your crypto trading app will be running on your phone in 30 seconds!**

---

## 📞 Need Help?

- Expo Docs: https://docs.expo.dev
- Expo Go App: https://expo.dev/client
- Troubleshooting: See mobile/README.md

**Happy Trading! 📱💰🚀**
