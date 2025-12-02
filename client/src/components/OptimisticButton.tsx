/**
 * Optimistic Button Component
 * Provides optimistic updates with loading states
 */

import { Button, ButtonProps } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OptimisticButtonProps extends ButtonProps {
  isLoading?: boolean;
  optimistic?: boolean;
  children: React.ReactNode;
}

export function OptimisticButton({
  isLoading = false,
  optimistic = false,
  className,
  disabled,
  children,
  ...props
}: OptimisticButtonProps) {
  return (
    <Button
      className={cn(className)}
      disabled={disabled || isLoading}
      aria-busy={isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          {optimistic ? children : 'Loading...'}
        </>
      ) : (
        children
      )}
    </Button>
  );
}

