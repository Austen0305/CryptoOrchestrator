/**
 * Optimized Debounce Hook
 * Enhanced debounce with immediate execution option
 */

import { useState, useEffect, useRef, useCallback } from 'react';

interface UseOptimizedDebounceOptions {
  delay: number;
  immediate?: boolean;
}

export function useOptimizedDebounce<T>(
  value: T,
  options: UseOptimizedDebounceOptions
): T {
  const { delay, immediate = false } = options;
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  const isFirstRun = useRef(true);

  useEffect(() => {
    if (immediate && isFirstRun.current) {
      setDebouncedValue(value);
      isFirstRun.current = false;
      return;
    }

    const handler = setTimeout(() => {
      setDebouncedValue(value);
      isFirstRun.current = false;
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay, immediate]);

  return debouncedValue;
}

/**
 * Debounced callback hook
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
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
