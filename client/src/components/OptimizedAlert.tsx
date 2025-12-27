/**
 * Optimized Alert Component
 * Enhanced alert with auto-dismiss and actions
 */

import React, { useEffect, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Button } from './ui/button';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OptimizedAlertProps {
  title?: string;
  description: string;
  variant?: 'default' | 'destructive' | 'success' | 'warning' | 'info';
  dismissible?: boolean;
  autoDismiss?: number; // milliseconds
  onDismiss?: () => void;
  actions?: Array<{
    label: string;
    onClick: () => void;
  }>;
  className?: string;
}

export function OptimizedAlert({
  title,
  description,
  variant = 'default',
  dismissible = false,
  autoDismiss,
  onDismiss,
  actions,
  className,
}: OptimizedAlertProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (autoDismiss && isVisible) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        onDismiss?.();
      }, autoDismiss);

      return () => clearTimeout(timer);
    }
    return undefined;
  }, [autoDismiss, isVisible, onDismiss]);

  const handleDismiss = () => {
    setIsVisible(false);
    onDismiss?.();
  };

  if (!isVisible) return null;

  const variantClasses = {
    default: '',
    destructive: 'border-destructive',
    success: 'border-green-500 bg-green-50 dark:bg-green-950',
    warning: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950',
    info: 'border-blue-500 bg-blue-50 dark:bg-blue-950',
  };

  return (
    <Alert className={cn(variantClasses[variant], className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {title && <AlertTitle>{title}</AlertTitle>}
          <AlertDescription>{description}</AlertDescription>
          {actions && actions.length > 0 && (
            <div className="mt-2 flex gap-2">
              {actions.map((action, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={action.onClick}
                >
                  {action.label}
                </Button>
              ))}
            </div>
          )}
        </div>
        {dismissible && (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDismiss}
            className="h-6 w-6"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
    </Alert>
  );
}

