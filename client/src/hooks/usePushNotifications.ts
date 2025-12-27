/**
 * Push Notifications Hook
 * Manages push notification subscription and display.
 */

import { useState, useEffect, useCallback } from 'react';

interface PushSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

interface NotificationPermissionState {
  permission: 'default' | 'granted' | 'denied' | 'unsupported';
  canRequest: boolean;
}

export function usePushNotifications() {
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const [permission, setPermission] = useState<NotificationPermissionState>({
    permission: 'default',
    canRequest: false,
  });

  useEffect(() => {
    // Check if notifications are supported
    if (!('Notification' in window)) {
      setPermission({ permission: 'unsupported', canRequest: false });
      return;
    }

    // Check current permission
    const currentPermission = Notification.permission;
    setPermission({
      permission: currentPermission,
      canRequest: currentPermission === 'default',
    });

    // Check for existing subscription
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then((registration) => {
        registration.pushManager
          .getSubscription()
          .then((sub) => {
            if (sub) {
              setSubscription({
                endpoint: sub.endpoint,
                keys: {
                  p256dh: arrayBufferToBase64(sub.getKey('p256dh')!),
                  auth: arrayBufferToBase64(sub.getKey('auth')!),
                },
              });
            }
          })
          .catch(console.error);
      });
    }
  }, []);

  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (!('Notification' in window)) {
      return false;
    }

    const result = await Notification.requestPermission();
    setPermission({
      permission: result,
      canRequest: result === 'default',
    });

    return result === 'granted';
  }, []);

  const subscribe = useCallback(async (): Promise<PushSubscription | null> => {
    if (!('serviceWorker' in navigator)) {
      console.error('Service workers not supported');
      return null;
    }

    // Request permission first
    const hasPermission = await requestPermission();
    if (!hasPermission) {
      console.error('Notification permission denied');
      return null;
    }

    try {
      const registration = await navigator.serviceWorker.ready;

      // Get VAPID public key from server (should be in env or config)
      const vapidPublicKey = import.meta.env.VITE_VAPID_PUBLIC_KEY;

      if (!vapidPublicKey) {
        console.error('VAPID public key not configured');
        return null;
      }

      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey) as BufferSource,
      });

      const pushSubscription: PushSubscription = {
        endpoint: subscription.endpoint,
        keys: {
          p256dh: arrayBufferToBase64(subscription.getKey('p256dh')!),
          auth: arrayBufferToBase64(subscription.getKey('auth')!),
        },
      };

      // Send subscription to server
      try {
        const token = localStorage.getItem('token');
        await fetch('/api/notifications/subscribe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify(pushSubscription),
        });
      } catch (error) {
        console.error('Failed to send subscription to server:', error);
      }

      setSubscription(pushSubscription);
      return pushSubscription;
    } catch (error) {
      console.error('Error subscribing to push notifications:', error);
      return null;
    }
  }, [requestPermission]);

  const unsubscribe = useCallback(async (): Promise<boolean> => {
    if (!('serviceWorker' in navigator)) {
      return false;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        await subscription.unsubscribe();

        // Notify server
        try {
          const token = localStorage.getItem('token');
          await fetch('/api/notifications/unsubscribe', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(token && { Authorization: `Bearer ${token}` }),
            },
            body: JSON.stringify({ endpoint: subscription.endpoint }),
          });
        } catch (error) {
          console.error('Failed to notify server of unsubscribe:', error);
        }

        setSubscription(null);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Error unsubscribing from push notifications:', error);
      return false;
    }
  }, []);

  return {
    subscription,
    permission,
    subscribe,
    unsubscribe,
    requestPermission,
  };
}

// Helper functions
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    const byte = bytes[i];
    if (byte !== undefined) {
      binary += String.fromCharCode(byte);
    }
  }
  return btoa(binary);
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}
