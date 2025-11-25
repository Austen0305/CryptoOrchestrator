import { useState, useEffect, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { Notification } from '../../../shared/schema';
import { useScenarioStore } from '@/hooks/useScenarioStore';

export const useNotifications = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const { toast } = useToast();
  const { getAuthHeaders, isAuthenticated } = useAuth();
  const { isConnected } = useWebSocket();
  // reconnectTimeoutRef removed (not used); any future reconnect logic can add it back with cleanup

  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      setIsLoading(true);
      const response = await fetch('/api/notifications', {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch notifications');
      }

      const data = await response.json();
      setNotifications(data.data || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
      toast({
        title: 'Error',
        description: 'Failed to load notifications',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [getAuthHeaders, isAuthenticated, toast]);

  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      const response = await fetch(`/api/notifications/${notificationId}/read`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to mark notification as read');
      }

      setNotifications(prev =>
        prev.map(notification =>
          notification.id === notificationId
            ? { ...notification, read: true }
            : notification
        )
      );
    } catch (error) {
      console.error('Error marking notification as read:', error);
      toast({
        title: 'Error',
        description: 'Failed to mark notification as read',
        variant: 'destructive',
      });
    }
  }, [getAuthHeaders, toast]);

  const markAllAsRead = useCallback(async () => {
    try {
      const response = await fetch('/api/notifications/read-all', {
        method: 'PATCH',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to mark all notifications as read');
      }

      setNotifications(prev =>
        prev.map(notification => ({ ...notification, read: true }))
      );

      toast({
        title: 'Success',
        description: 'All notifications marked as read',
      });
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
      toast({
        title: 'Error',
        description: 'Failed to mark all notifications as read',
        variant: 'destructive',
      });
    }
  }, [getAuthHeaders, toast]);

  const deleteNotification = useCallback(async (notificationId: string) => {
    try {
      const response = await fetch(`/api/notifications/${notificationId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to delete notification');
      }

      setNotifications(prev =>
        prev.filter(notification => notification.id !== notificationId)
      );

      toast({
        title: 'Success',
        description: 'Notification deleted',
      });
    } catch (error) {
      console.error('Error deleting notification:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete notification',
        variant: 'destructive',
      });
    }
  }, [getAuthHeaders, toast]);

  const createNotification = useCallback(async (
    type: Notification['type'],
    title: string,
    message: string,
    data?: Record<string, any>
  ) => {
    try {
      const response = await fetch('/api/notifications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          type,
          title,
          message,
          data,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create notification');
      }

      const result = await response.json();
      const newNotification = result.data;

      setNotifications(prev => [newNotification, ...prev]);

      // Show toast for new notification
      toast({
        title: newNotification.title,
        description: newNotification.message,
      });

      return newNotification;
    } catch (error) {
      console.error('Error creating notification:', error);
      return null;
    }
  }, [getAuthHeaders, toast]);

  // WebSocket subscription pattern updated: notifications served on dedicated /ws/notifications endpoint.
  // We reuse the main market-data socket only for generic events; dedicated endpoint preferred for volume.

  // Handle WebSocket messages for notifications
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'initial_notifications':
            setNotifications(data.data || []);
            break;
          case 'notification':
            setNotifications(prev => [data.data, ...prev]);
            setUnreadCount(prev => prev + 1);
            break;
          case 'risk_scenario':
            // Scenario broadcast from backend: data.data holds scenario result
            if (data.data?.data) {
              const scenario = data.data.data;
              // Update scenario store (maintain history)
              try {
                const store = useScenarioStore.getState();
                store.add?.(scenario);
              } catch (e) {
                console.warn('Scenario store update failed', e);
              }
            }
            // Also surface as notification if present
            if (data.data) {
              setNotifications(prev => [data.data, ...prev]);
              setUnreadCount(prev => prev + 1);
            }
            break;
          case 'notification_read':
            setNotifications(prev =>
              prev.map(n =>
                n.id === data.notification_id ? { ...n, read: true } : n
              )
            );
            setUnreadCount(prev => Math.max(0, prev - 1));
            break;
          case 'all_notifications_read':
            setNotifications(prev =>
              prev.map(n => ({ ...n, read: true }))
            );
            setUnreadCount(0);
            break;
          case 'notification_deleted':
            setNotifications(prev =>
              prev.filter(n => n.id !== data.notification_id)
            );
            break;
          case 'unread_count_update':
            setUnreadCount(data.count);
            break;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    if (!isConnected) return undefined;
    // Dedicated notifications websocket
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (!token || !isAuthenticated) return undefined;
    const wsBase = (typeof window !== 'undefined' && (window as any).__WS_BASE__)
      || (import.meta as any)?.env?.VITE_WS_BASE_URL
      || (() => {
        const api = (typeof window !== 'undefined' && (window as any).__API_BASE__) || (import.meta as any)?.env?.VITE_API_BASE_URL || '';
        if (api.startsWith('http')) return api.replace(/^http/, 'ws');
        return 'ws://localhost:8000';
      })();
    const ws = new WebSocket(`${wsBase}/ws/notifications`);
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'auth', token }));
    };
    ws.addEventListener('message', handleMessage);
    return () => ws.close();
  }, [isConnected]);

  // Fallback to polling when WebSocket is not available
  useEffect(() => {
    if (isConnected || !isAuthenticated) return undefined;
    fetchNotifications();
    const pollInterval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(pollInterval);
  }, [isAuthenticated, isConnected, fetchNotifications]);

  // Fetch notifications on mount and when authentication changes
  useEffect(() => {
    if (!isAuthenticated) {
      setNotifications([]);
      setUnreadCount(0);
      return undefined;
    }
    if (!isConnected) fetchNotifications();
    return undefined;
  }, [isAuthenticated, isConnected, fetchNotifications]);

  // Update unread count when notifications change (for non-WebSocket mode)
  useEffect(() => {
    if (isConnected) return undefined;
    setUnreadCount(notifications.filter(n => !n.read).length);
    return undefined;
  }, [notifications, isConnected]);

  return {
    notifications,
    isLoading,
    unreadCount,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    createNotification,
  };
};
