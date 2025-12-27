/**
 * Sentry Error Tracking Configuration
 * Provides centralized error tracking initialization
 * Compatible with @sentry/react v10+
 */

let sentryInitialized = false;

/**
 * Initialize Sentry for error tracking
 */
export function initSentry() {
  // Only initialize once
  if (sentryInitialized) {
    return;
  }

  // Check if Sentry DSN is configured
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  
  if (!dsn) {
    if (import.meta.env.DEV) {
      console.log('[Sentry] DSN not configured, skipping initialization');
    }
    return;
  }

  try {
    // Dynamically import Sentry (reduce bundle size when not used)
    // @ts-ignore - Optional dependency, may not be installed
    import('@sentry/react').then(async (Sentry: any) => {
      // @ts-ignore - Optional dependency, may not be installed
      const { browserTracingIntegration, replayIntegration } = await import('@sentry/react') as any;
      
      Sentry.init({
        dsn,
        environment: import.meta.env.MODE,
        release: import.meta.env.VITE_APP_VERSION || '1.0.0',
        integrations: [
          browserTracingIntegration(),
          replayIntegration({
            maskAllText: true,
            blockAllMedia: true,
          }),
        ],
        tracesSampleRate: import.meta.env.PROD ? 0.1 : 1.0,
        replaysSessionSampleRate: import.meta.env.PROD ? 0.1 : 1.0,
        replaysOnErrorSampleRate: 1.0,
        beforeSend(event: any, hint: any) {
          // Don't send errors in development
          if (import.meta.env.DEV) {
            console.error('[Sentry] Error caught:', hint.originalException || hint.syntheticException);
            return null;
          }
          return event;
        },
      });

      sentryInitialized = true;
      console.log('[Sentry] Error tracking initialized');
    }).catch((error) => {
      console.warn('[Sentry] Failed to initialize:', error);
    });
  } catch (error) {
    console.warn('[Sentry] Error loading Sentry:', error);
  }
}

/**
 * Report error to Sentry manually
 */
export function reportError(error: Error, context?: Record<string, any>) {
  if (!sentryInitialized) {
    console.error('[Sentry] Error reported but Sentry not initialized:', error, context);
    return;
  }

  // @ts-ignore - Optional dependency, may not be installed
  import('@sentry/react').then((Sentry: any) => {
    Sentry.captureException(error, {
      extra: context,
    });
  }).catch(() => {
    // Silently fail if Sentry not available
  });
}

