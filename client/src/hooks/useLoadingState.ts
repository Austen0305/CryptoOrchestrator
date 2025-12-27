/**
 * Loading state management utilities
 * Provides consistent loading indicators across the application
 */
import { useState, useCallback } from 'react';

export interface LoadingState {
  isLoading: boolean;
  startLoading: () => void;
  stopLoading: () => void;
  withLoading: <T>(fn: () => Promise<T>) => Promise<T>;
}

/**
 * Hook for managing loading state
 * 
 * Usage:
 *   const { isLoading, withLoading } = useLoadingState();
 *   
 *   const handleSubmit = async () => {
 *     await withLoading(async () => {
 *       await createBot(data);
 *     });
 *   };
 */
export function useLoadingState(initialState: boolean = false): LoadingState {
  const [isLoading, setIsLoading] = useState(initialState);

  const startLoading = useCallback(() => {
    setIsLoading(true);
  }, []);

  const stopLoading = useCallback(() => {
    setIsLoading(false);
  }, []);

  const withLoading = useCallback(async <T,>(fn: () => Promise<T>): Promise<T> => {
    startLoading();
    try {
      return await fn();
    } finally {
      stopLoading();
    }
  }, [startLoading, stopLoading]);

  return {
    isLoading,
    startLoading,
    stopLoading,
    withLoading,
  };
}

/**
 * Hook for managing multiple loading states
 * 
 * Usage:
 *   const { isLoading, setLoading } = useMultiLoadingState();
 *   
 *   const handleCreate = async () => {
 *     setLoading('create', true);
 *     try {
 *       await createBot(data);
 *     } finally {
 *       setLoading('create', false);
 *     }
 *   };
 */
export function useMultiLoadingState() {
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});

  const setLoading = useCallback((key: string, loading: boolean) => {
    setLoadingStates(prev => ({
      ...prev,
      [key]: loading,
    }));
  }, []);

  const isLoading = useCallback((key: string) => {
    return loadingStates[key] || false;
  }, [loadingStates]);

  const isAnyLoading = useCallback(() => {
    return Object.values(loadingStates).some(state => state);
  }, [loadingStates]);

  return {
    isLoading,
    setLoading,
    isAnyLoading,
    loadingStates,
  };
}

/**
 * Minimum loading time to prevent flashing
 * Ensures loading indicator shows for at least the specified duration
 */
export async function withMinimumLoadingTime<T>(
  fn: () => Promise<T>,
  minimumMs: number = 300
): Promise<T> {
  const startTime = Date.now();
  const result = await fn();
  const elapsed = Date.now() - startTime;
  
  if (elapsed < minimumMs) {
    await new Promise(resolve => setTimeout(resolve, minimumMs - elapsed));
  }
  
  return result;
}
