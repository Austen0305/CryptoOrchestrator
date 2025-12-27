/**
 * Optimized Lazy Load Component
 * Lazy load content when it enters viewport
 */

import React from 'react';
import { useIntersectionObserver } from '@/hooks/useIntersectionObserver';
import { LoadingSkeleton } from './LoadingSkeleton';

interface OptimizedLazyLoadProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  rootMargin?: string;
  triggerOnce?: boolean;
}

export function OptimizedLazyLoad({
  children,
  fallback = <LoadingSkeleton />,
  rootMargin = '50px',
  triggerOnce = true,
}: OptimizedLazyLoadProps) {
  const [ref, isIntersecting] = useIntersectionObserver<HTMLDivElement>({
    rootMargin,
    triggerOnce,
  });

  return (
    <div ref={ref}>
      {isIntersecting ? children : fallback}
    </div>
  );
}

