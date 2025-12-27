# Mobile Push Notifications Guide

This guide details the complete push notification implementation for the CryptoOrchestrator mobile app, including setup, configuration, testing, and troubleshooting.

## 🚀 Overview

The mobile app uses **Expo Push Notifications** to deliver real-time notifications for:
- **Trade Events**: Trade executions, order fills, stop loss/take profit triggers
- **Bot Events**: Bot started/stopped, bot status changes
- **Risk Alerts**: Risk limit breaches, portfolio alerts
- **Price Alerts**: Price target reached notifications
- **System Alerts**: System maintenance, security alerts

## 🏗️ Architecture

### Components

1. **Mobile App (`mobile/src/`)**
   - `services/PushNotificationService.ts` - Client-side push notification service
   - `App.tsx` - Notification initialization and handling
   - `services/api.ts` - API client for subscription management

2. **Backend (`server_fastapi/`)**
   - `services/expo_push_service.py` - Expo Push API integration
   - `services/notification_service.py` - Notification orchestration
   - `routes/notifications.py` - Subscription/unsubscription endpoints
   - `repositories/push_subscription_repository.py` - Database persistence
   - `models/push_subscription.py` - Subscription model

### Flow

```
1. Mobile App → Request Permissions → Get Expo Push Token
2. Mobile App → POST /api/notifications/subscribe → Backend
3. Backend → Store Subscription → Database
4. Backend Event → NotificationService.send_notification()
5. NotificationService → Get Active Subscriptions → Filter by Type
6. NotificationService → ExpoPushService.send_push_notification()
7. Expo Push API → Deliver to Device
8. Mobile App → Receive Notification → Handle Navigation
```

## 📋 Prerequisites

### Mobile App

- **Expo SDK**: v54.0+ (configured in `mobile/app.json`)
- **expo-notifications**: v0.28.0+ (installed in `mobile/package.json`)
- **expo-device**: v6.0.2+ (for device detection)
- **Physical Device**: Push notifications only work on physical devices (not simulators)

### Backend

- **httpx**: v0.25.2+ (for Expo Push API requests)
- **PostgreSQL**: For storing push subscriptions
- **Environment Variables**: None required (Expo Push API is public)

### iOS Requirements

- **Xcode**: 14.0+ (for iOS builds)
- **Apple Developer Account**: For APNs certificates (production)
- **Push Notification Capability**: Enabled in Xcode project

### Android Requirements

- **Google Play Services**: For FCM (handled by Expo)
- **Firebase Project**: Configured via Expo (for production)

## 🔧 Configuration

### Mobile App (`mobile/app.json`)

The app is already configured with:

```json
{
  "expo": {
    "plugins": [
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#111827",
          "sounds": ["./assets/notification-sound.wav"]
        }
      ]
    ],
    "ios": {
      "infoPlist": {
        "UIBackgroundModes": ["fetch", "remote-notification"]
      }
    }
  }
}
```

### Backend Environment Variables

No special environment variables are required. The Expo Push API is public and doesn't require authentication.

### Expo Project ID (Optional)

If using Expo's managed workflow, set `EXPO_PROJECT_ID` in your mobile app's environment:

```bash
# mobile/.env
EXPO_PROJECT_ID=your-expo-project-id
```

This is optional - Expo can generate tokens without it.

## ▶️ Setup Instructions

### 1. Initialize Native Projects

Before testing push notifications, ensure native projects are initialized:

```bash
cd mobile
npm run init:native
```

### 2. Build and Run on Physical Device

**iOS:**
```bash
npm run run:ios
# Or use Xcode to build and run on a physical device
```

**Android:**
```bash
npm run run:android
# Or use Android Studio to build and run on a physical device
```

**Note**: Push notifications **do not work** in simulators/emulators. You must use a physical device.

### 3. Verify Permissions

On first launch, the app will:
1. Request notification permissions
2. Register for push notifications
3. Get an Expo push token
4. Subscribe to the backend

Check the console logs to verify:
- `Successfully subscribed to push notifications` ✅

## 🧪 Testing

### Test from Backend

You can test push notifications by calling the notification service from the backend:

```python
from server_fastapi.services.notification_service import NotificationService, NotificationType, NotificationPriority
from server_fastapi.database import get_db_session

async def test_push_notification():
    async with get_db_session() as db:
        service = NotificationService(db)
        await service.send_notification(
            user_id=1,  # Your user ID
            notification_type=NotificationType.TRADE_EXECUTED,
            title="Test Trade",
            message="This is a test notification",
            priority=NotificationPriority.HIGH,
            data={"trade_id": 123, "type": "trade_executed"}
        )
```

### Test via API

You can also trigger a test notification via the API (if you have a test endpoint):

```bash
curl -X POST http://localhost:8000/api/notifications/test \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Notification",
    "body": "This is a test",
    "type": "system_alert"
  }'
```

### Test Notification Types

The app handles different notification types with appropriate navigation:

- **`trade_executed`** → Navigates to Trading screen
- **`bot_started`** / **`bot_stopped`** → Navigates to Dashboard
- **`risk_alert`** / **`portfolio_alert`** → Navigates to Portfolio screen
- **`price_alert`** → Navigates to Trading screen
- **`system_alert`** → Navigates to Dashboard (default)

