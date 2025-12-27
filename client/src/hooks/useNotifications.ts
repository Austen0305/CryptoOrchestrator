import { useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { Notification } from '../../../shared/schema';
import { useScenarioStore } from '@/hooks/useScenarioStore';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '@/lib/api';
import { apiRequest } from '@/lib/queryClient';
import logger from '@/lib/logger';

export const useNotifications = () => {
  const { toast } = useToast();
  const { isAuthenticated } = useAuth();
  const { isConnected } = useWebSocket();
  const queryClient = useQueryClient();

  // Fetch notifications using React Query
  const { data: notifications = [], isLoading, error, refetch } = useQuery<Notification[]>({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list(),
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds
    refetchInterval: isConnected ? false : 30000, // Poll every 30s if WebSocket not connected
    retry: 2,
  });

  // Calculate unread count
  const unreadCount = notifications.filter(n => !n.read).length;

  // Mark notification as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: (notificationId: string) => {
      // Notification id is a string in the schema, but API expects number
      // Parse string ID to number for API call
      const id = parseInt(notificationId, 10);
      if (isNaN(id)) {
        throw new Error(`Invalid notification ID: ${notificationId}`);
      }
      return notificationsApi.markRead(id);
    },
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (notificationId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['notifications'] });
      
      // Snapshot the previous value
      const previousNotifications = queryClient.getQueryData<Notification[]>(['notifications']);
      
      // Optimistically update to the new value
      if (previousNotifications) {
        queryClient.setQueryData<Notification[]>(['notifications'], (old) =>
          old?.map((n) => (n.id === notificationId ? { ...n, read: true } : n)) ?? []
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousNotifications };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (error: Error, notificationId, context) => {
      if (context?.previousNotifications) {
        queryClient.setQueryData(['notifications'], context.previousNotifications);
      }
      toast({
        title: 'Error',
        description: error.message || 'Failed to mark notification as read',
        variant: 'destructive',
      });
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  // Mark all as read mutation
  const markAllAsReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['notifications'] });
      
      // Snapshot the previous value
      const previousNotifications = queryClient.getQueryData<Notification[]>(['notifications']);
      
      // Optimistically update to the new value
      if (previousNotifications) {
        queryClient.setQueryData<Notification[]>(['notifications'], (old) =>
          old?.map((n) => ({ ...n, read: true })) ?? []
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousNotifications };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast({
        title: 'Success',
        description: 'All notifications marked as read',
      });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (error: Error, variables, context) => {
      if (context?.previousNotifications) {
        queryClient.setQueryData(['notifications'], context.previousNotifications);
      }
      toast({
        title: 'Error',
        description: error.message || 'Failed to mark all notifications as read',
        variant: 'destructive',
      });
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  // Delete notification mutation
  const deleteNotificationMutation = useMutation({
    mutationFn: (notificationId: string) => {
      // Notification id is a string in the schema, but API expects number
      const id = typeof notificationId === 'string' ? parseInt(notificationId, 10) : notificationId;
      return notificationsApi.delete(id);
    },
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (notificationId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['notifications'] });
      
      // Snapshot the previous value
      const previousNotifications = queryClient.getQueryData<Notification[]>(['notifications']);
      
      // Optimistically update to the new value (remove the notification)
      if (previousNotifications) {
        queryClient.setQueryData<Notification[]>(['notifications'], (old) =>
          old?.filter((n) => n.id !== notificationId) ?? []
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousNotifications };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast({
        title: 'Success',
        description: 'Notification deleted',
      });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (error: Error, notificationId, context) => {
      if (context?.previousNotifications) {
        queryClient.setQueryData(['notifications'], context.previousNotifications);
      }
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete notification',
        variant: 'destructive',
      });
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  // Create notification mutation
  // Note: No create function in notificationsApi, so using apiRequest directly
  const createNotificationMutation = useMutation({
    mutationFn: async (data: {
      type: Notification['type'];
      title: string;
      message: string;
      data?: Record<string, unknown>;
    }) => {
      // Using apiRequest directly since there's no create function in notificationsApi
      const response = await apiRequest<Notification>('/api/notifications', {
        method: 'POST',
        body: data,
      });
      return response;
    },
    onSuccess: (newNotification) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast({
        title: newNotification.title,
        description: newNotification.message,
      });
      return newNotification;
    },
    onError: (error: Error) => {
      logger.error('Error creating notification', { error });
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
    data?: Record<string, unknown>
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
