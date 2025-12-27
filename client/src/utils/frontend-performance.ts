/**
 * Frontend Performance Utilities
 * Performance monitoring and optimization for React components
 */

/**
 * Measure component render time
 */
export function measureRenderTime(componentName: string): () => void {
  const start = performance.now();
  
  return () => {
    const end = performance.now();
    const duration = end - start;
    
    if (import.meta.env.DEV) {
      if (duration > 16) { // > 1 frame at 60fps
        console.warn(`[Performance] ${componentName} took ${duration.toFixed(2)}ms to render`);
      }
    }
  };
}

/**
 * Check if component should update
 */
export function shouldComponentUpdate<T>(
  prevProps: T,
  nextProps: T,
  keys: (keyof T)[]
): boolean {
  return keys.some((key) => prevProps[key] !== nextProps[key]);
}

/**
 * Batch state updates
 */
export function batchUpdates(updates: (() => void)[]): void {
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    requestIdleCallback(() => {
      updates.forEach((update) => update());
    });
  } else {
    // Fallback for browsers without requestIdleCallback
    setTimeout(() => {
      updates.forEach((update) => update());
    }, 0);
  }
}

/**
 * Throttle function calls
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): T {
  let inThrottle: boolean;
  
  return ((...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  }) as T;
}

// Debounce is exported from performance.ts to avoid duplication

