/**
 * Error Handling Utilities
 * Centralized error handling for the frontend
 */

import { toast } from '@/hooks/use-toast';

export interface AppError {
  message: string;
  code?: string;
  statusCode?: number;
  details?: unknown;
}

/**
 * Extract error message from various error types
 */
export function extractErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  if (error && typeof error === 'object' && 'message' in error) {
    return String(error.message);
  }
  return 'An unexpected error occurred';
}

/**
 * Extract error code from error
 */
export function extractErrorCode(error: unknown): string | null {
  if (error && typeof error === 'object') {
    if ('code' in error) {
      return String(error.code);
    }
    if ('error' in error && typeof error.error === 'object' && error.error && 'code' in error.error) {
      return String(error.error.code);
    }
  }
  return null;
}

/**
 * Handle API errors consistently
 */
export function handleApiError(error: unknown, context?: string): AppError {
  const message = extractErrorMessage(error);
  const code = extractErrorCode(error);

  let statusCode: number | undefined;
  if (error && typeof error === 'object' && 'status' in error) {
    statusCode = Number(error.status);
  }

  const appError: AppError = {
    message,
    code: code || undefined,
    statusCode,
    details: error,
  };

  // Log error in development
  if (import.meta.env.DEV) {
    console.error(`[Error] ${context || 'API'}:`, appError);
  }

  return appError;
}

/**
 * Show error toast notification
 */
export function showErrorToast(error: unknown, context?: string): void {
  const appError = handleApiError(error, context);
  
  toast({
    title: 'Error',
    description: appError.message,
    variant: 'destructive',
  });
}

/**
 * Handle error with retry option
 */
export function handleErrorWithRetry(
  error: unknown,
  retryFn: () => void,
  context?: string
): void {
  const appError = handleApiError(error, context);
  
  toast({
    title: 'Error',
    description: appError.message,
    variant: 'destructive',
    action: (
      <button
        onClick={retryFn}
        className="text-sm font-medium underline"
      >
        Retry
      </button>
    ),
  });
}

/**
 * Error boundary error formatter
 */
export function formatErrorForBoundary(error: Error, errorInfo: React.ErrorInfo): string {
  return `
Error: ${error.message}
Stack: ${error.stack}
Component Stack: ${errorInfo.componentStack}
  `.trim();
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: unknown): boolean {
  if (error && typeof error === 'object') {
    if ('message' in error) {
      const message = String(error.message).toLowerCase();
      return (
        message.includes('network') ||
        message.includes('fetch') ||
        message.includes('connection') ||
        message.includes('timeout')
      );
    }
  }
  return false;
}

/**
 * Check if error is an authentication error
 */
export function isAuthError(error: unknown): boolean {
  if (error && typeof error === 'object' && 'status' in error) {
    const status = Number(error.status);
    return status === 401 || status === 403;
  }
  return false;
}