### Test Deep Linking

When a notification is tapped:
1. App opens (if closed) or comes to foreground
2. `handleNotificationNavigation()` is called
3. App navigates to the appropriate screen based on notification data

Test by:
1. Sending a notification while app is in background
2. Tapping the notification
3. Verifying the app navigates to the correct screen

## 📱 Notification Handling

### Foreground Notifications

When the app is in the foreground, notifications are displayed as:
- **Alert Dialog**: Shows notification title and body
- **Actions**: "View" (navigates) or "Dismiss"

### Background Notifications

When the app is in the background:
- Notification appears in the system notification tray
- Tapping the notification opens the app and navigates to the appropriate screen

### Notification Data Structure

Notifications include the following data:

```typescript
{
  notification_id: string;
  type: 'trade_executed' | 'bot_started' | 'risk_alert' | ...;
  priority: 'low' | 'medium' | 'high' | 'critical';
  trade_id?: number;  // For trade notifications
  bot_id?: string;    // For bot notifications
  // ... other type-specific data
}
```

## 🔍 Troubleshooting

### Notifications Not Received

1. **Check Device**: Ensure you're testing on a physical device (not simulator/emulator)
2. **Check Permissions**: Verify notification permissions are granted in device settings
3. **Check Subscription**: Verify the subscription was successful in backend logs
4. **Check Token**: Verify the Expo push token is valid (starts with `ExponentPushToken[`)
5. **Check Backend Logs**: Look for errors in `server_fastapi/services/expo_push_service.py`

### Subscription Failed

1. **Check Authentication**: Ensure user is authenticated when subscribing
2. **Check API Endpoint**: Verify `/api/notifications/subscribe` is accessible
3. **Check Network**: Ensure mobile app can reach the backend API
4. **Check Backend Logs**: Look for errors in `server_fastapi/routes/notifications.py`

### Navigation Not Working

1. **Check Navigation Ref**: Ensure `navigationRef` is properly initialized in `App.tsx`
2. **Check Notification Data**: Verify notification data includes `type` field
3. **Check Console Logs**: Look for navigation errors in React Native debugger

### Expo Push Token Invalid

1. **Check Token Format**: Should start with `ExponentPushToken[`
2. **Check Expo Project**: Ensure Expo project is properly configured
3. **Re-register**: Try unsubscribing and re-subscribing

## 📊 Monitoring

### Backend Monitoring

Check subscription status:

```bash
curl -X GET http://localhost:8000/api/notifications/subscriptions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

This returns:
- All subscriptions for the authenticated user
- Subscription status (active/inactive)
- Last notification sent timestamp
- Error count (if any)

### Mobile App Monitoring

Check subscription status in the app:
- Go to **Settings** → **Notifications**
- Verify "Push Notifications" toggle is enabled
- Check subscription status

## 🚀 Production Deployment

### iOS Production

1. **Configure APNs**: Set up Apple Push Notification service certificates in Apple Developer Portal
2. **Update app.json**: Ensure `ios.bundleIdentifier` matches your App Store app
3. **Build with EAS**: Use `eas build --platform ios` for production builds
4. **Test on TestFlight**: Test push notifications on TestFlight before App Store release

### Android Production

1. **Configure FCM**: Expo handles FCM configuration automatically
2. **Update app.json**: Ensure `android.package` matches your Play Store app
3. **Build with EAS**: Use `eas build --platform android` for production builds
4. **Test on Internal Testing**: Test push notifications on Play Store Internal Testing track

### Backend Production

1. **Database Migrations**: Ensure `push_subscriptions` table exists
2. **Environment Variables**: No special configuration needed
3. **Monitoring**: Set up logging and monitoring for push notification failures
4. **Rate Limiting**: Consider rate limiting push notification endpoints

## ✅ Checklist

- [x] Native projects initialized (`npm run init:native`)
- [x] Push notification service implemented
- [x] Backend Expo push service implemented
- [x] Subscription/unsubscription endpoints working
- [x] Notification handling with deep linking
- [x] Foreground notification alerts
- [x] Background notification navigation
- [ ] Tested on physical iOS device
- [ ] Tested on physical Android device
- [ ] Production APNs certificates configured (iOS)
- [ ] Production FCM configured (Android, via Expo)

## 📚 Additional Resources

- [Expo Push Notifications Documentation](https://docs.expo.dev/push-notifications/overview/)
- [Expo Push Notification API](https://docs.expo.dev/push-notifications/sending-notifications/)
- [React Navigation Deep Linking](https://reactnavigation.org/docs/deep-linking/)

## 🔗 Related Files

- `mobile/src/services/PushNotificationService.ts` - Client service
- `mobile/src/App.tsx` - Notification initialization and handling
- `server_fastapi/services/expo_push_service.py` - Backend Expo service
- `server_fastapi/services/notification_service.py` - Notification orchestration
- `server_fastapi/routes/notifications.py` - API endpoints
- `server_fastapi/models/push_subscription.py` - Database model

