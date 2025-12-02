/**
 * Real-time notifications hook using WebSocket connection.
 * 
 * Provides easy-to-use interface for receiving and managing
 * notifications in React components.
 */

import { useEffect, useState, useCallback, useRef } from 'react';

export interface Notification {
  id: string;
  type: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  data?: Record<string, any>;
  timestamp: string;
  read: boolean;
}

interface UseNotificationsOptions {
  userId: string;
  autoConnect?: boolean;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
}

interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  isConnected: boolean;
  markAsRead: (notificationId: string) => void;
  clearAll: () => void;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Hook for managing real-time notifications via WebSocket.
 * 
 * @example
 * ```typescript
 * const { notifications, unreadCount, markAsRead } = useNotifications({
 *   userId: currentUser.id,
 *   autoConnect: true
 * });
 * ```
 */
export function useNotifications(
  options: UseNotificationsOptions
): UseNotificationsReturn {
  const {
    userId,
    autoConnect = true,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5
  } = options;

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/notifications/ws/notifications?user_id=${userId}`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('Notifications WebSocket connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;

        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'ping' }));
          } else {
            clearInterval(pingInterval);
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'notification') {
            const notification = message.data as Notification;
            
            setNotifications((prev) => {
              // Avoid duplicates
              if (prev.some((n) => n.id === notification.id)) {
                return prev;
              }
              return [notification, ...prev].slice(0, 50); // Keep last 50
            });

            // Show browser notification if permitted
            if (Notification.permission === 'granted' && !notification.read) {
              showBrowserNotification(notification);
            }
          } else if (message.type === 'pong') {
            // Keep-alive response
            console.debug('Notification ping received');
          }
        } catch (error) {
          console.error('Error parsing notification message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('Notifications WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('Notifications WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(
            `Reconnecting... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
          );
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        } else {
          console.error('Max reconnection attempts reached');
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error connecting to notifications WebSocket:', error);
    }
  }, [userId, reconnectDelay, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const markAsRead = useCallback((notificationId: string) => {
    // Send to server
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'mark_read',
        notification_id: notificationId
      }));
    }

    // Update local state
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === notificationId ? { ...n, read: true } : n
      )
    );
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Calculate unread count
  const unreadCount = notifications.filter((n) => !n.read).length;

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Request browser notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  return {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    clearAll,
    connect,
    disconnect
  };
}

/**
 * Show browser notification.
 */
function showBrowserNotification(notification: Notification) {
  if (!('Notification' in window)) {
    return;
  }

  try {
    const browserNotification = new Notification(notification.title, {
      body: notification.message,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: notification.id,
      requireInteraction: notification.priority === 'critical'
    });

    browserNotification.onclick = () => {
      window.focus();
      browserNotification.close();
    };

    // Auto-close after 5 seconds (except critical)
    if (notification.priority !== 'critical') {
      setTimeout(() => browserNotification.close(), 5000);
    }
  } catch (error) {
    console.error('Error showing browser notification:', error);
  }
}

/**
 * Notification display component.
 */
export function NotificationItem({
  notification,
  onMarkAsRead,
  onClose
}: {
  notification: Notification;
  onMarkAsRead: () => void;
  onClose: () => void;
}) {
  const priorityColors = {
    low: 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-700',
    medium: 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700',
    high: 'bg-orange-50 dark:bg-orange-900/20 border-orange-300 dark:border-orange-700',
    critical: 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700'
  };

  const priorityIcons = {
    low: '📝',
    medium: '📢',
    high: '⚠️',
    critical: '🚨'
  };

  return (
    <div
      className={`p-4 mb-2 border rounded-lg ${priorityColors[notification.priority]} ${
        notification.read ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <span className="text-2xl">{priorityIcons[notification.priority]}</span>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                {notification.title}
              </h4>
              {!notification.read && (
                <span className="px-2 py-0.5 text-xs bg-blue-500 text-white rounded-full">
                  New
                </span>
              )}
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
              {notification.message}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              {new Date(notification.timestamp).toLocaleString()}
            </p>
          </div>
        </div>
        <div className="flex gap-2 ml-4">
          {!notification.read && (
            <button
              onClick={onMarkAsRead}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              title="Mark as read"
            >
              ✓
            </button>
          )}
          <button
            onClick={onClose}
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            title="Dismiss"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Notifications panel component.
 */
export function NotificationsPanel({
  notifications,
  unreadCount,
  onMarkAsRead,
  onClearAll
}: {
  notifications: Notification[];
  unreadCount: number;
  onMarkAsRead: (id: string) => void;
  onClearAll: () => void;
}) {
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const filteredNotifications = filter === 'unread'
    ? notifications.filter((n) => !n.read)
    : notifications;

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg p-4 max-w-md w-full max-h-[600px] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Notifications {unreadCount > 0 && `(${unreadCount})`}
        </h3>
        {notifications.length > 0 && (
          <button
            onClick={onClearAll}
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 text-sm rounded ${
            filter === 'all'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`px-3 py-1 text-sm rounded ${
            filter === 'unread'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
          }`}
        >
          Unread {unreadCount > 0 && `(${unreadCount})`}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filteredNotifications.length === 0 ? (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            No notifications
          </p>
        ) : (
          filteredNotifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onMarkAsRead={() => onMarkAsRead(notification.id)}
              onClose={() => onMarkAsRead(notification.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
