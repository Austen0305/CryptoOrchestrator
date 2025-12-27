/**
 * Offline Support Hook
 * Provides utilities for detecting offline status and managing offline actions.
 */

import { useState, useEffect, useCallback } from 'react';
import { offlineStorage } from '@/utils/offlineStorage';

interface OfflineStatus {
  isOnline: boolean;
  isOffline: boolean;
  pendingActions: number;
  lastSyncTime: Date | null;
}

export function useOfflineSupport() {
  const [status, setStatus] = useState<OfflineStatus>({
    isOnline: navigator.onLine,
    isOffline: !navigator.onLine,
    pendingActions: 0,
    lastSyncTime: null,
  });

  useEffect(() => {
    // Initialize offline storage
    offlineStorage.init().catch(console.error);

    // Update online status
    const updateOnlineStatus = () => {
      setStatus((prev) => ({
        ...prev,
        isOnline: navigator.onLine,
        isOffline: !navigator.onLine,
      }));
    };

    // Listen for online/offline events
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    // Update pending actions count
    const updatePendingCount = async () => {
      try {
        const actions = await offlineStorage.getPendingActions();
        setStatus((prev) => ({
          ...prev,
          pendingActions: actions.length,
        }));
      } catch (error) {
        console.error('Error getting pending actions:', error);
      }
    };

    updatePendingCount();
    const interval = setInterval(updatePendingCount, 5000); // Check every 5 seconds

    return () => {
      window.removeEventListener('online', updateOnlineStatus);
      window.removeEventListener('offline', updateOnlineStatus);
      clearInterval(interval);
    };
  }, []);

  const syncPendingActions = useCallback(async () => {
    if (!navigator.onLine) {
      return { success: false, message: 'Device is offline' };
    }

    try {
      const actions = await offlineStorage.getPendingActions();
      let synced = 0;
      let failed = 0;

      for (const action of actions) {
        try {
          // Execute action based on type
          if (action.type === 'trade') {
            const response = await fetch('/api/trades', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${localStorage.getItem('token')}`,
              },
              body: JSON.stringify(action.payload),
            });

            if (response.ok) {
              await offlineStorage.removePendingAction(action.id);
              synced++;
            } else {
              await offlineStorage.incrementRetry(action.id);
              failed++;
            }
          } else if (action.type === 'bot_action') {
            const response = await fetch(action.payload.url, {
              method: action.payload.method || 'POST',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${localStorage.getItem('token')}`,
              },
              body: JSON.stringify(action.payload.data),
            });

            if (response.ok) {
              await offlineStorage.removePendingAction(action.id);
              synced++;
            } else {
              await offlineStorage.incrementRetry(action.id);
              failed++;
            }
          }
        } catch (error) {
          console.error(`Failed to sync action ${action.id}:`, error);
          await offlineStorage.incrementRetry(action.id);
          failed++;
        }
      }

      // Update status
      setStatus((prev) => ({
        ...prev,
        pendingActions: failed,
        lastSyncTime: new Date(),
      }));

      return {
        success: true,
        synced,
        failed,
        message: `Synced ${synced} actions, ${failed} failed`,
      };
    } catch (error) {
      console.error('Error syncing pending actions:', error);
      return {
        success: false,
        message: `Sync failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }, []);

  const queueOfflineAction = useCallback(
    async (type: string, payload: any) => {
      try {
        const id = await offlineStorage.addPendingAction({ type, payload });
        setStatus((prev) => ({
          ...prev,
          pendingActions: prev.pendingActions + 1,
        }));

        // Try to sync immediately if online
        if (navigator.onLine) {
          await syncPendingActions();
        }

        return { success: true, id };
      } catch (error) {
        console.error('Error queueing offline action:', error);
        return {
          success: false,
          message: error instanceof Error ? error.message : 'Unknown error',
        };
      }
    },
    [syncPendingActions]
  );

  return {
    ...status,
    syncPendingActions,
    queueOfflineAction,
  };
}
