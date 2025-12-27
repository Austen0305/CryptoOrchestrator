/**
 * Optimized Suspense Component
 * Enhanced Suspense with better loading states and error handling
 */

import React, { Suspense, ReactNode } from 'react';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { OptimizedErrorBoundary } from './OptimizedErrorBoundary';

interface OptimizedSuspenseProps {
  children: ReactNode;
  fallback?: ReactNode;
  errorFallback?: ReactNode;
  showErrorDetails?: boolean;
}

export function OptimizedSuspense({
  children,
  fallback,
  errorFallback,
  showErrorDetails = false,
}: OptimizedSuspenseProps) {
  const defaultFallback = (
    <div className="flex items-center justify-center p-8">
      <LoadingSkeleton className="w-full max-w-md" />
    </div>
  );

  return (
    <OptimizedErrorBoundary fallback={errorFallback} showDetails={showErrorDetails}>
      <Suspense fallback={fallback || defaultFallback}>{children}</Suspense>
    </OptimizedErrorBoundary>
  );
}

