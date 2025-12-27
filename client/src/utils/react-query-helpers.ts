/**
 * React Query Helpers
 * Utility functions for React Query optimization
 */

import { QueryClient } from '@tanstack/react-query';

/**
 * Prefetch query data
 */
export async function prefetchQuery<T>(
  queryClient: QueryClient,
  queryKey: string[],
  queryFn: () => Promise<T>
): Promise<void> {
  await queryClient.prefetchQuery({
    queryKey,
    queryFn,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Invalidate and refetch queries
 */
export function invalidateAndRefetch(
  queryClient: QueryClient,
  queryKey: string[]
): Promise<void> {
  return queryClient.invalidateQueries({ queryKey });
}

/**
 * Optimistically update query data
 */
export function optimisticallyUpdate<T>(
  queryClient: QueryClient,
  queryKey: string[],
  updater: (old: T | undefined) => T
): void {
  queryClient.setQueryData<T>(queryKey, updater);
}

/**
 * Get cached query data
 */
export function getCachedData<T>(
  queryClient: QueryClient,
  queryKey: string[]
): T | undefined {
  return queryClient.getQueryData<T>(queryKey);
}

