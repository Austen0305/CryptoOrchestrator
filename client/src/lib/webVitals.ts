/**
 * Web Vitals Performance Tracking
 * Tracks Core Web Vitals (CLS, LCP, FID) and sends to analytics
 */

import { onCLS, onLCP, onFID, onINP, onTTFB, Metric } from 'web-vitals';

type MetricHandler = (metric: Metric) => void;

/**
 * Send metric to analytics endpoint
 */
async function sendToAnalytics(metric: Metric) {
  try {
    // Send to FastAPI analytics endpoint
    const response = await fetch('/api/analytics/web-vitals', {
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
      console.warn('Failed to send web vitals:', response.statusText);
    }
  } catch (error) {
    console.warn('Error sending web vitals:', error);
  }

  // Also log to console in development
  if (import.meta.env.DEV) {
    console.log(`[Web Vitals] ${metric.name}: ${metric.value} (${metric.rating})`);
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

  console.log('[Web Vitals] Performance tracking initialized');
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

