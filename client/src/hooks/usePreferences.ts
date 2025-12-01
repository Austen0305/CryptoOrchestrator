import { useCallback } from 'react';
import { useAuth } from './useAuth';
import { Theme, UserPreferences, UpdatePreferencesData } from '../../../shared/types';
import { apiRequest } from '../lib/queryClient';
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
    queryFn: async () => {
      try {
        const data = await apiRequest<UserPreferences>('/api/preferences', { method: 'GET' });
        return data;
      } catch (err) {
        // Log error but don't expose to user - let React Query handle it
        throw err;
      }
    },
    enabled: isAuthenticated && !!user,
    staleTime: 5 * 60 * 1000, // 5 minutes - preferences don't change often
    retry: 2,
  });

  // Update preferences mutation
  const updatePreferencesMutation = useMutation({
    mutationFn: async (updates: UpdatePreferencesData) => {
      const data = await apiRequest<UserPreferences>('/api/preferences', {
        method: 'PUT',
        body: updates,
      });
      return data;
    },
    onSuccess: (data) => {
      // Update cache with new preferences
      queryClient.setQueryData(['preferences'], data);
    },
    onError: (error) => {
      // Error handled by React Query - user will see error state
      logger.error('Failed to update preferences', { error });
    },
  });

  // Update theme mutation
  const updateThemeMutation = useMutation({
    mutationFn: async (theme: Theme) => {
      await apiRequest('/api/preferences/theme', {
        method: 'PATCH',
        body: { theme },
      });
      return theme;
    },
    onSuccess: (theme) => {
      // Optimistically update theme in cache
      queryClient.setQueryData<UserPreferences | null>(['preferences'], (old) => {
        if (!old) return null;
        return { ...old, theme };
      });
    },
    onError: (error) => {
      logger.error('Failed to update theme', { error });
    },
  });

  // Reset preferences mutation
  const resetPreferencesMutation = useMutation({
    mutationFn: async () => {
      const data = await apiRequest<{ preferences: UserPreferences }>('/api/preferences/reset', {
        method: 'POST',
      });
      return data.preferences;
    },
    onSuccess: (data) => {
      // Update cache with reset preferences
      queryClient.setQueryData(['preferences'], data);
    },
    onError: (error) => {
      logger.error('Failed to reset preferences', { error });
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
