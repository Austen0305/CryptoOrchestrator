import { useCallback } from 'react';
import { useAuth } from './useAuth';
import { Theme, UserPreferences, UpdatePreferencesData } from '../../../shared/types';
import type { PreferencesUpdatePayload } from '@/types/api';
import { preferencesApi } from '../lib/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import logger from '../lib/logger';

/**
 * Hook for managing user preferences using React Query
 * Provides preferences query and mutations for updates
 */
export function usePreferences() {
  const { user, isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  // Fetch preferences using React Query
  const {
    data: preferences = null,
    isLoading: loading,
    error: queryError,
    refetch,
  } = useQuery<UserPreferences | null>({
    queryKey: ['preferences'],
    queryFn: () => preferencesApi.get(),
    enabled: isAuthenticated && !!user,
    staleTime: 5 * 60 * 1000, // 5 minutes - preferences don't change often
    retry: 2,
  });

  // Update preferences mutation
  const updatePreferencesMutation = useMutation({
    mutationFn: (updates: UpdatePreferencesData) => preferencesApi.update(updates as PreferencesUpdatePayload),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (updates) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['preferences'] });
      
      // Snapshot the previous value
      const previousPreferences = queryClient.getQueryData<UserPreferences | null>(['preferences']);
      
      // Optimistically update to the new value
      if (previousPreferences) {
        queryClient.setQueryData<UserPreferences | null>(['preferences'], (old) => {
          if (!old) return null;
          const merged: UserPreferences = {
            userId: old.userId,
            theme: updates.theme ?? old.theme,
            notifications: {
              trade_executed: updates.notifications?.trade_executed ?? old.notifications.trade_executed ?? false,
              bot_status_change: updates.notifications?.bot_status_change ?? old.notifications.bot_status_change ?? false,
              market_alert: updates.notifications?.market_alert ?? old.notifications.market_alert ?? false,
              system: updates.notifications?.system ?? old.notifications.system ?? false,
            },
            uiSettings: {
              compact_mode: updates.uiSettings?.compact_mode ?? old.uiSettings.compact_mode ?? false,
              auto_refresh: updates.uiSettings?.auto_refresh ?? old.uiSettings.auto_refresh ?? false,
              refresh_interval: updates.uiSettings?.refresh_interval ?? old.uiSettings.refresh_interval ?? 5000,
              default_chart_period: updates.uiSettings?.default_chart_period ?? old.uiSettings.default_chart_period ?? '1d',
              language: updates.uiSettings?.language ?? old.uiSettings.language ?? 'en',
            },
            tradingSettings: {
              default_order_type: updates.tradingSettings?.default_order_type ?? old.tradingSettings.default_order_type ?? 'market',
              confirm_orders: updates.tradingSettings?.confirm_orders ?? old.tradingSettings.confirm_orders ?? true,
              show_fees: updates.tradingSettings?.show_fees ?? old.tradingSettings.show_fees ?? true,
            },
            createdAt: old.createdAt,
            updatedAt: Date.now(),
          };
          return merged;
        });
      }
      
      // Return a context object with the snapshotted value
      return { previousPreferences };
    },
    onSuccess: (data) => {
      // Update cache with new preferences
      queryClient.setQueryData(['preferences'], data);
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (error, updates, context) => {
      if (context?.previousPreferences) {
        queryClient.setQueryData(['preferences'], context.previousPreferences);
      }
      // Error handled by React Query - user will see error state
      logger.error('Failed to update preferences', { error });
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
    },
  });

  // Update theme mutation
  const updateThemeMutation = useMutation({
    mutationFn: async (theme: Theme) => {
      const updated = await preferencesApi.updateTheme(theme);
      return updated.theme;
    },
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (theme) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['preferences'] });
      
      // Snapshot the previous value
      const previousPreferences = queryClient.getQueryData<UserPreferences | null>(['preferences']);
      
      // Optimistically update theme in cache
      if (previousPreferences) {
        queryClient.setQueryData<UserPreferences | null>(['preferences'], (old) => {
          if (!old) return null;
          return { ...old, theme };
        });
      }
      
      // Return a context object with the snapshotted value
      return { previousPreferences };
    },
    onSuccess: (theme) => {
      // Update cache with new theme
      queryClient.setQueryData<UserPreferences | null>(['preferences'], (old) => {
        if (!old) return null;
        return { ...old, theme };
      });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (error, theme, context) => {
      if (context?.previousPreferences) {
        queryClient.setQueryData(['preferences'], context.previousPreferences);
      }
      logger.error('Failed to update theme', { error });
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
    },
  });

  // Reset preferences mutation
  const resetPreferencesMutation = useMutation({
    mutationFn: () => preferencesApi.reset(),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['preferences'] });
      
      // Snapshot the previous value
      const previousPreferences = queryClient.getQueryData<UserPreferences | null>(['preferences']);
      
      // Return a context object with the snapshotted value
      return { previousPreferences };
    },
    onSuccess: (data) => {
      // Update cache with reset preferences
      queryClient.setQueryData(['preferences'], data);
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (error, variables, context) => {
      if (context?.previousPreferences) {
        queryClient.setQueryData(['preferences'], context.previousPreferences);
      }
      logger.error('Failed to reset preferences', { error });
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
    },
  });

  // Wrapper functions for backward compatibility
  const updatePreferences = useCallback(
    async (updates: UpdatePreferencesData) => {
      return await updatePreferencesMutation.mutateAsync(updates);
    },
    [updatePreferencesMutation]
  );

  const updateTheme = useCallback(
    async (theme: Theme) => {
      return await updateThemeMutation.mutateAsync(theme);
    },
    [updateThemeMutation]
  );

  const resetPreferences = useCallback(async () => {
    return await resetPreferencesMutation.mutateAsync();
  }, [resetPreferencesMutation]);

  const reloadPreferences = useCallback(async () => {
    await refetch();
  }, [refetch]);

  // Convert error to string format for backward compatibility
  const error = queryError
    ? queryError instanceof Error
      ? queryError.message
      : 'Failed to load preferences'
    : null;

  return {
    preferences,
    loading,
    error,
    updatePreferences,
    updateTheme,
    resetPreferences,
    reloadPreferences,
    refetch, // Also expose refetch for convenience
  };
}
