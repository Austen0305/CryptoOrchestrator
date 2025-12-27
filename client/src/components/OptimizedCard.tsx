/**
 * Optimized Card Component
 * High-performance card with memoization and lazy loading
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
import { cn } from '@/lib/utils';

interface OptimizedCardProps {
  title?: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export const OptimizedCard = React.memo(function OptimizedCard({
  title,
  description,
  children,
  footer,
  className,
  onClick,
  hoverable = false,
}: OptimizedCardProps) {
  return (
    <Card
      className={cn(
        hoverable && 'transition-all hover:shadow-lg cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {(title || description) && (
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
      )}
      <CardContent>{children}</CardContent>
      {footer && <CardFooter>{footer}</CardFooter>}
    </Card>
  );
});
