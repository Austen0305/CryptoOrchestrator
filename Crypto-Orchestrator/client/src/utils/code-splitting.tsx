/**
 * Code Splitting Utilities
 * Helpers for dynamic imports and code splitting
 */

import React, { Suspense } from 'react';

/**
 * Lazy load component with error boundary
 */
export function lazyLoadComponent<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>
): React.LazyExoticComponent<T> {
  return React.lazy(async () => {
    try {
      return await importFn();
    } catch (error) {
      console.error('Failed to load component:', error);
      // Return a fallback component
      return {
        default: (() => (
          <div className="p-4 text-center text-muted-foreground">
            Failed to load component. Please refresh the page.
          </div>
        )) as unknown as T,
      };
    }
  });
}

/**
 * Preload component
 */
export function preloadComponent(importFn: () => Promise<unknown>): void {
  importFn().catch((error) => {
    console.error('Failed to preload component:', error);
  });
}

/**
 * Route-based code splitting helper
 */
export function createLazyRoute<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  fallback?: React.ReactNode
) {
  const LazyComponent = lazyLoadComponent(importFn);
  
  return (props: React.ComponentPropsWithoutRef<T>) => (
    <Suspense fallback={fallback || <div>Loading...</div>}>
      <LazyComponent {...(props as any)} />
    </Suspense>
  );
}

