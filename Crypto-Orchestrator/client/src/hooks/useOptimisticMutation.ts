/**
 * Optimistic Mutation Hook
 * Provides optimistic updates for mutations with rollback on error
 */

import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query';
import { useCallback } from 'react';

interface OptimisticMutationOptions<TData, TVariables, TError> {
  mutationFn: (variables: TVariables) => Promise<TData>;
  onMutate?: (variables: TVariables) => Promise<unknown> | unknown;
  onError?: (error: TError, variables: TVariables, context: unknown) => void;
  onSuccess?: (data: TData, variables: TVariables, context: unknown) => void;
  onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables, context: unknown) => void;
  invalidateQueries?: string[][];
}

export function useOptimisticMutation<TData, TVariables, TError = Error>(
  options: OptimisticMutationOptions<TData, TVariables, TError>
) {
  const queryClient = useQueryClient();
  const {
    mutationFn,
    onMutate,
    onError,
    onSuccess,
    onSettled,
    invalidateQueries = [],
  } = options;

  const mutation = useMutation<TData, TError, TVariables>({
    mutationFn,
    onMutate: async (variables) => {
      // Cancel outgoing refetches
      if (invalidateQueries.length > 0) {
        await Promise.all(
          invalidateQueries.map(queryKey =>
            queryClient.cancelQueries({ queryKey })
          )
        );
      }

      // Snapshot previous values
      const previousValues = await Promise.all(
        invalidateQueries.map(queryKey =>
          queryClient.getQueryData(queryKey)
        )
      );

      // Custom optimistic update
      if (onMutate) {
        await onMutate(variables);
      }

      return { previousValues };
    },
    onError: (error, variables, context) => {
      // Rollback on error
      if (context && typeof context === 'object' && 'previousValues' in context) {
        const previousValues = (context as { previousValues: unknown[] }).previousValues;
        if (Array.isArray(previousValues)) {
          invalidateQueries.forEach((queryKey, index) => {
            queryClient.setQueryData(queryKey, previousValues[index]);
          });
        }
      }

      if (onError) {
        onError(error, variables, context);
      }
    },
    onSuccess: (data, variables, context) => {
      if (onSuccess) {
        onSuccess(data, variables, context);
      }
    },
    onSettled: (data, error, variables, context) => {
      // Invalidate queries to refetch
      invalidateQueries.forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });

      if (onSettled) {
        onSettled(data, error, variables, context);
      }
    },
  });

  return mutation;
}

