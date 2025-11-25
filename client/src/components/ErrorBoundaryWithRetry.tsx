import React, { Component, ErrorInfo, ReactNode } from 'react';
import logger from '@/lib/logger';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { AlertCircle, RefreshCw, Home, Bug } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
  showDetails?: boolean;
  className?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
}

export class ErrorBoundaryWithRetry extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
    retryCount: 0,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to our logging system
    logger.error('React Error Boundary caught an error', {
      error: error.toString(),
      errorInfo,
      componentStack: errorInfo.componentStack,
      retryCount: this.state.retryCount,
    });

    // If Sentry is configured, report to it
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack,
          },
        },
      });
    }

    this.setState({ errorInfo });
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: this.state.retryCount + 1,
    });
    
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, errorInfo, retryCount } = this.state;
      const maxRetries = 3;

      return (
        <div className={cn("flex items-center justify-center min-h-[400px] p-4", this.props.className)}>
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-destructive" />
                <CardTitle>Something went wrong</CardTitle>
              </div>
              <CardDescription>
                An error occurred while rendering this component.
                {retryCount >= maxRetries && " Maximum retry attempts reached."}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {this.props.showDetails && error && (
                <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4">
                  <div className="font-mono text-sm text-destructive break-words">
                    {error.toString()}
                  </div>
                  {errorInfo && errorInfo.componentStack && (
                    <details className="mt-2">
                      <summary className="text-sm cursor-pointer text-muted-foreground">
                        Component Stack
                      </summary>
                      <pre className="mt-2 text-xs overflow-auto max-h-40 bg-background p-2 rounded border">
                        {errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                {retryCount < maxRetries && (
                  <Button onClick={this.handleReset} variant="default">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Retry ({retryCount}/{maxRetries})
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
              </div>

              {retryCount >= maxRetries && (
                <div className="rounded-md border border-yellow-500/50 bg-yellow-500/10 p-3">
                  <p className="text-sm text-yellow-700 dark:text-yellow-400">
                    Maximum retry attempts reached. Please reload the page or contact support if the issue persists.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

