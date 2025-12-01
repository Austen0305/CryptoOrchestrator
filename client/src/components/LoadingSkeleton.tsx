/**
 * Loading Skeleton Component
 * Provides consistent loading states across the application
 */

import { cn } from "@/lib/utils";

interface LoadingSkeletonProps {
  className?: string;
  variant?: 'default' | 'card' | 'table' | 'chart' | 'text';
  count?: number;
}

export function LoadingSkeleton({ 
  className, 
  variant = 'default',
  count = 1 
}: LoadingSkeletonProps) {
  const baseClasses = "animate-pulse bg-muted rounded loading-shimmer relative overflow-hidden";

  const variants = {
    default: "h-4 w-full",
    card: "h-32 w-full",
    table: "h-12 w-full",
    chart: "h-64 w-full",
    text: "h-4 w-3/4",
  };

  if (count > 1) {
    return (
      <div className={cn("space-y-2", className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className={cn(baseClasses, variants[variant])}
            aria-label="Loading"
            role="status"
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(baseClasses, variants[variant], className)}
      aria-label="Loading"
      role="status"
    >
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </div>
  );
}

/**
 * Card Skeleton - For card-based layouts
 */
export function CardSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-6 space-y-4" role="status" aria-label="Loading card">
      <LoadingSkeleton variant="text" className="h-6" />
      <LoadingSkeleton variant="default" count={3} />
      <LoadingSkeleton variant="card" className="h-32" />
    </div>
  );
}

/**
 * Table Skeleton - For table layouts
 */
export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-2" role="status" aria-label="Loading table">
      {/* Header */}
      <div className="flex gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <LoadingSkeleton key={i} variant="text" className="h-6 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: cols }).map((_, j) => (
            <LoadingSkeleton key={j} variant="default" className="flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * Chart Skeleton - For chart components
 */
export function ChartSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-6 space-y-4" role="status" aria-label="Loading chart">
      <LoadingSkeleton variant="text" className="h-6 w-1/3" />
      <LoadingSkeleton variant="chart" />
      <div className="flex gap-4">
        <LoadingSkeleton variant="text" className="h-4 w-1/4" />
        <LoadingSkeleton variant="text" className="h-4 w-1/4" />
        <LoadingSkeleton variant="text" className="h-4 w-1/4" />
      </div>
    </div>
  );
}

