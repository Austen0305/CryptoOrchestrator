/**
 * Error Retry Component
 * Provides a consistent retry mechanism for failed operations
 */

import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorRetryProps {
  error: Error | string;
  onRetry?: () => void;
  title?: string;
  className?: string;
  variant?: "default" | "destructive" | "warning";
}

// Helper function to make error messages more user-friendly
function getUserFriendlyErrorMessage(error: Error | string): string {
  const rawMessage = typeof error === "string" ? error : error.message;
  
  // Map technical errors to user-friendly messages
  if (rawMessage.includes('Failed to fetch') || rawMessage.includes('NetworkError') || rawMessage.includes('Network request failed')) {
    return "Unable to connect to our servers. Please check your internet connection and try again.";
  }
  
  if (rawMessage.includes('timeout') || rawMessage.includes('timed out')) {
    return "The request took too long. Please check your connection and try again.";
  }
  
  if (rawMessage.includes('HTTP 401') || rawMessage.includes('Unauthorized')) {
    return "Your session has expired. Please refresh the page and log in again.";
  }
  
  if (rawMessage.includes('HTTP 403') || rawMessage.includes('Forbidden')) {
    return "You don't have permission to perform this action.";
  }
  
  if (rawMessage.includes('HTTP 404') || rawMessage.includes('Not Found')) {
    return "The requested resource could not be found.";
  }
  
  if (rawMessage.includes('HTTP 429') || rawMessage.includes('rate limit')) {
    return "Too many requests. Please wait a moment and try again.";
  }
  
  if (rawMessage.includes('HTTP 500') || rawMessage.includes('HTTP 503') || rawMessage.includes('Internal Server Error')) {
    return "Our servers are temporarily unavailable. Please try again in a few moments.";
  }
  
  // If the message is already user-friendly (short and doesn't contain technical jargon), use it
  if (rawMessage.length < 200 && !rawMessage.includes('Error:') && !rawMessage.includes('TypeError')) {
    return rawMessage;
  }
  
  // Default user-friendly message
  return "Something went wrong. Please try again, and if the problem persists, contact support.";
}

export function ErrorRetry({
  error,
  onRetry,
  title = "Something went wrong",
  className,
  variant = "destructive",
}: ErrorRetryProps) {
  const errorMessage = getUserFriendlyErrorMessage(error);

  return (
    <Alert variant={variant} className={cn("my-4", className)}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="flex items-center justify-between gap-4">
        <span className="flex-1">{errorMessage}</span>
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
      </AlertDescription>
    </Alert>
  );
}

