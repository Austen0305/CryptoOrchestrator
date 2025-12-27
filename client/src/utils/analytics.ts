/**
 * Analytics Utilities
 * Frontend analytics and tracking
 */

/**
 * Track page view
 */
export function trackPageView(path: string): void {
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    // Example: Google Analytics, Plausible, etc.
    // gtag('config', 'GA_MEASUREMENT_ID', { page_path: path });
    console.log('[Analytics] Page view:', path);
  }
}

/**
 * Track event
 */
export function trackEvent(
  category: string,
  action: string,
  label?: string,
  value?: number
): void {
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    // Example: Google Analytics
    // gtag('event', action, { event_category: category, event_label: label, value });
    console.log('[Analytics] Event:', { category, action, label, value });
  }
}

/**
 * Track error
 */
export function trackError(error: Error, context?: Record<string, unknown>): void {
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    // Example: Sentry, LogRocket, etc.
    // Sentry.captureException(error, { contexts: { custom: context } });
    console.error('[Analytics] Error:', error, context);
  }
}

/**
 * Track performance metric
 */
export function trackPerformance(metric: string, value: number, unit: string = 'ms'): void {
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    // Example: Google Analytics
    // gtag('event', 'timing_complete', { name: metric, value, event_category: 'Performance' });
    console.log('[Analytics] Performance:', { metric, value, unit });
  }
}

