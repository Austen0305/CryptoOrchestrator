/**
 * Web Vitals Performance Tracking
 * Tracks Core Web Vitals (CLS, LCP, FID) and sends to analytics
 */

import { onCLS, onLCP, onFID, onINP, onTTFB, Metric } from 'web-vitals';
import logger from './logger';

type MetricHandler = (metric: Metric) => void;

/**
 * Send metric to analytics endpoint
 */
async function sendToAnalytics(metric: Metric) {
  try {
    // Get base URL from environment variables (Vite) or window, with fallback
    // Use the same logic as queryClient.getApiBaseUrl() for consistency
    let baseUrl: string;
    
    // Priority 1: Vite environment variable (available at build time)
    if (import.meta.env.VITE_API_URL) {
      baseUrl = import.meta.env.VITE_API_URL;
    }
    // Priority 2: Window global (runtime override)
    else {
      const windowWithGlobals = typeof window !== "undefined" ? (window as Window & { VITE_API_URL?: string }) : null;
      if (windowWithGlobals?.VITE_API_URL) {
        baseUrl = windowWithGlobals.VITE_API_URL;
      }
      // Fallback: localhost for development only
      else {
        baseUrl = "http://localhost:8000";
      }
    }
    
    // Remove trailing /api if present, since endpoints already include /api
    if (baseUrl.endsWith('/api')) {
      baseUrl = baseUrl.slice(0, -4);
    }
    
    // Ensure HTTPS when page is HTTPS (prevent mixed content)
    if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
      if (baseUrl.startsWith('http://') && !baseUrl.includes('localhost')) {
        // Convert HTTP to HTTPS for production URLs
        baseUrl = baseUrl.replace('http://', 'https://');
      }
      // Skip if still HTTP (would be blocked anyway) - but allow localhost for dev
      if (baseUrl.startsWith('http://') && !baseUrl.includes('localhost')) {
        return;
      }
    }
    
    // Remove trailing /api if present, then add /api/analytics/web-vitals
    // This handles both cases: baseUrl with /api and without
    const cleanBaseUrl = baseUrl.replace(/\/api\/?$/, '');
    const url = `${cleanBaseUrl}/api/analytics/web-vitals`;
    
    // Send to FastAPI analytics endpoint
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: metric.name,
        value: metric.value,
        id: metric.id,
        delta: metric.delta,
        rating: metric.rating,
        navigationType: metric.navigationType,
        timestamp: Date.now(),
      }),
    });

    if (!response.ok) {
      // Silently fail for 404 - endpoint may not be available until backend is restarted
      // Don't log 404 errors to avoid console spam
      if (response.status !== 404 && import.meta.env.DEV) {
        console.debug('Failed to send web vitals:', response.statusText);
      }
    }
  } catch (error) {
    // Silently fail - analytics endpoint is optional
    // Only log in development mode
    if (import.meta.env.DEV) {
      console.debug('Web vitals analytics endpoint not available:', error);
    }
  }

  // Log to logger in development
  if (import.meta.env.DEV) {
    logger.debug(`Web Vitals: ${metric.name}: ${metric.value} (${metric.rating})`);
  }
}

/**
 * Initialize Web Vitals tracking
 */
export function initWebVitals(onMetric?: MetricHandler) {
  const handler: MetricHandler = (metric: Metric) => {
    // Call custom handler if provided
    if (onMetric) {
      onMetric(metric);
    }
    
    // Send to analytics
    sendToAnalytics(metric);
  };

  // Track all Core Web Vitals
  onCLS(handler);      // Cumulative Layout Shift
  onLCP(handler);      // Largest Contentful Paint
  onFID(handler);      // First Input Delay
  onINP(handler);      // Interaction to Next Paint
  onTTFB(handler);     // Time to First Byte

  logger.debug('Web Vitals performance tracking initialized');
}

/**
 * Get performance score (0-100) based on Web Vitals
 */
export function getPerformanceScore(metrics: Metric[]): number {
  const scores: Record<string, number> = {
    good: 100,
    needsImprovement: 50,
    poor: 0,
  };

  const avgRating = metrics.reduce((sum, metric) => {
    return sum + (scores[metric.rating] || 0);
  }, 0) / metrics.length;

  return Math.round(avgRating);
}

