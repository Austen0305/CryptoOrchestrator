import { useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { Notification } from '../../../shared/schema';
import { useScenarioStore } from '@/hooks/useScenarioStore';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '@/lib/queryClient';

export const useNotifications = () => {
  const { toast } = useToast();
  const { isAuthenticated } = useAuth();
  const { isConnected } = useWebSocket();
  const queryClient = useQueryClient();

  // Fetch notifications using React Query
  const { data: notifications = [], isLoading, error, refetch } = useQuery<Notification[]>({
    queryKey: ['notifications'],
    queryFn: async () => {
      const response = await apiRequest<{ data: Notification[] }>('/api/notifications', {
        method: 'GET',
      });
      return response.data || [];
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds
    refetchInterval: isConnected ? false : 30000, // Poll every 30s if WebSocket not connected
    retry: 2,
  });

  // Calculate unread count
  const unreadCount = notifications.filter(n => !n.read).length;

  // Mark notification as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: async (notificationId: string) => {
      return await apiRequest(`/api/notifications/${notificationId}/read`, {
        method: 'PATCH',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to mark notification as read',
        variant: 'destructive',
      });
    },
  });

  // Mark all as read mutation
  const markAllAsReadMutation = useMutation({
    mutationFn: async () => {
      return await apiRequest('/api/notifications/read-all', {
        method: 'PATCH',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast({
        title: 'Success',
        description: 'All notifications marked as read',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to mark all notifications as read',
        variant: 'destructive',
      });
    },
  });

  // Delete notification mutation
  const deleteNotificationMutation = useMutation({
    mutationFn: async (notificationId: string) => {
      return await apiRequest(`/api/notifications/${notificationId}`, {
        method: 'DELETE',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast({
        title: 'Success',
        description: 'Notification deleted',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete notification',
        variant: 'destructive',
      });
    },
  });

  // Create notification mutation
  const createNotificationMutation = useMutation({
    mutationFn: async (data: {
      type: Notification['type'];
      title: string;
      message: string;
      data?: Record<string, unknown>;
    }) => {
      return await apiRequest<{ data: Notification }>('/api/notifications', {
        method: 'POST',
        body: data,
      });
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      const newNotification = response.data;
      toast({
        title: newNotification.title,
        description: newNotification.message,
      });
      return newNotification;
    },
    onError: (error: Error) => {
      console.error('Error creating notification:', error);
      return null;
    },
  });

  // WebSocket subscription pattern updated: notifications served on dedicated /ws/notifications endpoint.
  // We reuse the main market-data socket only for generic events; dedicated endpoint preferred for volume.

  // Handle WebSocket messages for notifications
  // Note: WebSocket handling is kept separate as it updates React Query cache directly
  // This is handled by the WebSocket hook or a separate WebSocket service
  // For now, we rely on React Query's refetchInterval when WebSocket is not connected

  const markAsRead = useCallback(async (notificationId: string) => {
    await markAsReadMutation.mutateAsync(notificationId);
  }, [markAsReadMutation]);

  const markAllAsRead = useCallback(async () => {
    await markAllAsReadMutation.mutateAsync();
  }, [markAllAsReadMutation]);

  const deleteNotification = useCallback(async (notificationId: string) => {
    await deleteNotificationMutation.mutateAsync(notificationId);
  }, [deleteNotificationMutation]);

  const createNotification = useCallback(async (
    type: Notification['type'],
    title: string,
    message: string,
    data?: Record<string, any>
  ) => {
    return await createNotificationMutation.mutateAsync({
      type,
      title,
      message,
      data,
    });
  }, [createNotificationMutation]);

  const fetchNotifications = useCallback(async () => {
    await refetch();
  }, [refetch]);

  return {
    notifications,
    isLoading,
    error,
    unreadCount,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    createNotification,
  };
};
