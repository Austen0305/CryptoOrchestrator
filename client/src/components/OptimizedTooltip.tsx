/**
 * Optimized Tooltip Component
 * High-performance tooltip with delay and positioning
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip';
import { useDebounce } from '@/utils/performance';

interface OptimizedTooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  delay?: number;
  side?: 'top' | 'bottom' | 'left' | 'right';
  disabled?: boolean;
}

export function OptimizedTooltip({
  content,
  children,
  delay = 300,
  side = 'top',
  disabled = false,
}: OptimizedTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [shouldShow, setShouldShow] = useState(false);

  const debouncedShow = useDebounce(() => {
    if (!disabled) {
      setShouldShow(true);
    }
  }, delay);

  const handleMouseEnter = () => {
    debouncedShow();
  };

  const handleMouseLeave = () => {
    setShouldShow(false);
    setIsOpen(false);
  };

  useEffect(() => {
    if (shouldShow) {
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  }, [shouldShow]);

  if (disabled) {
    return <>{children}</>;
  }

  return (
    <TooltipProvider>
      <Tooltip open={isOpen} onOpenChange={setIsOpen}>
        <TooltipTrigger
          asChild
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          {children}
        </TooltipTrigger>
        <TooltipContent side={side}>{content}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

