/**
 * Optimized Query Hook
 * Enhanced React Query hook with performance optimizations
 */

import { useQuery, UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { useMemo } from 'react';
import { handleApiError } from '@/utils/error-handling';

interface OptimizedQueryOptions<TData, TError = Error> extends Omit<UseQueryOptions<TData, TError>, 'queryFn'> {
  queryFn: () => Promise<TData>;
  enableCache?: boolean;
  cacheTime?: number;
  staleTime?: number;
}

/**
 * Optimized query hook with automatic error handling and caching
 */
export function useOptimizedQuery<TData, TError = Error>(
  options: OptimizedQueryOptions<TData, TError>
): UseQueryResult<TData, TError> {
  const {
    queryKey,
    queryFn,
    enableCache = true,
    cacheTime = 5 * 60 * 1000, // 5 minutes
    staleTime = 1 * 60 * 1000, // 1 minute
    ...restOptions
  } = options;

  // Memoize query function to prevent unnecessary re-renders
  const memoizedQueryFn = useMemo(() => {
    return async () => {
      try {
        return await queryFn();
      } catch (error) {
        const appError = handleApiError(error, `Query: ${String(queryKey)}`);
        throw appError;
      }
    };
  }, [queryFn, queryKey]);

  return useQuery<TData, TError>({
    queryKey,
    queryFn: memoizedQueryFn,
    gcTime: enableCache ? cacheTime : 0,
    staleTime: enableCache ? staleTime : 0,
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
      if (error && typeof error === 'object' && 'statusCode' in error) {
        const statusCode = Number(error.statusCode);
        if (statusCode >= 400 && statusCode < 500) {
          return false;
        }
      }
      return failureCount < 3;
    },
    ...restOptions,
  });
}

