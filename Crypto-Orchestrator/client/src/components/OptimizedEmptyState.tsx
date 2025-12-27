/**
 * Optimized Empty State Component
 * Consistent empty states across the application
 */

import React from 'react';
import { EmptyState } from './EmptyState';
import { Button } from './ui/button';
import { Plus, Search, RefreshCw } from 'lucide-react';

interface OptimizedEmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
  variant?: 'default' | 'search' | 'error' | 'loading';
}

const variantConfig = {
  default: {
    icon: <Plus className="h-12 w-12 text-muted-foreground" />,
    title: 'No items found',
    description: 'Get started by creating your first item.',
  },
  search: {
    icon: <Search className="h-12 w-12 text-muted-foreground" />,
    title: 'No results found',
    description: 'Try adjusting your search terms.',
  },
  error: {
    icon: <RefreshCw className="h-12 w-12 text-muted-foreground" />,
    title: 'Something went wrong',
    description: 'Please try again or contact support.',
  },
  loading: {
    icon: <RefreshCw className="h-12 w-12 text-muted-foreground animate-spin" />,
    title: 'Loading...',
    description: 'Please wait while we load your data.',
  },
};

export function OptimizedEmptyState({
  title,
  description,
  icon,
  action,
  variant = 'default',
}: OptimizedEmptyStateProps) {
  const config = variantConfig[variant];

  return (
    <EmptyState
      icon={(icon || config.icon) as any}
      title={title || config.title}
      description={description || config.description}
      action={
        action ? {
          label: action.label,
          onClick: action.onClick,
        } : undefined
      }
    />
  );
}

