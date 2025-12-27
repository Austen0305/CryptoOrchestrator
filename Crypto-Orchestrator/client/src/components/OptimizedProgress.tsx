/**
 * Optimized Progress Component
 * Enhanced progress bar with animations
 */

import React from 'react';
import { Progress } from './ui/progress';
import { cn } from '@/lib/utils';

interface OptimizedProgressProps {
  value: number;
  max?: number;
  showLabel?: boolean;
  label?: string;
  variant?: 'default' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  animated?: boolean;
}

const variantClasses = {
  default: '',
  success: '[&>div]:bg-green-500',
  warning: '[&>div]:bg-yellow-500',
  error: '[&>div]:bg-red-500',
};

const sizeClasses = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-4',
};

export function OptimizedProgress({
  value,
  max = 100,
  showLabel = false,
  label,
  variant = 'default',
  size = 'md',
  className,
  animated = true,
}: OptimizedProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={cn('w-full space-y-2', className)}>
      {(showLabel || label) && (
        <div className="flex justify-between items-center text-sm">
          <span className="text-muted-foreground">{label || 'Progress'}</span>
          <span className="font-medium">{Math.round(percentage)}%</span>
        </div>
      )}
      <Progress
        value={percentage}
        className={cn(
          sizeClasses[size],
          variantClasses[variant],
          animated && 'transition-all duration-300'
        )}
      />
    </div>
  );
}

