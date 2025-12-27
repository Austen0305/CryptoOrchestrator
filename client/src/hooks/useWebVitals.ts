import { onCLS, onLCP, onFID, Metric } from 'web-vitals';
import { useEffect, useState } from 'react';

export function useWebVitals() {
  const [metrics, setMetrics] = useState<Record<string, number>>({});

  useEffect(() => {
    function report(metric: Metric) {
      setMetrics(prev => ({ ...prev, [metric.name]: Math.round(metric.value) }));
    }
    onCLS(report);
    onLCP(report);
    onFID(report);
  }, []);

  return metrics as { CLS?: number; LCP?: number; FID?: number };
}
