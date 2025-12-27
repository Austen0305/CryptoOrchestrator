/**
 * Optimized Loading Component
 * Enhanced loading states with better UX
 */

import React from 'react';
import { LoadingSkeleton } from './LoadingSkeleton';
import { Card, CardContent } from './ui/card';
import { Loader2 } from 'lucide-react';

interface OptimizedLoadingProps {
  message?: string;
  fullScreen?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'skeleton' | 'dots';
}

export function OptimizedLoading({
  message = 'Loading...',
  fullScreen = false,
  size = 'md',
  variant = 'spinner',
}: OptimizedLoadingProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  if (fullScreen) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          {variant === 'spinner' && (
            <Loader2 className={`${sizeClasses[size]} animate-spin text-primary`} />
          )}
          {variant === 'dots' && (
            <div className="flex gap-2">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className={`${sizeClasses[size]} rounded-full bg-primary animate-pulse`}
                  style={{ animationDelay: `${i * 0.2}s` }}
                />
              ))}
            </div>
          )}
          <p className="text-sm text-muted-foreground">{message}</p>
        </div>
      </div>
    );
  }

  if (variant === 'skeleton') {
    return <LoadingSkeleton />;
  }

  return (
    <div className="flex items-center justify-center p-8">
      <div className="flex flex-col items-center gap-2">
        {variant === 'spinner' && (
          <Loader2 className={`${sizeClasses[size]} animate-spin text-primary`} />
        )}
        {variant === 'dots' && (
          <div className="flex gap-2">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className={`${sizeClasses[size]} rounded-full bg-primary animate-pulse`}
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </div>
        )}
        <p className="text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  );
}

/**
 * Loading overlay component
 */
export function LoadingOverlay({ message, show }: { message?: string; show: boolean }) {
  if (!show) return null;

  return (
    <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
      <OptimizedLoading message={message} variant="spinner" />
    </div>
  );
}

