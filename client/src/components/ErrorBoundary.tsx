import React, { Component, ErrorInfo, ReactNode } from 'react';
import logger from '@/lib/logger';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { AlertCircle, RefreshCw, Home, Bug } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to our logging system
    logger.error('React Error Boundary caught an error', {
      error: error.toString(),
      errorInfo,
      componentStack: errorInfo.componentStack,
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
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  private handleReportIssue = () => {
    const errorDetails = encodeURIComponent(
      `Error: ${this.state.error?.message}\n\nStack: ${this.state.error?.stack}`
    );
    window.open(
      `https://github.com/Austen0305/Kraken-autobot/issues/new?title=Error%20Report&body=${errorDetails}`,
      '_blank'
    );
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex items-center justify-center min-h-screen bg-background p-4">
          <Card className="max-w-2xl w-full">
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                <div className="p-3 rounded-full bg-destructive/10">
                  <AlertCircle className="h-12 w-12 text-destructive" />
                </div>
              </div>
              <CardTitle className="text-2xl">Oops! Something went wrong</CardTitle>
              <CardDescription>
                Don't worry, your data is safe. Try one of the options below to continue.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Error Message */}
              <div className="p-4 rounded-lg bg-muted">
                <p className="text-sm font-mono text-center">
                  {this.state.error?.message || 'An unexpected error occurred'}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Button onClick={this.handleReset} variant="outline" className="w-full gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Try Again
                </Button>
                <Button onClick={this.handleGoHome} variant="default" className="w-full gap-2">
                  <Home className="h-4 w-4" />
                  Go Home
                </Button>
                <Button onClick={this.handleReload} variant="secondary" className="w-full gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Reload Page
                </Button>
              </div>

              {/* Report Issue Button */}
              <div className="text-center">
                <Button 
                  onClick={this.handleReportIssue} 
                  variant="ghost" 
                  size="sm"
                  className="gap-2"
                >
                  <Bug className="h-4 w-4" />
                  Report this issue on GitHub
                </Button>
              </div>

              {/* Developer Details */}
              {import.meta.env?.DEV && this.state.error && (
                <details className="text-left">
                  <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground mb-2">
                    🔧 Developer Details
                  </summary>
                  <div className="space-y-2">
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-1">Error Message:</p>
                      <pre className="p-3 bg-muted rounded text-xs overflow-auto">
                        {this.state.error.message}
                      </pre>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground mb-1">Stack Trace:</p>
                      <pre className="p-3 bg-muted rounded text-xs overflow-auto max-h-48">
                        {this.state.error.stack}
                      </pre>
                    </div>
                  </div>
                </details>
              )}

              {/* Help Text */}
              <p className="text-xs text-center text-muted-foreground">
                If this problem persists, please check the{' '}
                <a href="/docs/troubleshooting" className="underline hover:text-foreground">
                  troubleshooting guide
                </a>{' '}
                or contact support.
              </p>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Declare Sentry on window
declare global {
  interface Window {
    Sentry?: {
      captureException: (error: Error, context?: any) => void;
    };
  }
}
