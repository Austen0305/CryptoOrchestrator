/**
 * Throttle Hook
 * Limits execution of a function to at most once per specified time period
 */

import { useRef, useCallback } from 'react';

export function useThrottle<T extends (...args: unknown[]) => any>(
  func: T,
  delay: number = 500
): T {
  const lastRun = useRef<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  return useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now();
      
      if (now - lastRun.current >= delay) {
        lastRun.current = now;
        func(...args);
      } else {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        
        timeoutRef.current = setTimeout(() => {
          lastRun.current = Date.now();
          func(...args);
        }, delay - (now - lastRun.current));
      }
    }) as T,
    [func, delay]
  );
}

