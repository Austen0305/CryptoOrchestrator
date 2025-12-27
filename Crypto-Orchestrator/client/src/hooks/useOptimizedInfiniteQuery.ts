/**
 * Optimized Infinite Query Hook
 * Enhanced infinite scroll with performance optimizations
 */

import { useInfiniteQuery, UseInfiniteQueryOptions } from '@tanstack/react-query';
import { useMemo, useCallback } from 'react';
import { handleApiError } from '@/utils/error-handling';

interface OptimizedInfiniteQueryOptions<TData, TError = Error>
  extends Omit<UseInfiniteQueryOptions<TData, TError>, 'queryFn'> {
  queryFn: (pageParam: unknown) => Promise<TData>;
  getNextPageParam: (lastPage: TData, allPages: TData[]) => unknown | undefined;
  pageSize?: number;
}

export function useOptimizedInfiniteQuery<TData, TError = Error>(
  options: OptimizedInfiniteQueryOptions<TData, TError>
) {
  const {
    queryKey,
    queryFn,
    getNextPageParam,
    pageSize = 20,
    initialPageParam,
    ...restOptions
  } = options;

  // Memoize query function
  const memoizedQueryFn = useMemo(() => {
    return async ({ pageParam = 0 }: { pageParam?: unknown }) => {
      try {
        return await queryFn(pageParam);
      } catch (error) {
        const appError = handleApiError(error, `Infinite Query: ${String(queryKey)}`);
        throw appError;
      }
    };
  }, [queryFn, queryKey]);

  const query = useInfiniteQuery<TData, TError>({
    queryKey,
    queryFn: memoizedQueryFn as any,
    getNextPageParam,
    initialPageParam: initialPageParam ?? 0,
    ...restOptions,
  } as any);

  // Flatten pages
  const data = useMemo(() => {
    return query.data?.pages.flat() || [];
  }, [query.data]);

  // Check if has more
  const hasNextPage = useMemo(() => {
    return query.hasNextPage ?? false;
  }, [query.hasNextPage]);

  // Load more
  const loadMore = useCallback(() => {
    if (hasNextPage && !query.isFetchingNextPage) {
      query.fetchNextPage();
    }
  }, [hasNextPage, query.isFetchingNextPage, query.fetchNextPage]);

  return {
    ...query,
    data,
    hasNextPage,
    loadMore,
  };
}

