/**
 * Optimized Portfolio WebSocket Hook
 * 
 * High-performance real-time portfolio streaming with:
 * - Delta-based updates (only changed positions)
 * - Throttled rendering to prevent UI jank
 * - Automatic reconnection with exponential backoff
 * - Message queue for burst handling
 * 
 * Performance optimizations:
 * - Uses ref for raw data, state for throttled renders
 * - Memoized selectors for position access
 * - Batch updates to reduce re-renders
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

// Types
interface Position {
  symbol: string;
  quantity: number;
  averageCost: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
  realizedPnl: number;
  lastUpdated: string;
}

interface PortfolioSnapshot {
  userId: number;
  totalValue: number;
  cashBalance: number;
  positionsValue: number;
  unrealizedPnl: number;
  realizedPnl: number;
  totalPnl: number;
  totalPnlPercent: number;
  pnl24h: number;
  pnl24hPercent: number;
  positions: Position[];
  riskMetrics: Record<string, number>;
  timestamp: string;
}

interface PortfolioDelta {
  userId: number;
  changedPositions: Position[];
  totalValueDelta: number;
  unrealizedPnlDelta: number;
  timestamp: string;
}

interface WebSocketMessage {
  type: "snapshot" | "delta" | "error" | "heartbeat";
  data: PortfolioSnapshot | PortfolioDelta | { message: string };
}

interface UsePortfolioStreamOptions {
  /** Throttle interval in ms (default: 100ms) */
  throttleMs?: number;
  /** Enable debug logging */
  debug?: boolean;
  /** Max reconnection attempts */
  maxReconnectAttempts?: number;
  /** Base reconnection delay in ms */
  reconnectDelayMs?: number;
}

interface PortfolioStreamState {
  portfolio: PortfolioSnapshot | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  lastUpdate: Date | null;
  messagesPerSecond: number;
}

/**
 * High-performance portfolio WebSocket hook
 * 
 * @example
 * ```tsx
 * const { portfolio, isConnected } = usePortfolioStream(userId);
 * 
 * // Access specific position with memoization
 * const btcPosition = usePosition(portfolio, "BTC/USDT");
 * ```
 */
