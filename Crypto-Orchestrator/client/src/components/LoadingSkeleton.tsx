/**
 * Loading Skeleton Component
 * Various skeleton loading states
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingSkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular' | 'card' | 'table' | 'chart' | 'list' | 'dashboard';
  className?: string;
  width?: string | number;
  height?: string | number;
  lines?: number;
  count?: number;
}

export function LoadingSkeleton({
  variant = 'rectangular',
  className,
  width,
  height,
  lines = 3,
  count,
}: LoadingSkeletonProps) {
  const baseClasses = 'animate-pulse bg-muted rounded';
  const itemCount = count || lines;

  if (variant === 'text') {
    return (
      <div className={cn('space-y-2', className)}>
        {Array.from({ length: itemCount }).map((_, i) => (
          <div
            key={i}
            className={cn(baseClasses, 'h-4')}
            style={{
              width: i === itemCount - 1 ? '60%' : '100%',
            }}
          />
        ))}
      </div>
    );
  }

  if (variant === 'circular') {
    return (
      <div
        className={cn(baseClasses, 'rounded-full', className)}
        style={{ width: width || 40, height: height || 40 }}
      />
    );
  }

  if (variant === 'card') {
    return (
      <div className={cn('space-y-4 p-4 border rounded-lg', className)}>
        <div className={cn(baseClasses, 'h-6 w-3/4')} />
        <div className={cn(baseClasses, 'h-4 w-full')} />
        <div className={cn(baseClasses, 'h-4 w-5/6')} />
      </div>
    );
  }

  if (variant === 'table') {
    return (
      <div className={cn('space-y-2', className)}>
        {Array.from({ length: itemCount }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <div className={cn(baseClasses, 'h-4 flex-1')} />
            <div className={cn(baseClasses, 'h-4 w-24')} />
            <div className={cn(baseClasses, 'h-4 w-32')} />
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'chart') {
    return (
      <div className={cn('space-y-2', className)}>
        <div className={cn(baseClasses, 'h-6 w-1/3')} />
        <div className={cn(baseClasses, 'h-48 w-full')} />
      </div>
    );
  }

  if (variant === 'list') {
    return (
      <div className={cn('space-y-3', className)}>
        {Array.from({ length: itemCount }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className={cn(baseClasses, 'h-10 w-10 rounded-full')} />
            <div className="flex-1 space-y-2">
              <div className={cn(baseClasses, 'h-4 w-3/4')} />
              <div className={cn(baseClasses, 'h-3 w-1/2')} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'dashboard') {
    return (
      <div className={cn('space-y-4', className)}>
        <div className={cn(baseClasses, 'h-8 w-1/3')} />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className={cn(baseClasses, 'h-24')} />
          ))}
        </div>
        <div className={cn(baseClasses, 'h-64')} />
      </div>
    );
  }

  // rectangular (default)
  return (
    <div
      className={cn(baseClasses, className)}
      style={{ width: width || '100%', height: height || 20 }}
    />
  );
}
