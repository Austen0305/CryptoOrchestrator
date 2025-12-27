/**
 * Error Retry Component
 * Provides a consistent retry mechanism for failed operations
 */

import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, RefreshCw, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatError } from "@/lib/errorMessages";

interface ErrorRetryProps {
  error: Error | string | unknown;
  onRetry?: () => void;
  title?: string;
  message?: string; // Deprecated: use title instead
  className?: string;
  variant?: "default" | "destructive" | "warning";
  showRecoveryAction?: boolean;
}

export function ErrorRetry({
  error,
  onRetry,
  title,
  message,
  className,
  variant = "destructive",
  showRecoveryAction = true,
}: ErrorRetryProps) {
  const errorInfo = formatError(error);
  const displayTitle = title || message || errorInfo.message;
  // Map "warning" to "default" since Alert doesn't support warning
  const alertVariant = variant === "warning" ? "default" : variant;

  return (
    <Alert variant={alertVariant} className={cn("my-4", className)}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{displayTitle}</AlertTitle>
      <AlertDescription className="space-y-2">
        <div className="flex items-center justify-between gap-4">
          <span className="flex-1">{errorInfo.message}</span>
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="shrink-0"
              aria-label="Retry the operation"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          )}
        </div>
        {showRecoveryAction && errorInfo.recoveryAction && (
          <div className="flex items-start gap-2 pt-2 border-t">
            <HelpCircle className="h-4 w-4 mt-0.5 text-muted-foreground" />
            <div className="flex-1">
              <p className="text-sm font-medium text-muted-foreground">What you can do:</p>
              <p className="text-sm text-muted-foreground">{errorInfo.recoveryAction}</p>
            </div>
          </div>
        )}
        {errorInfo.supportContact && (
          <div className="text-xs text-muted-foreground pt-1">
            Need help? Contact support for assistance.
          </div>
        )}
      </AlertDescription>
    </Alert>
  );
}

