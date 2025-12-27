/**
 * Bundle Analyzer Utility
 * Helps identify large dependencies and optimize bundle size
 */

export interface BundleInfo {
  name: string;
  size: number;
  gzipped?: number;
  type: 'dependency' | 'component' | 'utility';
}

/**
 * Analyze bundle size (for development)
 */
export function analyzeBundleSize(): BundleInfo[] {
  if (typeof window === 'undefined' || !import.meta.env.DEV) {
    return [];
  }

  const bundles: BundleInfo[] = [];

  // Check performance timing for resource sizes
  if ('performance' in window && 'getEntriesByType' in performance) {
    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
    
    resources.forEach((resource) => {
      if (resource.transferSize) {
        bundles.push({
          name: resource.name,
          size: resource.transferSize,
          type: resource.name.includes('node_modules') ? 'dependency' : 'component',
        });
      }
    });
  }

  return bundles.sort((a, b) => b.size - a.size);
}

/**
 * Log bundle analysis (development only)
 */
export function logBundleAnalysis(): void {
  if (!import.meta.env.DEV) return;

  const bundles = analyzeBundleSize();
  const largeBundles = bundles.filter((b) => b.size > 100 * 1024); // > 100KB

  if (largeBundles.length > 0) {
    console.group('📦 Bundle Analysis');
    console.table(largeBundles.map((b) => ({
      Name: b.name.split('/').pop(),
      Size: `${(b.size / 1024).toFixed(2)} KB`,
      Type: b.type,
    })));
    console.groupEnd();
  }
}

