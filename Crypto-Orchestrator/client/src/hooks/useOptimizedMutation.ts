/**
 * Optimized Mutation Hook
 * Enhanced React Query mutation hook with performance optimizations
 */

import { useMutation, UseMutationOptions, UseMutationResult } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { handleApiError, showErrorToast } from '@/utils/error-handling';
import { queryClient } from '@/lib/queryClient';
import { toast } from '@/hooks/use-toast';

interface OptimizedMutationOptions<TData, TVariables, TError = Error>
  extends Omit<UseMutationOptions<TData, TError, TVariables>, 'mutationFn'> {
  mutationFn: (variables: TVariables) => Promise<TData>;
  invalidateQueries?: string[][];
  showErrorToast?: boolean;
  onSuccessMessage?: string;
}

/**
 * Optimized mutation hook with automatic error handling and cache invalidation
 */
export function useOptimizedMutation<TData, TVariables, TError = Error>(
  options: OptimizedMutationOptions<TData, TVariables, TError>
): UseMutationResult<TData, TError, TVariables> {
  const {
    mutationFn,
    invalidateQueries = [],
    showErrorToast: showToast = true,
    onSuccessMessage,
    onSuccess,
    onError,
    ...restOptions
  } = options;

  // Memoize mutation function
  const memoizedMutationFn = useMemo(() => {
    return async (variables: TVariables) => {
      try {
        return await mutationFn(variables);
      } catch (error) {
        const appError = handleApiError(error, 'Mutation');
        throw appError;
      }
    };
  }, [mutationFn]);

  // Handle success with cache invalidation
  const handleSuccess = useCallback(
    (data: TData, variables: TVariables, context: any) => {
      // Invalidate related queries
      invalidateQueries.forEach((queryKey) => {
        queryClient.invalidateQueries({ queryKey });
      });

      // Call original onSuccess if provided
      if (onSuccess) {
        (onSuccess as any)(data, variables, context);
      }

      // Show success message if provided
      if (onSuccessMessage) {
        toast({
          title: 'Success',
          description: onSuccessMessage,
        });
      }
    },
    [invalidateQueries, onSuccess, onSuccessMessage]
  );

  // Handle error with toast notification
  const handleError = useCallback(
    (error: TError, variables: TVariables, context: any) => {
      if (showToast) {
        showErrorToast(error, 'Mutation');
      }

      // Call original onError if provided
      if (onError) {
        (onError as any)(error, variables, context);
      }
    },
    [showToast, onError]
  );

  return useMutation<TData, TError, TVariables>({
    mutationFn: memoizedMutationFn,
    onSuccess: handleSuccess,
    onError: handleError,
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
      if (error && typeof error === 'object' && 'statusCode' in error) {
        const statusCode = Number(error.statusCode);
        if (statusCode >= 400 && statusCode < 500) {
          return false;
        }
      }
      return failureCount < 2;
    },
    ...restOptions,
  });
}

