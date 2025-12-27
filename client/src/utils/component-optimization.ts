/**
 * Component Optimization Utilities
 * Helpers for optimizing React component performance
 */

import React from 'react';

/**
 * Memoize component with deep comparison
 */
export function memoWithDeepCompare<T extends React.ComponentType<any>>(
  Component: T
): React.MemoExoticComponent<T> {
  return React.memo(Component, (prevProps, nextProps) => {
    return JSON.stringify(prevProps) === JSON.stringify(nextProps);
  });
}

/**
 * Lazy load component with retry
 */
export function lazyLoadWithRetry<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  retries = 3
): React.LazyExoticComponent<T> {
  return React.lazy(async () => {
    let lastError: Error | null = null;

    for (let i = 0; i < retries; i++) {
      try {
        return await importFn();
      } catch (error) {
        lastError = error as Error;
        if (i < retries - 1) {
          await new Promise((resolve) => setTimeout(resolve, 1000 * (i + 1)));
        }
      }
    }

    throw lastError || new Error('Failed to load component');
  });
}

/**
 * Preload component
 */
export function preloadComponent(importFn: () => Promise<unknown>): void {
  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.as = 'script';
  
  importFn().catch((error) => {
    console.error('Failed to preload component:', error);
  });
}

/**
 * Check if component should re-render
 */
export function shouldUpdate<T extends Record<string, unknown>>(
  prevProps: T,
  nextProps: T,
  keys: (keyof T)[]
): boolean {
  return keys.some((key) => prevProps[key] !== nextProps[key]);
}

