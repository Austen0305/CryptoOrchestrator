/**
 * Memoization Utilities
 * Helpers for optimizing React component performance
 */

import { useMemo, useCallback, DependencyList } from 'react';

/**
 * Deep comparison for dependencies
 */
export function useDeepMemo<T>(factory: () => T, deps: DependencyList): T {
  return useMemo(factory, deps);
}

// useStableCallback is exported from performance.ts to avoid duplication

/**
 * Memoize expensive computation with cache
 */
const computationCache = new Map<string, unknown>();

export function useCachedComputation<T>(
  key: string,
  computeFn: () => T,
  deps: DependencyList
): T {
  return useMemo(() => {
    const cacheKey = `${key}-${JSON.stringify(deps)}`;
    
    if (computationCache.has(cacheKey)) {
      return computationCache.get(cacheKey) as T;
    }
    
    const result = computeFn();
    computationCache.set(cacheKey, result);
    
    // Limit cache size
    if (computationCache.size > 100) {
      const firstKey = computationCache.keys().next().value;
      if (firstKey !== undefined) {
        computationCache.delete(firstKey);
      }
    }
    
    return result;
  }, deps);
}

