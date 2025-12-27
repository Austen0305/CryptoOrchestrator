/**
 * Route Optimization Utilities
 * Helpers for optimizing route loading and navigation
 */

import React from 'react';
import { lazyLoadComponent } from './code-splitting';

/**
 * Preload route on hover
 */
export function preloadRoute(importFn: () => Promise<unknown>): void {
  importFn().catch((error) => {
    console.error('Failed to preload route:', error);
  });
}

/**
 * Create optimized route component
 */
export function createOptimizedRoute<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  fallback?: React.ReactNode
) {
  const LazyComponent = lazyLoadComponent(importFn);

  return (props: React.ComponentPropsWithoutRef<T>) => (
    <React.Suspense fallback={fallback || <div>Loading...</div>}>
      <LazyComponent {...props} />
    </React.Suspense>
  );
}

/**
 * Prefetch route data
 */
export function prefetchRouteData(
  queryClient: any,
  queryKey: string[],
  queryFn: () => Promise<unknown>
): void {
  queryClient.prefetchQuery({
    queryKey,
    queryFn,
    staleTime: 5 * 60 * 1000,
  });
}
