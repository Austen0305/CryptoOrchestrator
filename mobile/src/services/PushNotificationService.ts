/**
 * Push Notification Service for Mobile App
 * Handles push notification registration, subscription, and display
 */

import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import { Platform } from "react-native";
import { api } from "./api";
import AsyncStorage from "@react-native-async-storage/async-storage";

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export interface PushNotificationToken {
  token: string;
  endpoint?: string;
  keys?: {
    p256dh: string;
    auth: string;
  };
}

export interface NotificationData {
  type: "trade" | "bot" | "risk" | "system" | "price_alert";
  title: string;
  body: string;
  data?: Record<string, unknown>;
}

class PushNotificationService {
  private token: string | null = null;
  private isSubscribed: boolean = false;

  /**
   * Request notification permissions
   */
  async requestPermissions(): Promise<boolean> {
    try {
      if (!Device.isDevice) {
        console.warn("Push notifications only work on physical devices");
        return false;
      }

      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== "granted") {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== "granted") {
        console.warn("Failed to get push notification permissions");
        return false;
      }

      return true;
    } catch (error) {
      console.error("Error requesting notification permissions:", error);
      return false;
    }
  }

  /**
   * Register for push notifications and get token
   */
  async registerForPushNotifications(): Promise<string | null> {
    try {
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) {
        return null;
      }

      // Get push token
      // For Expo, projectId is optional if using Expo's managed service
      const tokenData = await Notifications.getExpoPushTokenAsync(
        process.env.EXPO_PROJECT_ID ? { projectId: process.env.EXPO_PROJECT_ID } : undefined
      );

      this.token = tokenData.data;

      // Store token locally
      await AsyncStorage.setItem("push_notification_token", this.token);

      return this.token;
    } catch (error) {
      console.error("Error registering for push notifications:", error);
      return null;
    }
  }

  /**
   * Subscribe to push notifications on backend
   */
  async subscribe(): Promise<boolean> {
    try {
      if (!this.token) {
        const token = await this.registerForPushNotifications();
        if (!token) {
          return false;
        }
      }

      // For Expo, we send the Expo push token directly
      // The backend will handle Expo push notifications
      let platform: string;
      if (Platform.OS === "ios") {
        platform = "ios";
      } else if (Platform.OS === "android") {
        platform = "android";
      } else {
        platform = "unknown";
      }

      await api.post("notifications/subscribe", {
        expo_push_token: this.token,
        platform: platform,
        device_id: await this._getDeviceId(),
        app_version: await this._getAppVersion(),
      });

      this.isSubscribed = true;
      await AsyncStorage.setItem("push_notification_subscribed", "true");

      return true;
    } catch (error) {
      console.error("Error subscribing to push notifications:", error);
      return false;
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async unsubscribe(): Promise<boolean> {
    try {
      if (!this.token) {
        const storedToken = await AsyncStorage.getItem("push_notification_token");
        if (storedToken) {
          this.token = storedToken;
        }
      }

      if (this.token) {
        await api.post("notifications/unsubscribe", {
          expo_push_token: this.token,
        });
      }

      this.isSubscribed = false;
      await AsyncStorage.removeItem("push_notification_subscribed");
      await AsyncStorage.removeItem("push_notification_token");

      return true;
    } catch (error) {
      console.error("Error unsubscribing from push notifications:", error);
      return false;
    }
  }

  /**
   * Check if subscribed to push notifications
   */
  async isSubscribedToPushNotifications(): Promise<boolean> {
    try {
      const subscribed = await AsyncStorage.getItem("push_notification_subscribed");
      return subscribed === "true" && this.isSubscribed;
    } catch {
      return false;
    }
  }

  /**
   * Get device ID for tracking
   */
  private async _getDeviceId(): Promise<string | null> {
    try {
      // Use AsyncStorage to store a device ID
      let deviceId = await AsyncStorage.getItem("device_id");
      if (!deviceId) {
        // Generate a simple device ID (in production, use a proper UUID library)
        deviceId = `device_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
        await AsyncStorage.setItem("device_id", deviceId);
      }
      return deviceId;
    } catch (error) {
      console.error("Error getting device ID:", error);
      return null;
    }
  }

  /**
   * Get app version
   */
  private async _getAppVersion(): Promise<string | null> {
    try {
      const Constants = await import("expo-constants");
      return Constants.default.expoConfig?.version ?? null;
    } catch (error) {
      console.error("Error getting app version:", error);
      return null;
    }
  }

  /**
   * Get stored push notification token
   */
  async getToken(): Promise<string | null> {
    try {
      if (this.token) {
        return this.token;
      }

      const storedToken = await AsyncStorage.getItem("push_notification_token");
      if (storedToken) {
        this.token = storedToken;
        return this.token;
      }

      // Try to register if no token exists
      return await this.registerForPushNotifications();
    } catch (error) {
      console.error("Error getting push notification token:", error);
      return null;
    }
  }

  /**
   * Schedule a local notification
   */
  async scheduleLocalNotification(
    title: string,
    body: string,
    data?: Record<string, unknown>,
    trigger?: Notifications.NotificationTriggerInput
  ): Promise<string> {
    try {
      const identifier = await Notifications.scheduleNotificationAsync({
        content: {
          title,
          body,
          data,
          sound: true,
          priority: Notifications.AndroidNotificationPriority.HIGH,
        },
        trigger: trigger ?? null, // null = immediate
      });

      return identifier;
    } catch (error) {
      console.error("Error scheduling local notification:", error);
      throw error;
    }
  }

  /**
   * Cancel a scheduled notification
   */
  async cancelNotification(identifier: string): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(identifier);
    } catch (error) {
      console.error("Error canceling notification:", error);
    }
  }

  /**
   * Cancel all scheduled notifications
   */
  async cancelAllNotifications(): Promise<void> {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync();
    } catch (error) {
      console.error("Error canceling all notifications:", error);
    }
  }

  /**
   * Get all scheduled notifications
   */
  async getScheduledNotifications(): Promise<Notifications.NotificationRequest[]> {
    try {
      return await Notifications.getAllScheduledNotificationsAsync();
    } catch (error) {
      console.error("Error getting scheduled notifications:", error);
      return [];
    }
  }

  /**
   * Set notification badge count
   */
  async setBadgeCount(count: number): Promise<void> {
    try {
      await Notifications.setBadgeCountAsync(count);
    } catch (error) {
      console.error("Error setting badge count:", error);
    }
  }

  /**
   * Clear notification badge
   */
  async clearBadge(): Promise<void> {
    try {
      await Notifications.setBadgeCountAsync(0);
    } catch (error) {
      console.error("Error clearing badge:", error);
    }
  }
}

// Notification categories for actionable notifications
export const NotificationCategories = {
  TRADE: "TRADE",
  BOT: "BOT",
  RISK: "RISK",
  SYSTEM: "SYSTEM",
};

// Create notification categories
Notifications.setNotificationCategoryAsync(NotificationCategories.TRADE, [
  {
    identifier: "VIEW_TRADE",
    buttonTitle: "View Trade",
    options: { opensAppToForeground: true },
  },
  {
    identifier: "DISMISS",
    buttonTitle: "Dismiss",
    options: { isDestructive: true },
  },
]);

Notifications.setNotificationCategoryAsync(NotificationCategories.BOT, [
  {
    identifier: "VIEW_BOT",
    buttonTitle: "View Bot",
    options: { opensAppToForeground: true },
  },
  {
    identifier: "DISMISS",
    buttonTitle: "Dismiss",
    options: { isDestructive: true },
  },
]);

export const pushNotificationService = new PushNotificationService();
export default pushNotificationService;
