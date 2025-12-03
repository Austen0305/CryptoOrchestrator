/**
 * Enhanced Error Display Component
 * Shows user-friendly error messages with actionable information
 */
import { AlertCircle, RefreshCw, XCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export interface ErrorDetails {
  message: string;
  details?: Record<string, any>;
  code?: string;
  field?: string;
}

export interface EnhancedErrorProps {
  error: Error | ErrorDetails | string;
  title?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  showDetails?: boolean;
}

/**
 * Extract user-friendly error message from various error formats
 */
function extractErrorMessage(error: Error | ErrorDetails | string): ErrorDetails {
  if (typeof error === 'string') {
    return { message: error };
  }

  if (error instanceof Error) {
    // Try to parse API error response
    try {
      const apiError = JSON.parse(error.message);
      if (apiError.detail) {
        if (typeof apiError.detail === 'string') {
          return { message: apiError.detail };
        }
        if (apiError.detail.message) {
          return {
            message: apiError.detail.message,
            details: apiError.detail.details,
          };
        }
      }
    } catch {
      // Not JSON, use error message as-is
    }

    return { message: error.message };
  }

  return error;
}

/**
 * Enhanced error display with actionable information
 */
export function EnhancedError({
  error,
  title = "Error",
  onRetry,
  onDismiss,
  showDetails = false,
}: EnhancedErrorProps) {
  const errorInfo = extractErrorMessage(error);

  return (
    <Alert variant="destructive" className="relative">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle className="font-semibold">{title}</AlertTitle>
      <AlertDescription className="mt-2">
        <div className="space-y-2">
          <p>{errorInfo.message}</p>

          {showDetails && errorInfo.details && (
            <div className="mt-3 p-3 bg-destructive/10 rounded-md border border-destructive/20">
              <div className="text-sm font-medium mb-2">Details:</div>
              <pre className="text-xs overflow-auto max-h-40">
                {JSON.stringify(errorInfo.details, null, 2)}
              </pre>
            </div>
          )}

          {errorInfo.field && (
            <p className="text-sm text-muted-foreground">
              Field: <code className="text-xs bg-muted px-1 py-0.5 rounded">{errorInfo.field}</code>
            </p>
          )}

          <div className="flex gap-2 mt-3">
            {onRetry && (
              <Button
                size="sm"
                variant="outline"
                onClick={onRetry}
                className="gap-2"
              >
                <RefreshCw className="h-3 w-3" />
                Try Again
              </Button>
            )}
            {onDismiss && (
              <Button
                size="sm"
                variant="ghost"
                onClick={onDismiss}
                className="gap-2"
              >
                <XCircle className="h-3 w-3" />
                Dismiss
              </Button>
            )}
          </div>
        </div>
      </AlertDescription>
    </Alert>
  );
}

/**
 * Inline error message for form fields
 */
export function InlineError({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-destructive mt-1">
      <AlertCircle className="h-3 w-3" />
      <span>{message}</span>
    </div>
  );
}

/**
 * Format common API errors into user-friendly messages
 */
export function formatApiError(error: any): string {
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    
    if (typeof detail === 'string') {
      return detail;
    }
    
    if (detail.message) {
      return detail.message;
    }
  }

  if (error.message) {
    return error.message;
  }

  return 'An unexpected error occurred. Please try again.';
}
