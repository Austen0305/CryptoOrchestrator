import React from 'react';
import { useNotificationStore } from '@/lib/notifications';

export function NotificationLiveRegion() {
  const { notifications } = useNotificationStore();
  const latest = notifications[0];
  return (
    <div aria-live="polite" aria-atomic="true" className="sr-only">
      {latest ? `${latest.title}: ${latest.message}` : ''}
    </div>
  );
}
