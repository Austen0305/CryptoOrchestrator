/**
 * Performance Utilities
 * Utilities for optimizing React component performance
 */

import React, { useCallback, useMemo, useRef, useEffect, useState, DependencyList } from 'react';

/**
 * Debounce hook for expensive operations
 */
export function useDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    },
    [callback, delay]
  ) as T;

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedCallback;
}

/**
 * Throttle hook for frequent events
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const lastRunRef = useRef<number>(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const throttledCallback = useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now();
      const timeSinceLastRun = now - lastRunRef.current;

      if (timeSinceLastRun >= delay) {
        lastRunRef.current = now;
        callback(...args);
      } else {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        timeoutRef.current = setTimeout(() => {
          lastRunRef.current = Date.now();
          callback(...args);
        }, delay - timeSinceLastRun);
      }
    },
    [callback, delay]
  ) as T;

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return throttledCallback;
}

/**
 * Memoize expensive computations
 */
export function useMemoizedValue<T>(
  computeFn: () => T,
  deps: React.DependencyList
): T {
  return useMemo(computeFn, deps);
}

/**
 * Stable callback reference
 */
export function useStableCallback<T extends (...args: any[]) => any>(
  callback: T
): T {
  return useCallback(callback, []);
}

/**
 * Performance monitoring hook
 */
export function usePerformanceMonitor(componentName: string) {
  const renderCountRef = useRef(0);
  const mountTimeRef = useRef<number | null>(null);

  useEffect(() => {
    mountTimeRef.current = performance.now();
    return () => {
      if (mountTimeRef.current) {
        const unmountTime = performance.now();
        const lifetime = unmountTime - mountTimeRef.current;
        if (import.meta.env.DEV) {
          console.log(
            `[Performance] ${componentName} lifetime: ${lifetime.toFixed(2)}ms, renders: ${renderCountRef.current}`
          );
        }
      }
    };
  }, [componentName]);

  useEffect(() => {
    renderCountRef.current += 1;
    if (import.meta.env.DEV && renderCountRef.current > 10) {
      console.warn(
        `[Performance] ${componentName} has rendered ${renderCountRef.current} times. Consider optimization.`
      );
    }
  });
}


/**
 * Virtual scrolling helper
 */
export function useVirtualScroll<T>(
  items: T[],
  itemHeight: number,
  containerHeight: number
) {
  const [scrollTop, setScrollTop] = React.useState(0);

  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(
    startIndex + Math.ceil(containerHeight / itemHeight) + 1,
    items.length
  );

  const visibleItems = useMemo(
    () => items.slice(startIndex, endIndex),
    [items, startIndex, endIndex]
  );

  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
  };
}

/**
 * Debounce function for non-hook usage
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Deduplicate concurrent requests
 */
const pendingRequests = new Map<string, Promise<any>>();

export function deduplicateRequest<T>(
  key: string,
  requestFn: () => Promise<T>
): Promise<T> {
  if (pendingRequests.has(key)) {
    return pendingRequests.get(key)!;
  }

  const promise = requestFn().finally(() => {
    pendingRequests.delete(key);
  });

  pendingRequests.set(key, promise);
  return promise;
}
