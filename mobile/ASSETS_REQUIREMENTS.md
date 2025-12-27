# Mobile App Assets Requirements

This document lists all required assets for App Store and Play Store submission.

## 📱 Required Assets

### App Icons

#### iOS App Icon
- **File**: `mobile/assets/icon.png`
- **Size**: 1024x1024 pixels
- **Format**: PNG (no transparency, no alpha channel)
- **Requirements**:
  - Square format
  - No rounded corners (iOS adds them automatically)
  - No text or borders
  - High quality, professional design
  - Represents the app clearly

#### Android Adaptive Icon
- **File**: `mobile/assets/adaptive-icon.png`
- **Size**: 1024x1024 pixels (foreground)
- **Format**: PNG (with transparency)
- **Background Color**: `#111827` (defined in `app.json`)
- **Requirements**:
  - Foreground image with transparency
  - Safe zone: Keep important content within 512x512 center area
  - Background color will be applied automatically

### Splash Screen

- **File**: `mobile/assets/splash.png`
- **Size**: 2048x2048 pixels (will be scaled)
- **Format**: PNG
- **Background Color**: `#111827` (defined in `app.json`)
- **Requirements**:
  - App logo centered
  - Professional design
  - Matches app branding

### Notification Icon (Android)

- **File**: `mobile/assets/notification-icon.png`
- **Size**: 96x96 pixels (recommended)
- **Format**: PNG (with transparency)
- **Color**: `#111827` (defined in `app.json`)
- **Requirements**:
  - Simple, recognizable icon
  - Works in monochrome
  - Clear at small sizes

### Notification Sound (Optional)

- **File**: `mobile/assets/notification-sound.wav`
- **Format**: WAV
- **Duration**: 1-3 seconds
- **Requirements**:
  - Professional sound
  - Not too loud or jarring
  - Matches app tone

## 📸 Screenshots

### iOS App Store Screenshots

#### Required Device Sizes

1. **iPhone 6.7" Display** (iPhone 14 Pro Max, 15 Pro Max)
   - **Size**: 1290x2796 pixels
   - **Required**: Yes
   - **Recommended**: 3-5 screenshots

2. **iPhone 6.5" Display** (iPhone 11 Pro Max, XS Max)
   - **Size**: 1242x2688 pixels
   - **Required**: Yes (if supporting older devices)
   - **Recommended**: 3-5 screenshots

3. **iPhone 5.5" Display** (iPhone 8 Plus)
   - **Size**: 1242x2208 pixels
   - **Required**: No (optional for older devices)
   - **Recommended**: 3-5 screenshots

4. **iPad Pro 12.9"** (if supporting iPad)
   - **Size**: 2048x2732 pixels
   - **Required**: Yes (if `supportsTablet: true`)
   - **Recommended**: 3-5 screenshots

#### Screenshot Content Suggestions

1. **Dashboard Screen**
   - Portfolio overview
   - Performance charts
   - Recent trades

2. **Trading Screen**
   - Order placement interface
   - DEX swap interface
   - Price charts

3. **Portfolio Screen**
   - Multi-chain wallet display
   - Token balances
   - Trading statistics

4. **Settings Screen**
   - Preferences
   - Security settings
   - Notification settings

5. **Bot Management** (if applicable)
   - Bot list
   - Bot configuration
   - Bot status

### Google Play Store Screenshots

#### Phone Screenshots
- **Size**: 1080x1920 pixels (minimum)
- **Maximum**: 3840x2160 pixels
- **Required**: Minimum 2
- **Recommended**: 4-8 screenshots
- **Format**: PNG or JPEG

#### Tablet Screenshots (Optional)
- **Size**: 1200x1920 pixels (minimum)
- **Maximum**: 3840x2160 pixels
- **Required**: No (but recommended)
- **Recommended**: 4-8 screenshots

#### Feature Graphic
- **File**: `mobile/assets/feature-graphic.png`
- **Size**: 1024x500 pixels
- **Format**: PNG or JPEG
- **Required**: Yes
- **Purpose**: Banner image displayed at top of Play Store listing

#### Screenshot Content
- Same as iOS suggestions above
- Ensure screenshots showcase key features
- Use realistic data (not test data)
- Highlight unique features

## 🎬 App Preview Video (Optional but Recommended)

