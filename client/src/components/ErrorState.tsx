/**
 * Error State Component
 * Provides consistent, helpful error states throughout the application
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, RefreshCw, Home, ArrowLeft, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  title?: string;
  message: string;
  error?: Error | string;
  onRetry?: () => void;
  onGoHome?: () => void;
  onGoBack?: () => void;
  showDetails?: boolean;
  className?: string;
  severity?: "error" | "warning" | "info";
}

export function ErrorState({
  title = "Something went wrong",
  message,
  error,
  onRetry,
  onGoHome,
  onGoBack,
  showDetails = false,
  className,
  severity = "error",
}: ErrorStateProps) {
  const errorMessage = error instanceof Error ? error.message : error || message;
  const isError = severity === "error";
  const isWarning = severity === "warning";

  return (
    <Card className={cn("border-destructive/50", className)}>
      <CardHeader>
        <div className="flex items-center gap-2">
          {isError && <AlertCircle className="h-5 w-5 text-destructive" />}
          {isWarning && <AlertCircle className="h-5 w-5 text-yellow-500" />}
          {!isError && !isWarning && <HelpCircle className="h-5 w-5 text-blue-500" />}
          <CardTitle>{title}</CardTitle>
        </div>
        <CardDescription>{message}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {showDetails && errorMessage && (
          <Alert variant={isError ? "destructive" : "default"}>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="font-mono text-xs">
              {errorMessage}
            </AlertDescription>
          </Alert>
        )}
        <div className="flex gap-2 flex-wrap">
          {onRetry && (
            <Button onClick={onRetry} variant="default" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          )}
          {onGoBack && (
            <Button onClick={onGoBack} variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
          )}
          {onGoHome && (
            <Button onClick={onGoHome} variant="outline" size="sm">
              <Home className="h-4 w-4 mr-2" />
              Go Home
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Pre-configured error states for common scenarios
 */
export function NetworkErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorState
      title="Connection Error"
      message="Unable to connect to the server. Please check your internet connection and try again."
      onRetry={onRetry}
      severity="error"
    />
  );
}

export function NotFoundErrorState({ onGoHome }: { onGoHome?: () => void }) {
  return (
    <ErrorState
      title="Not Found"
      message="The page or resource you're looking for doesn't exist."
      onGoHome={onGoHome}
      severity="warning"
    />
  );
}

export function UnauthorizedErrorState({ onGoHome }: { onGoHome?: () => void }) {
  return (
    <ErrorState
      title="Access Denied"
      message="You don't have permission to access this resource. Please log in or contact support."
      onGoHome={onGoHome}
      severity="warning"
    />
  );
}

export function ServerErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorState
      title="Server Error"
      message="The server encountered an error. Please try again in a moment."
      onRetry={onRetry}
      showDetails={false}
      severity="error"
    />
  );
}

