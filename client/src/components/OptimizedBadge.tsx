/**
 * Optimized Badge Component
 * High-performance badge with variants
 */

import React from 'react';
import { Badge } from './ui/badge';
import { cn } from '@/lib/utils';

interface OptimizedBadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const variantClasses = {
  default: 'bg-primary text-primary-foreground',
  success: 'bg-green-500 text-white',
  warning: 'bg-yellow-500 text-white',
  error: 'bg-red-500 text-white',
  info: 'bg-blue-500 text-white',
};

const sizeClasses = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-1',
  lg: 'text-base px-3 py-1.5',
};

export const OptimizedBadge = React.memo(function OptimizedBadge({
  children,
  variant = 'default',
  size = 'md',
  className,
}: OptimizedBadgeProps) {
  return (
    <Badge
      className={cn(variantClasses[variant], sizeClasses[size], className)}
    >
      {children}
    </Badge>
  );
});
