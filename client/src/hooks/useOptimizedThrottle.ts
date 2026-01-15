/**
 * Optimized Throttle Hook
 * Enhanced throttle for frequent events
 */

import { useRef, useCallback } from 'react';

export function useOptimizedThrottle<T extends (...args: any[]) => any>(
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

  return throttledCallback;
}

