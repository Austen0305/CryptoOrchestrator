import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, Zap, Clock, Database } from 'lucide-react';
import { useWebVitals } from '@/hooks/useWebVitals';

interface PerformanceMetrics {
  fps: number;
  memory: number;
  loadTime: number;
  apiLatency: number;
}

interface BackendMetrics {
  system?: {
    cpu_percent?: number;
    memory_percent?: number;
    disk_free_gb?: number;
    network_sent_mb?: number;
    network_recv_mb?: number;
  };
  application?: {
    uptime_seconds?: number;
    active_bots?: number;
    total_requests?: number;
    active_websocket_connections?: number;
    average_response_time_ms?: number;
  };
  circuit_breakers?: Record<string, unknown>;
  database?: Record<string, unknown>;
  timestamp?: string;
  [key: string]: unknown; // Allow additional fields for flexibility
}

export function PerformanceMonitor() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    memory: 0,
    loadTime: 0,
    apiLatency: 0,
  });
  const [isVisible, setIsVisible] = useState(false);
  const [wsLatency, setWsLatency] = useState<number | null>(null);
  const [backendMetrics, setBackendMetrics] = useState<BackendMetrics>({});
  const vitals = useWebVitals();

  useEffect(() => {
    // Only show in development
    if (import.meta.env.MODE !== 'development') return;

    // Keyboard shortcut: Ctrl+Shift+P to toggle
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'P') {
        e.preventDefault();
        setIsVisible((prev) => !prev);
      }
    };

  document.addEventListener('keydown', handleKeyDown);

  // Collect cleanup callbacks
  const cleanupFns: Array<() => void> = [];

  // Connect performance metrics websocket
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    let perfWs: WebSocket | null = null;
    if (token) {
      // Type-safe access to window/import.meta properties
      interface WindowWithGlobals extends Window {
        __WS_BASE__?: string;
        __API_BASE__?: string;
      }
      interface ImportMetaWithEnv extends Omit<ImportMeta, 'env'> {
        env: {
          VITE_WS_BASE_URL?: string;
          VITE_API_BASE_URL?: string;
        };
      }

      const windowWithGlobals = typeof window !== 'undefined' ? window as WindowWithGlobals : null;
      const importMetaWithEnv = import.meta as ImportMetaWithEnv;

      const wsBase = windowWithGlobals?.__WS_BASE__
        || importMetaWithEnv?.env?.VITE_WS_BASE_URL
        || (() => {
          const api = windowWithGlobals?.__API_BASE__ || importMetaWithEnv?.env?.VITE_API_BASE_URL || '';
          if (api.startsWith('http')) return api.replace(/^http/, 'ws');
          return 'ws://localhost:8000';
        })();
      perfWs = new WebSocket(`${wsBase}/ws/performance-metrics`);
      perfWs.onopen = () => {
        perfWs?.send(JSON.stringify({ type: 'auth', token }));
      };
      perfWs.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'auth_success') return;
          if (data.type === 'metrics') {
            setBackendMetrics(data.data || {});
          } else if (data.type === 'pong' && data.sentAt) {
            const rtt = performance.now() - data.sentAt;
            setWsLatency(Math.round(rtt));
          }
        } catch (error) {
          // Silently ignore WebSocket message parsing errors to prevent console spam
          // These are typically non-critical performance monitoring messages
        }
      };
      // periodic ping
      const pingInterval = setInterval(() => {
        perfWs?.send(JSON.stringify({ type: 'ping', sentAt: performance.now() }));
      }, 5000);
      // cleanup ping and socket
      const cleanupPerf = () => {
        clearInterval(pingInterval);
        perfWs?.close();
      };
      // augment cleanup below
      cleanupFns.push(cleanupPerf);
    }

    // Calculate initial load time
    if (performance.timing) {
      const loadTime =
        performance.timing.loadEventEnd - performance.timing.navigationStart;
      setMetrics((prev) => ({ ...prev, loadTime }));
    }

    // FPS Counter
    let frameCount = 0;
    let lastTime = performance.now();
    
    function countFPS() {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime >= lastTime + 1000) {
        setMetrics((prev) => ({ ...prev, fps: frameCount }));
        frameCount = 0;
        lastTime = currentTime;
      }
      
      requestAnimationFrame(countFPS);
    }
    
    const fpsAnimation = requestAnimationFrame(countFPS);

    // Memory usage (if available) - Chrome-specific API
    interface PerformanceWithMemory extends Performance {
      memory?: {
        usedJSHeapSize: number;
        totalJSHeapSize: number;
        jsHeapSizeLimit: number;
      };
    }
    const performanceWithMemory = performance as PerformanceWithMemory;

    const memoryInterval = setInterval(() => {
      if (performanceWithMemory.memory) {
        const memory = performanceWithMemory.memory.usedJSHeapSize / 1048576; // MB
        setMetrics((prev) => ({ ...prev, memory }));
      }
    }, 1000);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      cancelAnimationFrame(fpsAnimation);
      clearInterval(memoryInterval);
      cleanupFns.forEach(fn => fn());
    };
  }, []);

  if (!isVisible || import.meta.env.MODE !== 'development') {
    return null;
  }

  const getPerformanceColor = (value: number, thresholds: [number, number]) => {
    if (value >= thresholds[0]) return 'text-green-500';
    if (value >= thresholds[1]) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80">
      <Card className="border-2 border-primary/20 shadow-lg">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Performance Monitor
            </span>
            <Badge variant="outline" className="text-xs">
              DEV
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {/* FPS */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-muted-foreground" />
              <span>FPS</span>
            </div>
            <span
              className={`font-mono font-semibold ${getPerformanceColor(
                metrics.fps,
                [50, 30]
              )}`}
            >
              {metrics.fps.toFixed(0)}
            </span>
          </div>

          {/* Memory */}
          {metrics.memory > 0 && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-muted-foreground" />
                <span>Memory</span>
              </div>
              <span className="font-mono font-semibold">
                {metrics.memory.toFixed(1)} MB
              </span>
            </div>
          )}

          {/* Load Time */}
          {metrics.loadTime > 0 && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span>Load Time</span>
              </div>
              <span
                className={`font-mono font-semibold ${getPerformanceColor(
                  5000 - metrics.loadTime,
                  [3000, 1000]
                )}`}
              >
                {(metrics.loadTime / 1000).toFixed(2)}s
              </span>
            </div>
          )}

          {/* API Latency */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <span>API Latency</span>
            </div>
            <span className="font-mono font-semibold">
              {metrics.apiLatency > 0 ? `${metrics.apiLatency}ms` : 'N/A'}
            </span>
          </div>

          {/* WS RTT */}
          {wsLatency !== null && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span>WS RTT</span>
              </div>
              <span className="font-mono font-semibold">{wsLatency}ms</span>
            </div>
          )}

          {/* Backend metrics snapshot */}
          {Object.keys(backendMetrics).length > 0 && (
            <div className="mt-2 border-t pt-2 text-xs max-h-32 overflow-auto space-y-1">
              {Object.entries(backendMetrics).map(([k, v]) => (
                <div key={k} className="flex justify-between"><span className="text-muted-foreground">{k}</span><span className="font-mono">{String(v)}</span></div>
              ))}
            </div>
          )}

          {/* Web Vitals */}
          {(vitals.CLS || vitals.LCP || vitals.FID) && (
            <div className="mt-2 border-t pt-2 text-xs space-y-1">
              {vitals.LCP !== undefined && (
                <div className="flex justify-between"><span className="text-muted-foreground">LCP</span><span className="font-mono">{vitals.LCP} ms</span></div>
              )}
              {vitals.CLS !== undefined && (
                <div className="flex justify-between"><span className="text-muted-foreground">CLS</span><span className="font-mono">{vitals.CLS}</span></div>
              )}
              {vitals.FID !== undefined && (
                <div className="flex justify-between"><span className="text-muted-foreground">FID</span><span className="font-mono">{vitals.FID} ms</span></div>
              )}
            </div>
          )}

          {/* Keyboard Hint */}
          <div className="pt-2 border-t text-xs text-muted-foreground text-center">
            Press <kbd className="px-1 py-0.5 rounded bg-muted">Ctrl</kbd>+
            <kbd className="px-1 py-0.5 rounded bg-muted">Shift</kbd>+
            <kbd className="px-1 py-0.5 rounded bg-muted">P</kbd> to toggle
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Hook to track API call performance
 */
export function useAPIPerformance() {
  const [latency, setLatency] = useState<number>(0);

  const measureLatency = async <T,>(apiCall: () => Promise<T>): Promise<T> => {
    const startTime = performance.now();
    try {
      const result = await apiCall();
      const endTime = performance.now();
      setLatency(Math.round(endTime - startTime));
      return result;
    } catch (error) {
      const endTime = performance.now();
      setLatency(Math.round(endTime - startTime));
      throw error;
    }
  };

  return { latency, measureLatency };
}
