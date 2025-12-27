/**
 * Copy to Clipboard Hook
 * Copy text to clipboard with feedback
 */

import { useState, useCallback } from 'react';
import { toast } from '@/components/OptimizedToast';

export function useCopyToClipboard(): [boolean, (text: string) => Promise<boolean>] {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = useCallback(async (text: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success({ description: 'Copied to clipboard' });
      
      setTimeout(() => {
        setCopied(false);
      }, 2000);

      return true;
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      toast.error({ description: 'Failed to copy to clipboard' });
      return false;
    }
  }, []);

  return [copied, copyToClipboard];
}

