/**
 * Offline Hook for Mobile App
 * React hook for offline status and queued actions
 */

import { useState, useEffect } from 'react';
import { offlineService, OfflineStatus, QueuedAction } from '../services/OfflineService';

export interface UseOfflineResult {
  isOnline: boolean;
  status: OfflineStatus | null;
  queuedActions: QueuedAction[];
  queueAction: (
    type: QueuedAction['type'],
    action: string,
    payload: Record<string, any>
  ) => Promise<string>;
  syncNow: () => Promise<void>;
  clearQueue: () => Promise<void>;
  removeAction: (actionId: string) => Promise<boolean>;
}

export const useOffline = (): UseOfflineResult => {
  const [isOnline, setIsOnline] = useState(true);
  const [status, setStatus] = useState<OfflineStatus | null>(null);
  const [queuedActions, setQueuedActions] = useState<QueuedAction[]>([]);

  useEffect(() => {
    // Initial status
    offlineService.getStatus().then(setStatus);
    setQueuedActions(offlineService.getQueuedActions());

    // Listen to network status changes
    const handleNetworkStatusChanged = (online: boolean) => {
      setIsOnline(online);
      offlineService.getStatus().then(setStatus);
    };

    // Listen to queue changes
    const handleActionQueued = () => {
      setQueuedActions(offlineService.getQueuedActions());
      offlineService.getStatus().then(setStatus);
    };

    const handleActionExecuted = () => {
      setQueuedActions(offlineService.getQueuedActions());
      offlineService.getStatus().then(setStatus);
    };

    const handleActionFailed = () => {
      setQueuedActions(offlineService.getQueuedActions());
      offlineService.getStatus().then(setStatus);
    };

    const handleSyncCompleted = () => {
      offlineService.getStatus().then(setStatus);
    };

    offlineService.on('networkStatusChanged', handleNetworkStatusChanged);
    offlineService.on('actionQueued', handleActionQueued);
    offlineService.on('actionExecuted', handleActionExecuted);
    offlineService.on('actionFailed', handleActionFailed);
    offlineService.on('syncCompleted', handleSyncCompleted);

    // Periodic status update
    const interval = setInterval(() => {
      offlineService.getStatus().then(setStatus);
      setQueuedActions(offlineService.getQueuedActions());
    }, 5000);

    return () => {
      offlineService.off('networkStatusChanged', handleNetworkStatusChanged);
      offlineService.off('actionQueued', handleActionQueued);
      offlineService.off('actionExecuted', handleActionExecuted);
      offlineService.off('actionFailed', handleActionFailed);
      offlineService.off('syncCompleted', handleSyncCompleted);
      clearInterval(interval);
    };
  }, []);

  const queueAction = async (
    type: QueuedAction['type'],
    action: string,
    payload: Record<string, any>
  ): Promise<string> => {
    return await offlineService.queueAction(type, action, payload);
  };

  const syncNow = async (): Promise<void> => {
    await offlineService.syncQueuedActions();
  };

  const clearQueue = async (): Promise<void> => {
    await offlineService.clearQueuedActions();
  };

  const removeAction = async (actionId: string): Promise<boolean> => {
    return await offlineService.removeQueuedAction(actionId);
  };

  return {
    isOnline,
    status,
    queuedActions,
    queueAction,
    syncNow,
    clearQueue,
    removeAction,
  };
};
