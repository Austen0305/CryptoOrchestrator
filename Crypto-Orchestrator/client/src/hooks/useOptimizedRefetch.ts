/**
 * Optimized Refetch Hook
 * Enhanced refetch with retry logic and error handling
 */

import { useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { showErrorToast } from '@/utils/error-handling';

interface UseOptimizedRefetchOptions {
  queryKey: string[];
  retries?: number;
  retryDelay?: number;
  showErrorToast?: boolean;
}

export function useOptimizedRefetch({
  queryKey,
  retries = 3,
  retryDelay = 1000,
  showErrorToast: showToast = true,
}: UseOptimizedRefetchOptions) {
  const queryClient = useQueryClient();

  const refetch = useCallback(
    async () => {
      let lastError: Error | null = null;

      for (let i = 0; i < retries; i++) {
        try {
          await queryClient.refetchQueries({ queryKey });
          return;
        } catch (error) {
          lastError = error as Error;
          if (i < retries - 1) {
            await new Promise((resolve) => setTimeout(resolve, retryDelay * (i + 1)));
          }
        }
      }

      if (showToast && lastError) {
        showErrorToast(lastError, 'Refetch');
      }

      throw lastError;
    },
    [queryClient, queryKey, retries, retryDelay, showToast]
  );

  return { refetch };
}

