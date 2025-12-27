/**
 * Error Recovery Hook
 * Provides automatic retry with exponential backoff, offline error handling, and error state persistence
 */
import { useState, useCallback, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { formatError } from "@/lib/errorMessages";
import logger from "@/lib/logger";

interface RetryOptions {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  retryable?: (error: unknown) => boolean;
}

interface ErrorState {
  error: Error | null;
  retryCount: number;
  isRetrying: boolean;
  canRetry: boolean;
}

/**
 * Hook for error recovery with automatic retry
 */
export function useErrorRecovery<T>(
  operation: () => Promise<T>,
  options: RetryOptions = {}
) {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 30000,
    retryable = () => true,
  } = options;

  const [errorState, setErrorState] = useState<ErrorState>({
    error: null,
    retryCount: 0,
    isRetrying: false,
    canRetry: true,
  });

  const { toast } = useToast();

  const executeWithRetry = useCallback(async (): Promise<T | null> => {
    setErrorState({
      error: null,
      retryCount: 0,
      isRetrying: false,
      canRetry: true,
    });

    let attempt = 0;

    while (attempt <= maxRetries) {
      try {
        const result = await operation();
        
        // Success - reset error state
        if (attempt > 0) {
          setErrorState({
            error: null,
            retryCount: 0,
            isRetrying: false,
            canRetry: true,
          });
          
          toast({
            title: "Operation Successful",
            description: "The operation completed after retrying.",
          });
        }
        
        return result;
      } catch (error) {
        attempt++;
        
        // Check if error is retryable
        if (!retryable(error) || attempt > maxRetries) {
          const errorInfo = formatError(error);
          
          setErrorState({
            error: error instanceof Error ? error : new Error(String(error)),
            retryCount: attempt - 1,
            isRetrying: false,
            canRetry: false,
          });
          
          toast({
            title: "Operation Failed",
            description: errorInfo.message,
            variant: "destructive",
          });
          
          return null;
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(initialDelay * Math.pow(2, attempt - 1), maxDelay);
        
        setErrorState({
          error: error instanceof Error ? error : new Error(String(error)),
          retryCount: attempt - 1,
          isRetrying: true,
          canRetry: true,
        });

        // Wait before retry
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }

    return null;
  }, [operation, maxRetries, initialDelay, maxDelay, retryable, toast]);

  const retry = useCallback(async (): Promise<T | null> => {
    if (!errorState.canRetry || errorState.retryCount >= maxRetries) {
      return null;
    }

    return executeWithRetry();
  }, [errorState, maxRetries, executeWithRetry]);

  return {
    execute: executeWithRetry,
    retry,
    error: errorState.error,
    retryCount: errorState.retryCount,
    isRetrying: errorState.isRetrying,
    canRetry: errorState.canRetry && errorState.retryCount < maxRetries,
  };
}

/**
 * Hook for offline error handling
 */
export function useOfflineErrorHandling() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true
  );

  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return {
    isOnline,
    isOffline: !isOnline,
  };
}

/**
 * Hook for error state persistence (localStorage)
 */
export function useErrorStatePersistence(key: string) {
  const [errorState, setErrorState] = useState<ErrorState | null>(null);

  useEffect(() => {
    // Load error state from localStorage on mount
    try {
      const stored = localStorage.getItem(`error_state_${key}`);
      if (stored) {
        const parsed = JSON.parse(stored);
        setErrorState(parsed);
      }
    } catch (e) {
      logger.error("Failed to load error state from localStorage", { error: e, key });
    }
  }, [key]);

  const saveErrorState = useCallback(
    (state: ErrorState) => {
      try {
        localStorage.setItem(`error_state_${key}`, JSON.stringify(state));
        setErrorState(state);
      } catch (e) {
        logger.error("Failed to save error state to localStorage", { error: e, key });
      }
    },
    [key]
  );

  const clearErrorState = useCallback(() => {
    try {
      localStorage.removeItem(`error_state_${key}`);
      setErrorState(null);
    } catch (e) {
      logger.error("Failed to clear error state from localStorage", { error: e, key });
    }
  }, [key]);

  return {
    errorState,
    saveErrorState,
    clearErrorState,
  };
}