export function usePortfolioStream(
  userId: number | undefined,
  options: UsePortfolioStreamOptions = {}
): PortfolioStreamState & {
  reconnect: () => void;
  disconnect: () => void;
} {
  const {
    throttleMs = 100,
    debug = false,
    maxReconnectAttempts = 10,
    reconnectDelayMs = 1000,
  } = options;

  // State for UI rendering (throttled)
  const [state, setState] = useState<PortfolioStreamState>({
    portfolio: null,
    isConnected: false,
    isConnecting: false,
    error: null,
    lastUpdate: null,
    messagesPerSecond: 0,
  });

  // Refs for real-time data (not triggering renders)
  const wsRef = useRef<WebSocket | null>(null);
  const portfolioRef = useRef<PortfolioSnapshot | null>(null);
  const messageQueueRef = useRef<WebSocketMessage[]>([]);
  const messageCountRef = useRef(0);
  const reconnectAttemptRef = useRef(0);
  const throttleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rpsIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Process message queue and update state (throttled)
  const flushUpdates = useCallback(() => {
    const queue = messageQueueRef.current;
    if (queue.length === 0) return;

    // Process all queued messages
    for (const msg of queue) {
      if (msg.type === "snapshot") {
        portfolioRef.current = msg.data as PortfolioSnapshot;
      } else if (msg.type === "delta" && portfolioRef.current) {
        const delta = msg.data as PortfolioDelta;
        // Apply delta updates
        const current = portfolioRef.current;
        const updatedPositions = [...current.positions];

        for (const changedPos of delta.changedPositions) {
          const idx = updatedPositions.findIndex(
            (p) => p.symbol === changedPos.symbol
          );
          if (idx >= 0) {
            updatedPositions[idx] = changedPos;
          } else {
            updatedPositions.push(changedPos);
          }
        }

        portfolioRef.current = {
          ...current,
          totalValue: current.totalValue + delta.totalValueDelta,
          unrealizedPnl: current.unrealizedPnl + delta.unrealizedPnlDelta,
          positions: updatedPositions,
          timestamp: delta.timestamp,
        };
      }
    }

    // Clear queue
    messageQueueRef.current = [];

    // Update state (triggers render)
    if (portfolioRef.current) {
      setState((prev) => ({
        ...prev,
        portfolio: portfolioRef.current,
        lastUpdate: new Date(),
      }));
    }
  }, []);

  // Schedule throttled flush
  const scheduleFlush = useCallback(() => {
    if (throttleTimerRef.current) return;

    throttleTimerRef.current = setTimeout(() => {
      throttleTimerRef.current = null;
      flushUpdates();
    }, throttleMs);
  }, [throttleMs, flushUpdates]);

  // Handle incoming message
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const msg: WebSocketMessage = JSON.parse(event.data);
        messageCountRef.current++;

        if (msg.type === "heartbeat") {
          if (debug) console.log("[WS] Heartbeat received");
          return;
        }

        if (msg.type === "error") {
          const errorData = msg.data as { message: string };
          setState((prev) => ({ ...prev, error: errorData.message }));
          return;
        }

        // Queue message and schedule throttled flush
        messageQueueRef.current.push(msg);
        scheduleFlush();
      } catch (e) {
        console.error("[WS] Failed to parse message:", e);
      }
    },
    [debug, scheduleFlush]
  );

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!userId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setState((prev) => ({ ...prev, isConnecting: true, error: null }));

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/v1/portfolio/stream/${userId}`;

    if (debug) console.log("[WS] Connecting to:", wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      if (debug) console.log("[WS] Connected");
      reconnectAttemptRef.current = 0;
      setState((prev) => ({
        ...prev,
        isConnected: true,
        isConnecting: false,
        error: null,
      }));
    };

    ws.onmessage = handleMessage;

    ws.onclose = (event) => {
      if (debug) console.log("[WS] Closed:", event.code, event.reason);
      setState((prev) => ({ ...prev, isConnected: false, isConnecting: false }));

      // Attempt reconnection with exponential backoff
      if (reconnectAttemptRef.current < maxReconnectAttempts) {
        const delay =
          reconnectDelayMs * Math.pow(2, reconnectAttemptRef.current);
        reconnectAttemptRef.current++;
        if (debug)
          console.log(
            `[WS] Reconnecting in ${delay}ms (attempt ${reconnectAttemptRef.current})`
          );
        setTimeout(connect, delay);
      } else {
        setState((prev) => ({
          ...prev,
          error: "Max reconnection attempts reached",
        }));
      }
    };

    ws.onerror = (error) => {
      console.error("[WS] Error:", error);
      setState((prev) => ({ ...prev, error: "WebSocket error" }));
    };

    wsRef.current = ws;
  }, [
    userId,
    debug,
    handleMessage,
    maxReconnectAttempts,
    reconnectDelayMs,
  ]);

  // Disconnect
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setState((prev) => ({ ...prev, isConnected: false }));
  }, []);

  // Reconnect (force)
  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptRef.current = 0;
    connect();
  }, [disconnect, connect]);

  // Calculate messages per second
  useEffect(() => {
    rpsIntervalRef.current = setInterval(() => {
      setState((prev) => ({
        ...prev,
        messagesPerSecond: messageCountRef.current,
      }));
      messageCountRef.current = 0;
    }, 1000);

    return () => {
      if (rpsIntervalRef.current) {
        clearInterval(rpsIntervalRef.current);
      }
    };
  }, []);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
      if (throttleTimerRef.current) {
        clearTimeout(throttleTimerRef.current);
      }
    };
  }, [connect, disconnect]);

  return {
    ...state,
    reconnect,
    disconnect,
  };
}

/**
 * Memoized position selector hook
 * Prevents re-renders when other positions change
 */
export function usePosition(
  portfolio: PortfolioSnapshot | null,
  symbol: string
): Position | null {
  return useMemo(() => {
    if (!portfolio) return null;
    return portfolio.positions.find((p) => p.symbol === symbol) ?? null;
  }, [portfolio, symbol]);
}

/**
 * Memoized risk metrics selector
 */
export function useRiskMetrics(
  portfolio: PortfolioSnapshot | null
): Record<string, number> {
  return useMemo(() => {
    if (!portfolio) return {};
    return portfolio.riskMetrics;
  }, [portfolio?.riskMetrics]);
}

export default usePortfolioStream;
