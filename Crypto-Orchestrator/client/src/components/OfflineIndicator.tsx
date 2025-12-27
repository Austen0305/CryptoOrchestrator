/**
 * Offline Indicator Component
 * Displays offline status and pending sync actions.
 */

import { useOfflineSupport } from '@/hooks/useOfflineSupport';
import { AlertCircle, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export function OfflineIndicator() {
  const { isOffline, pendingActions, syncPendingActions } = useOfflineSupport();

  if (!isOffline && pendingActions === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-md">
      {isOffline ? (
        <Alert variant="destructive">
          <WifiOff className="h-4 w-4" />
          <AlertTitle>You're offline</AlertTitle>
          <AlertDescription>
            Some features may be limited. Changes will sync when you're back online.
          </AlertDescription>
        </Alert>
      ) : pendingActions > 0 ? (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Pending actions</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{pendingActions} action{pendingActions !== 1 ? 's' : ''} waiting to sync</span>
            <Button
              size="sm"
              variant="outline"
              onClick={syncPendingActions}
              className="ml-2"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Sync Now
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}
