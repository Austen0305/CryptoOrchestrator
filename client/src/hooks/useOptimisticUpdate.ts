/**
 * Optimistic Updates Hook
 * Provides optimistic updates for better UX
 */

import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query';
import { toast } from '@/components/ui/use-toast';

interface OptimisticUpdateOptions<TData, TVariables> {
  queryKey: string[];
  updateFn: (variables: TVariables) => Promise<TData>;
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: Error, variables: TVariables, context: any) => void;
  successMessage?: string;
  errorMessage?: string;
  optimisticData?: (variables: TVariables) => TData;
}

/**
 * Hook for optimistic updates
 * Immediately updates the UI, then syncs with server
 */
export function useOptimisticUpdate<TData, TVariables>(
  options: OptimisticUpdateOptions<TData, TVariables>
) {
  const queryClient = useQueryClient();
  const {
    queryKey,
    updateFn,
    onSuccess,
    onError,
    successMessage,
    errorMessage,
    optimisticData,
  } = options;

  return useMutation({
    mutationFn: updateFn,
    onMutate: async (variables) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot previous value
      const previousData = queryClient.getQueryData<TData>(queryKey);

      // Optimistically update
      if (optimisticData) {
        queryClient.setQueryData(queryKey, optimisticData(variables));
      }

      return { previousData };
    },
    onError: (error, variables, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData);
      }

      toast({
        title: 'Error',
        description: errorMessage || error.message || 'Operation failed',
        variant: 'destructive',
      });

      if (onError) {
        onError(error as Error, variables, context);
      }
    },
    onSuccess: (data, variables) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey });

      if (successMessage) {
        toast({
          title: 'Success',
          description: successMessage,
        });
      }

      if (onSuccess) {
        onSuccess(data, variables);
      }
    },
    onSettled: () => {
      // Always refetch after mutation
      queryClient.invalidateQueries({ queryKey });
    },
  });
}

