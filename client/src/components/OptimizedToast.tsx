/**
 * Optimized Toast Component
 * Enhanced toast notifications with actions and auto-dismiss
 */

import React from 'react';
import { toast as shadcnToast, ToastActionElement } from '@/hooks/use-toast';
import { ToastAction } from '@/hooks/use-toast';

interface ToastOptions {
  title?: string;
  description: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

function createToastAction(action?: { label: string; onClick: () => void }): ToastActionElement | undefined {
  if (!action) return undefined;
  return (
    <ToastAction altText={action.label} onClick={action.onClick}>
      {action.label}
    </ToastAction>
  ) as ToastActionElement;
}

export const toast = {
  success: (options: ToastOptions) => {
    return shadcnToast({
      title: options.title || 'Success',
      description: options.description,
      duration: options.duration,
      action: createToastAction(options.action),
      variant: 'default',
    });
  },
  error: (options: ToastOptions) => {
    return shadcnToast({
      title: options.title || 'Error',
      description: options.description,
      duration: options.duration,
      action: createToastAction(options.action),
      variant: 'destructive',
    });
  },
  warning: (options: ToastOptions) => {
    return shadcnToast({
      title: options.title || 'Warning',
      description: options.description,
      duration: options.duration,
      action: createToastAction(options.action),
    });
  },
  info: (options: ToastOptions) => {
    return shadcnToast({
      title: options.title || 'Info',
      description: options.description,
      duration: options.duration,
      action: createToastAction(options.action),
    });
  },
};

export const OptimizedToast = toast;
export default toast;
