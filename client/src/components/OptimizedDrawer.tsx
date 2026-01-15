/**
 * Optimized Drawer Component
 * High-performance drawer with lazy loading
 */

import React, { Suspense } from 'react';
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from './ui/drawer';
import { LoadingSkeleton } from './LoadingSkeleton';
import { cn } from '@/lib/utils';

interface OptimizedDrawerProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  trigger?: React.ReactNode;
  title?: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  side?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
  lazy?: boolean;
}

export function OptimizedDrawer({
  open,
  onOpenChange,
  trigger,
  title,
  description,
  children,
  footer,
  side = 'right',
  className,
  lazy = true,
}: OptimizedDrawerProps) {
  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      {trigger ? <DrawerTrigger asChild>{trigger as any}</DrawerTrigger> : null}
      <DrawerContent className={cn(className)}>
        {(title || description) && (
          <DrawerHeader>
            {title && <DrawerTitle>{title}</DrawerTitle>}
            {description && <DrawerDescription>{description}</DrawerDescription>}
          </DrawerHeader>
        )}
        <div className="px-4">
          {lazy && open ? (
            <Suspense fallback={<LoadingSkeleton variant="card" />}>
              {children}
            </Suspense>
          ) : (
            children
          )}
        </div>
        {footer && <DrawerFooter>{footer as any}</DrawerFooter>}
      </DrawerContent>
    </Drawer>
  );
}

