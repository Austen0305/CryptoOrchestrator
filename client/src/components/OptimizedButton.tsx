/**
 * Optimized Button Component
 * Enhanced button with loading states, debouncing, and accessibility
 */

import React, { useCallback, useRef } from 'react';
import { Button, ButtonProps } from './ui/button';
import { Loader2 } from 'lucide-react';
import { useDebounce } from '@/utils/performance';

interface OptimizedButtonProps extends ButtonProps {
  loading?: boolean;
  debounceMs?: number;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void | Promise<void>;
}

export const OptimizedButton = React.memo(function OptimizedButton({
  loading = false,
  debounceMs = 300,
  onClick,
  disabled,
  children,
  ...props
}: OptimizedButtonProps) {
  const isProcessingRef = useRef(false);

  const debouncedOnClick = useDebounce(
    useCallback(
      async (e: React.MouseEvent<HTMLButtonElement>) => {
        if (isProcessingRef.current || disabled) return;
        
        isProcessingRef.current = true;
        try {
          await onClick?.(e);
        } finally {
          isProcessingRef.current = false;
        }
      },
      [onClick, disabled]
    ),
    debounceMs
  );

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();
      debouncedOnClick(e);
    },
    [debouncedOnClick]
  );

  return (
    <Button
      {...props}
      onClick={handleClick}
      disabled={disabled || loading || isProcessingRef.current}
    >
      {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {children}
    </Button>
  );
});

