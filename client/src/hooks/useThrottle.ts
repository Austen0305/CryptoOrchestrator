/**
 * Throttle Hook
 * Limits execution of a function to at most once per specified time period
 */

import { useRef, useCallback } from 'react';

export function useThrottle<T extends (...args: unknown[]) => any>(
  func: T,
  delay: number
): T {
  const lastRunRef = useRef<number>(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const throttledCallback = useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now();
      
      if (now - lastRunRef.current >= delay) {
        lastRunRef.current = now;
        func(...args);
      } else {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        
        timeoutRef.current = setTimeout(() => {
          lastRunRef.current = Date.now();
          func(...args);
        }, delay - (now - lastRunRef.current));
      }
    }) as T,
    [func, delay]
  );

  return throttledCallback;
}

