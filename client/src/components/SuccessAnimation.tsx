/**
 * Success Animation Component
 * Provides visual feedback for successful actions
 */

import { useEffect, useState } from 'react';
import { CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SuccessAnimationProps {
  message?: string;
  show: boolean;
  onComplete?: () => void;
  duration?: number;
  className?: string;
}

export function SuccessAnimation({
  message = 'Success!',
  show,
  onComplete,
  duration = 2000,
  className,
}: SuccessAnimationProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (show) {
      setIsVisible(true);
      const timer = setTimeout(() => {
        setIsVisible(false);
        onComplete?.();
      }, duration);
      return () => clearTimeout(timer);
    } else {
      setIsVisible(false);
    }
  }, [show, duration, onComplete]);

  if (!isVisible) return null;

  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm',
        'animate-fade-in',
        className
      )}
    >
      <div className="flex flex-col items-center gap-4 p-8 bg-card border border-card-border rounded-lg shadow-xl animate-scale-in">
        <div className="relative">
          <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping" />
          <CheckCircle2 className="h-16 w-16 text-green-500 relative z-10 animate-scale-in" />
        </div>
        <p className="text-lg font-semibold text-foreground">{message}</p>
      </div>
    </div>
  );
}

/**
 * Inline success indicator
 */
export function SuccessIndicator({ message, className }: { message: string; className?: string }) {
  return (
    <div className={cn('flex items-center gap-2 text-green-600 dark:text-green-400 animate-fade-in', className)}>
      <CheckCircle2 className="h-4 w-4" />
      <span className="text-sm">{message}</span>
    </div>
  );
}
