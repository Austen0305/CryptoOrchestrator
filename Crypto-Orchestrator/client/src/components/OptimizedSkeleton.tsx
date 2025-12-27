/**
 * Optimized Skeleton Component
 * Enhanced loading skeleton with better animations
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface OptimizedSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}

export function OptimizedSkeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  animation = 'pulse',
  style,
  ...props
}: OptimizedSkeletonProps) {
  const variantClasses = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-none',
    rounded: 'rounded-md',
  };

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-shimmer',
    none: '',
  };

  return (
    <div
      className={cn(
        'bg-muted',
        variantClasses[variant],
        animationClasses[animation],
        className
      )}
      style={{
        width: width || (variant === 'text' ? '100%' : undefined),
        height: height || (variant === 'text' ? '1em' : undefined),
        ...style,
      }}
      {...props}
    />
  );
}

/**
 * Skeleton group for multiple skeletons
 */
export function SkeletonGroup({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('space-y-2', className)}>
      {children}
    </div>
  );
}