### iOS App Preview
- **Duration**: 15-30 seconds
- **Resolution**: 1080p (1920x1080) or higher
- **Format**: MOV or MP4
- **Frame Rate**: 30fps
- **Content**: Showcase key features and user experience

### Android Promo Video
- **Duration**: Up to 30 seconds
- **Resolution**: 1080p minimum
- **Format**: MP4
- **Frame Rate**: 30fps
- **Content**: Showcase key features and user experience

## 📝 Asset Creation Guidelines

### Design Principles

1. **Consistency**: All assets should match app branding
2. **Quality**: Use high-resolution images, avoid pixelation
3. **Clarity**: Icons and images should be clear and recognizable
4. **Professional**: Maintain professional appearance
5. **Accessibility**: Ensure good contrast and readability

### Tools

**Icon Design:**
- Figma, Sketch, Adobe Illustrator
- Online: Canva, IconGenerator

**Screenshot Capture:**
- iOS: Xcode Simulator, iOS Device
- Android: Android Studio Emulator, Android Device
- Tools: Fastlane, App Store Connect, Play Console

**Image Editing:**
- Photoshop, GIMP, Figma
- Online: Canva, Photopea

**Optimization:**
- TinyPNG, ImageOptim, Squoosh

## 📂 Asset Directory Structure

```
mobile/
├── assets/
│   ├── icon.png                    # iOS app icon (1024x1024)
│   ├── adaptive-icon.png           # Android adaptive icon (1024x1024)
│   ├── splash.png                  # Splash screen (2048x2048)
│   ├── notification-icon.png       # Android notification icon (96x96)
│   ├── notification-sound.wav     # Notification sound (optional)
│   ├── feature-graphic.png         # Play Store feature graphic (1024x500)
│   └── screenshots/
│       ├── ios/
│       │   ├── iphone-6.7/
│       │   │   ├── screenshot-1.png
│       │   │   ├── screenshot-2.png
│       │   │   └── screenshot-3.png
│       │   ├── iphone-6.5/
│       │   │   └── ...
│       │   └── ipad-12.9/
│       │       └── ...
│       └── android/
│           ├── phone/
│           │   ├── screenshot-1.png
│           │   ├── screenshot-2.png
│           │   └── ...
│           └── tablet/
│               └── ...
```

## ✅ Asset Checklist

### Required for Submission
- [ ] iOS app icon (1024x1024 PNG)
- [ ] Android adaptive icon (1024x1024 PNG)
- [ ] Splash screen (2048x2048 PNG)
- [ ] iOS screenshots (minimum 1 per device size)
- [ ] Android screenshots (minimum 2)
- [ ] Android feature graphic (1024x500 PNG)
- [ ] Privacy policy URL
- [ ] Support URL

### Optional but Recommended
- [ ] Android notification icon (96x96 PNG)
- [ ] Notification sound (WAV)
- [ ] App preview video (iOS)
- [ ] Promo video (Android)
- [ ] Additional screenshots (more than minimum)

## 🚀 Quick Start

1. **Create Assets Directory**:
   ```bash
   mkdir -p mobile/assets/screenshots/{ios,android}
   ```

2. **Generate Icons**:
   - Use design tool to create 1024x1024 icon
   - Export as PNG (no transparency for iOS)
   - Save as `mobile/assets/icon.png`

3. **Create Adaptive Icon**:
   - Use same design but with transparency
   - Save as `mobile/assets/adaptive-icon.png`

4. **Create Splash Screen**:
   - Design splash screen with app logo
   - Export as 2048x2048 PNG
   - Save as `mobile/assets/splash.png`

5. **Capture Screenshots**:
   - Run app on device/simulator
   - Navigate to each key screen
   - Capture screenshots at required sizes
   - Save in appropriate directories

6. **Optimize Assets**:
   - Compress images (TinyPNG, ImageOptim)
   - Ensure file sizes are reasonable
   - Verify quality is maintained

## 📚 Resources

- [Apple App Icon Guidelines](https://developer.apple.com/design/human-interface-guidelines/app-icons)
- [Android Adaptive Icons](https://developer.android.com/guide/practices/ui_guidelines/icon_design_adaptive)
- [App Store Screenshot Guidelines](https://developer.apple.com/app-store/product-page/)
- [Play Store Asset Guidelines](https://support.google.com/googleplay/android-developer/answer/9866151)

---

**Create all required assets before starting the submission process!** 🎨

