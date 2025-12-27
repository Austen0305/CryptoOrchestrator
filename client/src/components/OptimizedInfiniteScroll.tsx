/**
 * Optimized Infinite Scroll Component
 * Infinite scroll with intersection observer
 */

import React, { useEffect, useRef, useCallback } from 'react';
import { useIntersectionObserver } from '@/hooks/useIntersectionObserver';
import { OptimizedLoading } from './OptimizedLoading';

interface OptimizedInfiniteScrollProps {
  hasMore: boolean;
  isLoading: boolean;
  onLoadMore: () => void;
  threshold?: number;
  rootMargin?: string;
  children: React.ReactNode;
  loader?: React.ReactNode;
  endMessage?: React.ReactNode;
}

export function OptimizedInfiniteScroll({
  hasMore,
  isLoading,
  onLoadMore,
  threshold = 0.1,
  rootMargin = '100px',
  children,
  loader,
  endMessage,
}: OptimizedInfiniteScrollProps) {
  const [loadMoreRef, isIntersecting] = useIntersectionObserver<HTMLDivElement>({
    threshold,
    rootMargin,
  });

  const hasLoadedRef = useRef(false);

  useEffect(() => {
    if (isIntersecting && hasMore && !isLoading && !hasLoadedRef.current) {
      hasLoadedRef.current = true;
      onLoadMore();
    } else if (!isIntersecting) {
      hasLoadedRef.current = false;
    }
  }, [isIntersecting, hasMore, isLoading, onLoadMore]);

  return (
    <>
      {children}
      {hasMore && (
        <div ref={loadMoreRef} className="flex justify-center py-4">
          {isLoading && (loader || <OptimizedLoading variant="spinner" size="sm" />)}
        </div>
      )}
      {!hasMore && endMessage && (
        <div className="flex justify-center py-4 text-sm text-muted-foreground">
          {endMessage}
        </div>
      )}
    </>
  );
}
