/**
 * Optimized Copy Button Component
 * Button that copies text to clipboard
 */

import React from 'react';
import { Button } from './ui/button';
import { Copy, Check } from 'lucide-react';
import { useCopyToClipboard } from '@/hooks/useCopyToClipboard';
import { cn } from '@/lib/utils';

interface OptimizedCopyButtonProps {
  text: string;
  label?: string;
  className?: string;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

export function OptimizedCopyButton({
  text,
  label = 'Copy',
  className,
  variant = 'outline',
  size = 'sm',
}: OptimizedCopyButtonProps) {
  const [copied, copyToClipboard] = useCopyToClipboard();

  return (
    <Button
      variant={variant}
      size={size}
      onClick={() => copyToClipboard(text)}
      className={cn(className)}
    >
      {copied ? (
        <>
          <Check className="h-4 w-4 mr-2" />
          Copied
        </>
      ) : (
        <>
          <Copy className="h-4 w-4 mr-2" />
          {label}
        </>
      )}
    </Button>
  );
}

