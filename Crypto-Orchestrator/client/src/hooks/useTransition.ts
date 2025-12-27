/**
 * useTransition Hook Wrapper
 * Provides a convenient wrapper for React 18's useTransition
 * for better UX during state updates
 */

import { useTransition as useReactTransition, startTransition } from 'react';

export function useTransition() {
  const [isPending, start] = useReactTransition();
  
  return {
    isPending,
    startTransition: start,
  };
}

// Export startTransition for direct use
export { startTransition };

