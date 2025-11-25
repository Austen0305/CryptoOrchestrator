import { useEffect, useRef, useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

interface SubscriptionState {
  symbols: Set<string>;
}

interface IncomingMarketUpdate {
  symbol: string;
  price?: number;
  bid?: number;
  ask?: number;
  spread?: number;
  change24h?: number;
  volume24h?: number;
  ts?: number;
  [key: string]: any;
}

export const useWebSocket = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const queryClient = useQueryClient();
  const subscription = useRef<SubscriptionState>({ symbols: new Set(["BTC/USD"]) });

  // Local cache of latest market data to reduce renders; components can pull via queryClient or custom selector later
  const latestMarketDataRef = useRef<Record<string, IncomingMarketUpdate>>({});
  const candlesRef = useRef<Record<string, Array<[number, number, number, number, number, number]>>>({});

  useEffect(() => {
    // Visibility-aware throttle state
    let lastInvalidate = 0;
    const VISIBLE_INTERVAL = 250; // ms
    const HIDDEN_INTERVAL = 2000; // ms
    const maybeInvalidateMarkets = () => {
      const now = Date.now();
      const interval = document.visibilityState === 'hidden' ? HIDDEN_INTERVAL : VISIBLE_INTERVAL;
      if (now - lastInvalidate >= interval) {
        lastInvalidate = now;
        queryClient.invalidateQueries({ queryKey: ["markets"] });
      }
    };

    const connectWebSocket = () => {
      const wsBase =
        (typeof window !== 'undefined' && (window as any).__WS_BASE__) ||
        (import.meta as any)?.env?.VITE_WS_BASE_URL ||
        // derive from API_BASE if present
        (() => {
          const api = (typeof window !== 'undefined' && (window as any).__API_BASE__) || (import.meta as any)?.env?.VITE_API_BASE_URL || '';
          if (api.startsWith('http')) {
            return api.replace(/^http/, 'ws');
          }
          return 'ws://localhost:8000';
        })();
      // Use specific market-data endpoint that expects auth handshake message
  const ws = new WebSocket(`${wsBase}/ws/market-data`);

      ws.onopen = () => {
        console.log("WebSocket connected (pending auth)");
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        if (!token) {
          console.warn('No token present for WebSocket; closing to prevent 500 loop');
          ws.close();
          return;
        }
        ws.send(JSON.stringify({ type: 'auth', token }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("WebSocket message:", data);

          if (data.type === 'auth_success') {
            console.log('WebSocket authenticated');
            setIsConnected(true);
            return; // Don't process further for auth confirmation
          }
          if (data.error === 'Authentication required') {
            console.warn('WebSocket auth failed, closing connection');
            ws.close();
            return;
          }
          if (data.error) {
            console.warn('WebSocket error payload received:', data.error);
          }

          // Handle different message types
          switch (data.type) {
            case "market_data": {
              // Normalize and store latest market update
              const update: IncomingMarketUpdate = data;
              if (update.symbol) {
                // attach timestamp if missing
                if (!update.ts) {
                  update.ts = Date.now();
                }
                latestMarketDataRef.current[update.symbol] = update;
              }
              // Invalidate markets with visibility-aware throttle
              maybeInvalidateMarkets();
              break; }
            case "backfill": {
              const { symbol, candles } = data;
              if (symbol && Array.isArray(candles)) {
                candlesRef.current[symbol] = (candlesRef.current[symbol] || []).concat(candles).sort((a,b)=>a[0]-b[0]);
              }
              break; }
            case "portfolio_update":
              queryClient.invalidateQueries({ queryKey: ["portfolio", data.data.mode] });
              break;
            case "trade_executed":
              queryClient.invalidateQueries({ queryKey: ["trades"] });
              break;
            case "bot_created":
            case "bot_updated":
            case "bot_deleted":
            case "bot_status_changed":
              queryClient.invalidateQueries({ queryKey: ["bots"] });
              queryClient.invalidateQueries({ queryKey: ["status"] });
              break;
            default:
              console.log("Unknown WebSocket message type:", data.type);
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        if (token) {
          console.log("WebSocket disconnected; scheduling reconnect in 7s");
          setTimeout(connectWebSocket, 7000);
        } else {
          console.log("WebSocket disconnected; no token so not reconnecting");
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      wsRef.current = ws;
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [queryClient]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const subscribeSymbols = useCallback((symbols: string[]) => {
    symbols.forEach(s => subscription.current.symbols.add(s));
    sendMessage({ action: 'subscribe', symbols: Array.from(subscription.current.symbols) });
  }, [sendMessage]);

  const unsubscribeSymbols = useCallback((symbols: string[]) => {
    symbols.forEach(s => subscription.current.symbols.delete(s));
    if (subscription.current.symbols.size === 0) {
      sendMessage({ action: 'unsubscribe' });
    } else {
      sendMessage({ action: 'subscribe', symbols: Array.from(subscription.current.symbols) });
    }
  }, [sendMessage]);

  const getLatestMarketData = useCallback(() => ({ ...latestMarketDataRef.current }), []);

  // Auto-resubscribe after reconnect
  useEffect(() => {
    if (isConnected && subscription.current.symbols.size) {
      sendMessage({ action: 'subscribe', symbols: Array.from(subscription.current.symbols) });
      // Backfill stub: send last timestamp per symbol for potential historical gap fill
      const sincePayload = Object.fromEntries(
        Array.from(subscription.current.symbols).map(sym => [sym, latestMarketDataRef.current[sym]?.ts || Date.now() - 60_000])
      );
      sendMessage({ action: 'backfill_request', since: sincePayload });
    }
  }, [isConnected, sendMessage]);

  const getCandles = useCallback((symbol: string) => candlesRef.current[symbol] || [], []);

  return { ws: wsRef.current, isConnected, sendMessage, subscribeSymbols, unsubscribeSymbols, getLatestMarketData, getCandles };
};
