/**
 * Enhanced Error Boundary Component
 * Provides comprehensive error handling with recovery options, error reporting, and user-friendly UI
 */

import React, { Component, ErrorInfo, ReactNode } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw, Home, Bug, X } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import logger from "@/lib/logger";
import { classifyError, logError, getUserFriendlyMessage, formatErrorForDisplay } from "@/utils/errorHandling2026";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  resetKeys?: Array<string | number>;
  resetOnPropsChange?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
  retryCount: number;
}

const MAX_RETRIES = 3;

export class EnhancedErrorBoundary extends Component<Props, State> {
  private resetTimeoutId: number | null = null;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const errorCount = this.state.errorCount + 1;
    this.setState({ errorInfo, errorCount });

    // Log error
    logger.error("EnhancedErrorBoundary caught an error", { error, errorInfo });

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Report to error tracking service (e.g., Sentry)
    interface WindowWithSentry extends Window {
      Sentry?: {
        captureException: (error: Error, context?: { contexts?: { react?: ErrorInfo }; tags?: Record<string, boolean> }) => void;
      };
    }
    const windowWithSentry = typeof window !== "undefined" ? window as WindowWithSentry : null;
    if (windowWithSentry?.Sentry) {
      windowWithSentry.Sentry.captureException(error, {
        contexts: { react: errorInfo },
        tags: { errorBoundary: true },
      });
    }
  }

  override componentDidUpdate(prevProps: Props) {
    const { resetKeys, resetOnPropsChange } = this.props;
    const { hasError } = this.state;

    if (hasError && resetOnPropsChange) {
      if (resetKeys && resetKeys.some((key, index) => key !== prevProps.resetKeys?.[index])) {
        this.resetErrorBoundary();
      }
    }
  }

  override componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  resetErrorBoundary = () => {
    if (this.state.retryCount >= MAX_RETRIES) {
      return;
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: this.state.retryCount + 1,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = "/";
  };

  handleDismiss = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  override render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, errorInfo, retryCount, errorCount } = this.state;
      const canRetry = retryCount < MAX_RETRIES;
      const showDetails = this.props.showDetails ?? (process.env.NODE_ENV === "development");

      return (
        <div className="flex items-center justify-center min-h-[400px] p-4">
          <Card className="w-full max-w-2xl border-destructive/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-destructive" />
                  <CardTitle>Something went wrong</CardTitle>
                </div>
                {!canRetry && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={this.handleDismiss}
                    className="h-8 w-8"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
              <CardDescription>
                An error occurred while rendering this component.
                {!canRetry && " Maximum retry attempts reached."}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Error Details</AlertTitle>
                <AlertDescription>
                  {error ? getUserFriendlyMessage(error) : "An unexpected error occurred"}
                </AlertDescription>
              </Alert>

              {showDetails && error && (
                <div className="space-y-2">
                  <div className="p-3 bg-muted rounded-md">
                    <p className="text-sm font-mono text-muted-foreground break-all">
                      {error.message}
                    </p>
                  </div>
                  {errorInfo && (
                    <details className="p-3 bg-muted rounded-md">
                      <summary className="cursor-pointer text-sm font-semibold mb-2">
                        Stack Trace
                      </summary>
                      <pre className="text-xs font-mono text-muted-foreground overflow-auto max-h-48">
                        {errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                {canRetry && (
                  <Button onClick={this.resetErrorBoundary} variant="default">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Try Again ({retryCount}/{MAX_RETRIES})
                  </Button>
                )}
                <Button onClick={this.handleReload} variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reload Page
                </Button>
                <Button onClick={this.handleGoHome} variant="outline">
                  <Home className="h-4 w-4 mr-2" />
                  Go Home
                </Button>
                {showDetails && (
                  <Button
                    onClick={() => {
                      const errorReport = {
                        error: error?.message,
                        stack: error?.stack,
                        componentStack: errorInfo?.componentStack,
                        errorCount,
                        retryCount,
                        timestamp: new Date().toISOString(),
                      };
                      logger.error("Error Report", { errorReport });
                      // Could send to error tracking service
                    }}
                    variant="outline"
                  >
                    <Bug className="h-4 w-4 mr-2" />
                    Report Error
                  </Button>
                )}
              </div>

              {errorCount > 1 && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Multiple Errors Detected</AlertTitle>
                  <AlertDescription>
                    This error has occurred {errorCount} times. Consider refreshing the page.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

