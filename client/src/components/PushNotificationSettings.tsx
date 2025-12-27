/**
 * Push Notification Settings Component
 * Allows users to enable/disable push notifications.
 */

import { useState, useEffect } from 'react';
import { usePushNotifications } from '@/hooks/usePushNotifications';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Bell, BellOff, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

export function PushNotificationSettings() {
  const { subscription, permission, subscribe, unsubscribe } = usePushNotifications();
  const [isSubscribing, setIsSubscribing] = useState(false);

  const handleToggle = async () => {
    setIsSubscribing(true);
    try {
      if (subscription) {
        await unsubscribe();
      } else {
        await subscribe();
      }
    } catch (error) {
      console.error('Error toggling push notifications:', error);
    } finally {
      setIsSubscribing(false);
    }
  };

  if (permission.permission === 'unsupported') {
    return (
      <Alert>
        <AlertDescription>
          Push notifications are not supported in this browser.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <Label htmlFor="push-notifications">Push Notifications</Label>
          <p className="text-sm text-muted-foreground">
            Receive notifications for trading alerts, bot status, and important updates
          </p>
        </div>
        <Switch
          id="push-notifications"
          checked={!!subscription}
          onCheckedChange={handleToggle}
          disabled={isSubscribing || permission.permission === 'denied'}
        />
      </div>

      {permission.permission === 'denied' && (
        <Alert variant="destructive">
          <AlertDescription>
            Notification permission was denied. Please enable it in your browser settings.
          </AlertDescription>
        </Alert>
      )}

      {subscription && (
        <Alert>
          <Bell className="h-4 w-4" />
          <AlertDescription>
            Push notifications are enabled. You'll receive alerts for important events.
          </AlertDescription>
        </Alert>
      )}

      {!subscription && permission.permission === 'default' && (
        <Button
          variant="outline"
          onClick={handleToggle}
          disabled={isSubscribing}
        >
          {isSubscribing ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Enabling...
            </>
          ) : (
            <>
              <Bell className="h-4 w-4 mr-2" />
              Enable Notifications
            </>
          )}
        </Button>
      )}
    </div>
  );
}
