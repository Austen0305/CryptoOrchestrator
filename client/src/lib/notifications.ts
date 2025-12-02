import { create } from 'zustand';
import { TrendingUp, AlertTriangle, CheckCircle, Info, Bot } from 'lucide-react';

export type NotificationType = 'success' | 'error' | 'warning' | 'info' | 'trade' | 'bot';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionLabel?: string;
  actionUrl?: string;
}

interface NotificationStore {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],
  unreadCount: 0,

  addNotification: (notification) => {
    const newNotification: Notification = {
      ...notification,
      id: `notif-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      read: false,
    };

    set((state) => ({
      notifications: [newNotification, ...state.notifications].slice(0, 50), // Keep last 50
      unreadCount: state.unreadCount + 1,
    }));

    // Optional: Play sound
    if (typeof Audio !== 'undefined') {
      try {
        const audio = new Audio('/notification.mp3');
        audio.volume = 0.3;
        audio.play().catch(() => {
          // Ignore audio play errors (user interaction required in some browsers)
        });
      } catch (error) {
        // Audio not available
      }
    }
  },

  markAsRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    })),

  markAllAsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    })),

  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
      unreadCount: state.notifications.find((n) => n.id === id && !n.read)
        ? state.unreadCount - 1
        : state.unreadCount,
    })),

  clearAll: () =>
    set({
      notifications: [],
      unreadCount: 0,
    }),
}));

// Accessibility live region for announcements (consumer can mount once in App shell)
// React live region is provided in components/NotificationLiveRegion.tsx to avoid JSX in .ts files.

// Helper function to get icon for notification type
export function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case 'success':
      return CheckCircle;
    case 'error':
      return AlertTriangle;
    case 'warning':
      return AlertTriangle;
    case 'trade':
      return TrendingUp;
    case 'bot':
      return Bot;
    case 'info':
    default:
      return Info;
  }
}

// Helper function to get color classes for notification type
export function getNotificationColor(type: NotificationType) {
  switch (type) {
    case 'success':
      return 'text-green-500 bg-green-500/10 border-green-500/20';
    case 'error':
      return 'text-red-500 bg-red-500/10 border-red-500/20';
    case 'warning':
      return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
    case 'trade':
      return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
    case 'bot':
      return 'text-purple-500 bg-purple-500/10 border-purple-500/20';
    case 'info':
    default:
      return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
  }
}

// Convenience functions for common notification types
export function notifyTradeExecuted(symbol: string, side: 'buy' | 'sell', amount: number, price: number) {
  const store = useNotificationStore.getState();
  store.addNotification({
    type: 'trade',
    title: `Trade Executed: ${side.toUpperCase()} ${symbol}`,
    message: `${side === 'buy' ? 'Bought' : 'Sold'} ${amount} ${symbol} at $${price.toFixed(2)}`,
    actionLabel: 'View Trade',
    actionUrl: '/analytics',
  });
}

export function notifyBotStatusChange(botName: string, status: 'started' | 'stopped' | 'error', message?: string) {
  const store = useNotificationStore.getState();
  const type = status === 'error' ? 'error' : 'bot';
  const title = `Bot ${status === 'started' ? 'Started' : status === 'stopped' ? 'Stopped' : 'Error'}`;
  
  store.addNotification({
    type,
    title: `${title}: ${botName}`,
    message: message || `The bot "${botName}" has ${status}`,
    actionLabel: 'Manage Bots',
    actionUrl: '/bots',
  });
}

export function notifyPriceAlert(symbol: string, price: number, condition: string) {
  const store = useNotificationStore.getState();
  store.addNotification({
    type: 'warning',
    title: `Price Alert: ${symbol}`,
    message: `${symbol} has ${condition} $${price.toFixed(2)}`,
    actionLabel: 'View Market',
    actionUrl: '/markets',
  });
}

export function notifyRiskAlert(message: string, severity: 'warning' | 'error' = 'warning') {
  const store = useNotificationStore.getState();
  store.addNotification({
    type: severity,
    title: 'Risk Alert',
    message,
    actionLabel: 'View Risk',
    actionUrl: '/risk',
  });
}
