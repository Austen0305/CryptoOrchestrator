/**
 * Optimized Chart Component
 * High-performance chart wrapper with lazy loading
 */

import React, { Suspense, lazy } from 'react';
import { LoadingSkeleton } from './LoadingSkeleton';

// Lazy load chart library
const ChartComponent = lazy(() =>
  import('recharts').then((module) => ({
    default: ({ children, ...props }: React.ComponentPropsWithoutRef<typeof module.LineChart>) => (
      <module.LineChart {...props}>{children}</module.LineChart>
    ),
  }))
);

interface OptimizedChartProps {
  data: Array<Record<string, unknown>>;
  dataKey: string;
  children: React.ReactNode;
  height?: number;
  className?: string;
}

export function OptimizedChart({
  data,
  dataKey,
  children,
  height = 300,
  className,
}: OptimizedChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        No data available
      </div>
    );
  }

  return (
    <Suspense fallback={<LoadingSkeleton variant="chart" className="h-full" />}>
      <div className={className} style={{ height }}>
        <ChartComponent data={data} height={height}>
          {children}
        </ChartComponent>
      </div>
    </Suspense>
  );
}
