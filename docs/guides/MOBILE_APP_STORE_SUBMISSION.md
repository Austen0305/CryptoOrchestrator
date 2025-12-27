# Mobile App Store Submission Guide

This comprehensive guide covers preparing and submitting the CryptoOrchestrator mobile app to the Apple App Store and Google Play Store.

## 🎯 Overview

The mobile app is built with **Expo** and uses **EAS Build** for creating production builds. This guide covers:
- Prerequisites and account setup
- Asset requirements (icons, screenshots, descriptions)
- Build configuration
- Submission process
- Post-submission monitoring

## 📋 Prerequisites

### Required Accounts

1. **Apple Developer Account**
   - Cost: $99/year
   - Required for: iOS App Store submission
   - Sign up: [developer.apple.com](https://developer.apple.com)
   - Enable: App Store Connect access

2. **Google Play Developer Account**
   - Cost: $25 one-time fee
   - Required for: Android Play Store submission
   - Sign up: [play.google.com/console](https://play.google.com/console)
   - Enable: Google Play Console access

3. **Expo Account** (Free)
   - Required for: EAS Build service
   - Sign up: [expo.dev](https://expo.dev)
   - Link project: `eas init` or via Expo dashboard

### Required Tools

- **EAS CLI**: `npm install -g eas-cli`
- **Expo CLI**: `npm install -g expo-cli` (optional, EAS CLI includes it)
- **Xcode** (macOS only): For iOS builds and local testing
- **Android Studio** (optional): For Android builds and local testing

## 🏗️ Configuration

### 1. EAS Project Setup

First, initialize EAS for your project:

```bash
cd mobile
eas init
```

This will:
- Create an Expo project (if not already created)
- Link your project to your Expo account
- Update `app.json` with your project ID

### 2. Update `app.json`

Ensure your `app.json` has all required fields:

```json
{
  "expo": {
    "name": "CryptoOrchestrator",
    "slug": "crypto-orchestrator",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#111827"
    },
    "ios": {
      "bundleIdentifier": "com.cryptoorchestrator.mobile",
      "buildNumber": "1",
      "supportsTablet": true,
      "infoPlist": {
        "NSFaceIDUsageDescription": "Use Face ID to unlock CryptoOrchestrator and authenticate transactions",
        "NSCameraUsageDescription": "Camera access is required for QR code scanning",
        "NSPhotoLibraryUsageDescription": "Photo library access is required for profile pictures",
        "NSLocationWhenInUseUsageDescription": "Location access helps provide location-based trading features"
      },
      "config": {
        "usesNonExemptEncryption": false
      }
    },
    "android": {
      "package": "com.cryptoorchestrator.mobile",
      "versionCode": 1,
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#111827"
      },
      "permissions": [
        "USE_BIOMETRIC",
        "USE_FINGERPRINT",
        "CAMERA",
        "INTERNET",
        "VIBRATE"
      ]
    },
    "extra": {
      "eas": {
        "projectId": "your-expo-project-id"
      }
    }
  }
}
```

### 3. Update `eas.json`

Configure build profiles in `eas.json`:

```json
{
  "cli": {
    "version": ">= 5.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": {
        "simulator": true
      },
      "android": {
        "buildType": "apk"
      }
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "simulator": false
      },
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "ios": {
        "simulator": false
      },
      "android": {
        "buildType": "app-bundle"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "your-apple-id@example.com",
        "ascAppId": "your-app-store-connect-app-id",
        "appleTeamId": "your-apple-team-id"
      },
      "android": {
        "serviceAccountKeyPath": "./google-service-account.json",
        "track": "internal"
      }
    }
  }
}
```

## 📱 Asset Requirements

### App Icon

**iOS:**
- **Size**: 1024x1024 pixels
- **Format**: PNG (no transparency)
- **Location**: `mobile/assets/icon.png`
- **Requirements**: 
  - No rounded corners (iOS adds them automatically)
  - No alpha channel
  - Square format

**Android:**
- **Size**: 1024x1024 pixels (foreground)
- **Format**: PNG (with transparency for adaptive icon)
- **Location**: `mobile/assets/adaptive-icon.png`
- **Background Color**: `#111827` (defined in `app.json`)

### Splash Screen

- **Size**: 2048x2048 pixels (will be scaled)
- **Format**: PNG
- **Location**: `mobile/assets/splash.png`
- **Background Color**: `#111827` (defined in `app.json`)

### Screenshots

**iOS App Store:**
- **iPhone 6.7" (iPhone 14 Pro Max, 15 Pro Max)**: 1290x2796 pixels
- **iPhone 6.5" (iPhone 11 Pro Max, XS Max)**: 1242x2688 pixels
- **iPhone 5.5" (iPhone 8 Plus)**: 1242x2208 pixels
- **iPad Pro 12.9"**: 2048x2732 pixels
- **Minimum**: 1 screenshot per device size
- **Recommended**: 3-5 screenshots per device size

**Google Play Store:**
- **Phone**: 1080x1920 pixels (minimum), up to 3840x2160
- **Tablet**: 1200x1920 pixels (minimum), up to 3840x2160
- **Minimum**: 2 screenshots
- **Recommended**: 4-8 screenshots

**Screenshot Content:**
- Dashboard with portfolio overview
- Trading screen with order placement
- Portfolio screen with multi-chain wallets
- Settings screen with preferences
- Bot management (if applicable)

### App Preview Video (Optional but Recommended)

**iOS:**
- **Duration**: 15-30 seconds
- **Resolution**: 1080p (1920x1080) or higher
- **Format**: MOV or MP4
- **Frame Rate**: 30fps

**Android:**
- **Duration**: 30 seconds (max)
- **Resolution**: 1080p minimum
- **Format**: MP4
- **Frame Rate**: 30fps

## 📝 Store Listing Requirements

### App Name

- **iOS**: Up to 30 characters
- **Android**: Up to 50 characters
- **Current**: "CryptoOrchestrator" (19 characters) ✅

### Subtitle (iOS) / Short Description (Android)

- **iOS**: Up to 30 characters
- **Android**: Up to 80 characters
- **Suggested**: "Automated Crypto Trading Platform"

### Description

**iOS**: Up to 4000 characters
**Android**: Up to 4000 characters

**Template**:
```
CryptoOrchestrator is a professional cryptocurrency trading automation platform that empowers traders to automate their strategies with AI-powered bots, advanced risk management, and comprehensive analytics.

Key Features:
• Automated Trading Bots - Create and deploy custom trading bots with advanced strategies
• Multi-Chain Wallet Support - Manage wallets across Ethereum, Base, Arbitrum, Polygon, and more
• DEX Trading - Execute swaps across multiple decentralized exchanges with best price routing
• Real-Time Portfolio Tracking - Monitor your portfolio performance with live updates
• Risk Management - Advanced risk controls including stop-loss, take-profit, and drawdown limits
• Push Notifications - Stay informed with real-time alerts for trades, bot status, and risk events
• Biometric Security - Secure your account with Face ID, Touch ID, or fingerprint authentication
• Offline Mode - Queue actions when offline and sync when connection is restored

Whether you're a beginner or experienced trader, CryptoOrchestrator provides the tools you need to automate and optimize your cryptocurrency trading strategy.

Privacy Policy: https://cryptoorchestrator.com/privacy
Terms of Service: https://cryptoorchestrator.com/terms
```

### Keywords (iOS)

- **Limit**: 100 characters total
- **Separator**: Comma
- **Suggested**: "crypto, trading, bitcoin, ethereum, bot, automation, defi, wallet, portfolio"

### Category

- **iOS**: Finance
- **Android**: Finance

### Age Rating

- **iOS**: 17+ (Financial Services)
- **Android**: Everyone (with financial services warning)

### Privacy Policy URL

- **Required**: Yes (both stores)
- **URL**: `https://cryptoorchestrator.com/privacy` or your domain
- **Content**: See `docs/PRIVACY_POLICY.md`

### Support URL

- **Required**: Yes (both stores)
- **URL**: `https://cryptoorchestrator.com/support` or your domain

### Marketing URL (Optional)

- **URL**: `https://cryptoorchestrator.com`

## 🔐 Certificates & Credentials

### iOS (App Store Connect)

1. **Create App in App Store Connect**:
   - Go to [appstoreconnect.apple.com](https://appstoreconnect.apple.com)
   - Click "My Apps" → "+" → "New App"
   - Fill in app information
   - Note your **App ID** (e.g., `1234567890`)

2. **EAS Handles Certificates Automatically**:
   - EAS Build automatically manages certificates and provisioning profiles
   - No manual certificate setup required
   - Certificates are stored securely in Expo's cloud

3. **Configure `eas.json`**:
   ```json
   {
     "submit": {
       "production": {
         "ios": {
           "appleId": "your-apple-id@example.com",
           "ascAppId": "1234567890",
           "appleTeamId": "ABCD123456"
         }
       }
     }
   }
   ```

### Android (Google Play Console)

1. **Create App in Google Play Console**:
   - Go to [play.google.com/console](https://play.google.com/console)
   - Click "Create app"
   - Fill in app information
   - Complete store listing

2. **Create Service Account** (for automated submission):
   - Go to Google Cloud Console
   - Create a service account
   - Download JSON key file
   - Grant "Play Console API" access
   - Save as `mobile/google-service-account.json` (add to `.gitignore`)

3. **Configure `eas.json`**:
   ```json
   {
     "submit": {
       "production": {
         "android": {
           "serviceAccountKeyPath": "./google-service-account.json",
           "track": "internal"
         }
       }
     }
   }
   ```

## 🏗️ Building for Production

### iOS Build

```bash
cd mobile
eas build --platform ios --profile production
```

This will:
1. Create a production build
2. Sign with your Apple Developer certificate
3. Upload to EAS servers
4. Provide download link when complete

**Build Time**: ~15-30 minutes

### Android Build

```bash
cd mobile
eas build --platform android --profile production
```

This will:
1. Create an App Bundle (AAB) for Play Store
2. Sign with your keystore (managed by EAS)
3. Upload to EAS servers
4. Provide download link when complete

**Build Time**: ~10-20 minutes

### Build Both Platforms

```bash
cd mobile
eas build --platform all --profile production
```

## 📤 Submission Process

### iOS (App Store)

#### Option 1: Automated Submission (Recommended)

```bash
cd mobile
eas submit --platform ios --profile production
```

This will:
1. Use the build from `eas build`
2. Upload to App Store Connect
3. Create a new version (if needed)
4. Submit for review

#### Option 2: Manual Submission

1. **Download Build**:
   - Get the `.ipa` file from EAS build output
   - Or download from [expo.dev](https://expo.dev)

2. **Upload via Transporter**:
   - Install [Transporter](https://apps.apple.com/app/transporter/id1450874784) (macOS)
   - Open Transporter
   - Drag `.ipa` file
   - Click "Deliver"

3. **Submit in App Store Connect**:
   - Go to App Store Connect
   - Select your app
   - Go to "App Store" tab
   - Click "+ Version"
   - Fill in version information
   - Upload screenshots and metadata
   - Click "Submit for Review"

### Android (Play Store)

#### Option 1: Automated Submission (Recommended)

```bash
cd mobile
eas submit --platform android --profile production
```

This will:
1. Use the build from `eas build`
   - Upload to Google Play Console
   - Create a new release (if needed)
   - Submit for review

#### Option 2: Manual Submission

1. **Download Build**:
   - Get the `.aab` file from EAS build output
   - Or download from [expo.dev](https://expo.dev)

2. **Upload to Play Console**:
   - Go to Google Play Console
   - Select your app
   - Go to "Production" → "Create new release"
   - Upload `.aab` file
   - Fill in release notes
   - Review and roll out

## ✅ Pre-Submission Checklist

### iOS App Store

- [ ] Apple Developer account active ($99/year)
- [ ] App created in App Store Connect
- [ ] App icon (1024x1024 PNG)
- [ ] Screenshots for all required device sizes
- [ ] App description (up to 4000 characters)
- [ ] Keywords (up to 100 characters)
- [ ] Privacy Policy URL (required)
- [ ] Support URL (required)
- [ ] Age rating configured (17+)
- [ ] Category selected (Finance)
- [ ] Version and build number set
- [ ] Production build created with EAS
- [ ] Build tested on physical device
- [ ] All features working correctly
- [ ] No crashes or critical bugs
- [ ] Compliance with App Store Review Guidelines

### Google Play Store

- [ ] Google Play Developer account active ($25 one-time)
- [ ] App created in Play Console
- [ ] App icon (1024x1024 PNG)
- [ ] Adaptive icon (1024x1024 PNG with transparency)
- [ ] Screenshots (minimum 2, recommended 4-8)
- [ ] Feature graphic (1024x500 PNG)
- [ ] Short description (up to 80 characters)
- [ ] Full description (up to 4000 characters)
- [ ] Privacy Policy URL (required)
- [ ] Support URL (required)
- [ ] Age rating configured
- [ ] Category selected (Finance)
- [ ] Content rating completed
- [ ] Version code and version name set
- [ ] Production build created (AAB format)
- [ ] Build tested on physical device
- [ ] All features working correctly
- [ ] No crashes or critical bugs
- [ ] Compliance with Play Store policies

## 🚨 App Store Review Guidelines

### iOS App Store

**Key Requirements:**
- **2.1 App Completeness**: App must be fully functional
- **2.3 Accurate Metadata**: App name, description, screenshots must be accurate
- **3.1.1 In-App Purchase**: If using subscriptions, must use Apple's IAP
- **4.0 Design**: App must follow Apple's Human Interface Guidelines
- **5.1.1 Privacy**: Must have privacy policy and handle user data responsibly
- **5.2.1 Intellectual Property**: Must not infringe on trademarks or copyrights

**Financial Services Specific:**
- Must comply with financial regulations
- Must clearly disclose risks
- Must have proper licensing (if required)
- Must handle user funds securely

### Google Play Store

**Key Requirements:**
- **Financial Services**: Must comply with financial regulations
- **User Data**: Must handle user data securely and transparently
- **Content Rating**: Must accurately rate app content
- **Permissions**: Must request only necessary permissions
- **Malware**: Must not contain malware or harmful code

**Financial Services Specific:**
- Must comply with financial regulations
- Must clearly disclose risks
- Must have proper licensing (if required)
- Must handle user funds securely

## 📊 Post-Submission

### Monitoring

1. **App Store Connect** (iOS):
   - Check submission status
   - Respond to review feedback
   - Monitor crash reports
   - Track download statistics

2. **Google Play Console** (Android):
   - Check release status
   - Respond to review feedback
   - Monitor crash reports
   - Track download statistics

### Review Timeline

- **iOS**: Typically 24-48 hours (can take up to 7 days)
- **Android**: Typically 1-3 days (can take up to 7 days)

### Common Rejection Reasons

**iOS:**
- App crashes or freezes
- Missing or inaccurate metadata
- Privacy policy issues
- Incomplete functionality
- Guideline violations

**Android:**
- App crashes or freezes
- Missing or inaccurate metadata
- Privacy policy issues
- Permission misuse
- Policy violations

## 🔄 Updates and Releases

### Version Updates

1. **Update Version Numbers**:
   ```json
   // app.json
   {
     "expo": {
       "version": "1.0.1",  // User-facing version
       "ios": {
         "buildNumber": "2"  // Increment for each build
       },
       "android": {
         "versionCode": 2  // Increment for each build
       }
     }
   }
   ```

2. **Create New Build**:
   ```bash
   eas build --platform all --profile production
   ```

3. **Submit Update**:
   ```bash
   eas submit --platform all --profile production
   ```

### Release Notes

**iOS**: Up to 4000 characters
**Android**: Up to 500 characters

**Template**:
```
Version 1.0.1

Bug Fixes:
• Fixed crash when viewing portfolio
• Improved notification delivery reliability
• Fixed biometric authentication on some devices

Improvements:
• Enhanced trading screen performance
• Improved offline mode synchronization
• Updated UI for better accessibility
```

## 🛠️ Troubleshooting

### Build Failures

**iOS:**
- Check Apple Developer account status
- Verify bundle identifier is unique
- Ensure certificates are valid
- Check EAS build logs for errors

**Android:**
- Check package name is unique
- Verify keystore is configured
- Check EAS build logs for errors

### Submission Failures

**iOS:**
- Verify App Store Connect credentials
- Check app status in App Store Connect
- Ensure build is for correct platform (not simulator)

**Android:**
- Verify service account has correct permissions
- Check Play Console app status
- Ensure build is AAB format (not APK)

### Review Rejections

1. **Read Review Feedback**: Carefully review rejection reasons
2. **Fix Issues**: Address all mentioned problems
3. **Resubmit**: Create new build and resubmit
4. **Appeal** (if needed): Use App Store Connect or Play Console appeal process

## 📚 Additional Resources

- [Expo EAS Build Documentation](https://docs.expo.dev/build/introduction/)
- [Expo EAS Submit Documentation](https://docs.expo.dev/submit/introduction/)
- [Apple App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Google Play Store Policies](https://play.google.com/about/developer-content-policy/)
- [App Store Connect Help](https://help.apple.com/app-store-connect/)
- [Google Play Console Help](https://support.google.com/googleplay/android-developer)

## ✅ Submission Checklist Summary

### Before Building
- [ ] EAS project initialized (`eas init`)
- [ ] `app.json` configured with all required fields
- [ ] `eas.json` configured with build and submit profiles
- [ ] App icons created (iOS 1024x1024, Android adaptive)
- [ ] Splash screen created
- [ ] Privacy policy URL available
- [ ] Support URL available

### Before Submitting
- [ ] Production builds created for both platforms
- [ ] Builds tested on physical devices
- [ ] All features working correctly
- [ ] Screenshots captured for all required sizes
- [ ] App description written
- [ ] Keywords selected (iOS)
- [ ] Store listings completed
- [ ] Age rating configured
- [ ] Category selected

### Submission
- [ ] iOS app submitted to App Store Connect
- [ ] Android app submitted to Google Play Console
- [ ] Submission status monitored
- [ ] Review feedback addressed (if any)

---

**Ready to submit! Follow this guide step-by-step to get your app published on both stores.** 🚀

