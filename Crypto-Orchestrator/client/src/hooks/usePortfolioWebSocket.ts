/**
 * WebSocket Hook for Real-time Portfolio Updates
 */

import { useEffect, useState, useRef } from "react";
import { useAuth } from "./useAuth";

// Window and ImportMeta types are now defined in client/src/types/global.d.ts

interface PortfolioData {
  totalBalance: number;
  availableBalance: number;
  positions: Record<string, unknown>;
  profitLoss24h: number;
  profitLossTotal: number;
  successfulTrades?: number;
  failedTrades?: number;
  totalTrades?: number;
  winRate?: number;
  averageWin?: number;
  averageLoss?: number;
}

interface PortfolioUpdate {
  type: string;
  timestamp: string;
  data: PortfolioData;
}

export function usePortfolioWebSocket(mode: "paper" | "real" = "paper") {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const maxReconnectAttempts = 10;
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    const connect = () => {
      try {
        const baseUrl =
          (typeof window !== "undefined" ? window.__API_BASE__ : undefined) ||
          import.meta.env.VITE_API_BASE_URL ||
          "http://localhost:8000";
        const wsUrl = baseUrl.replace("http://", "ws://").replace("https://", "wss://");
        const token = localStorage.getItem("auth_token");

        if (!token) {
          setError("No authentication token found");
          return;
        }

        const fullUrl = `${wsUrl}/api/ws/portfolio?token=${encodeURIComponent(token)}`;
        const ws = new WebSocket(fullUrl);

        ws.onopen = () => {
          // Connection opened - token is already in query string
          // Backend will authenticate automatically
          setIsConnected(true);
          setError(null);
          reconnectAttemptsRef.current = 0; // Reset on successful connection
        };

        ws.onmessage = (event: MessageEvent) => {
          try {
            const message: PortfolioUpdate = JSON.parse(event.data as string);

            // Handle auth success message
            if (message.type === "auth_success") {
              setIsConnected(true);
              setError(null);
              return;
            }

            // Handle error messages
            if (message.type === "error") {
              const errorMsg =
                ("error" in message ? (message as { error?: unknown }).error : null) ||
                message.data;
              setError(typeof errorMsg === "string" ? errorMsg : "WebSocket error");
              if (errorMsg === "Authentication required") {
                setIsConnected(false);
                ws.close();
              }
              return;
            }

            // Handle portfolio updates
            if (message.type === "portfolio_update" && message.data) {
              setPortfolio(message.data as PortfolioData);
            } else if (message.type === "pong") {
              // Heartbeat response
            }
          } catch (e: unknown) {
            const error = e instanceof Error ? e : new Error(String(e));
            // Failed to parse message - log silently
          }
        };

        ws.onerror = (error) => {
          // WebSocket error - handled by onerror
          setError("WebSocket connection error");
        };

        ws.onclose = (event) => {
          // WebSocket disconnected
          setIsConnected(false);

          // Don't reconnect if max attempts reached or no auth
          if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
            setError("Maximum reconnection attempts reached. Please refresh the page.");
            reconnectAttemptsRef.current = 0;
            return;
          }

          // Calculate exponential backoff delay with jitter
          const baseDelay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000); // Max 30s
          const jitter = Math.random() * 1000; // 0-1s jitter
          const delay = baseDelay + jitter;

          reconnectAttemptsRef.current += 1;

          // Attempt to reconnect with exponential backoff
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null;
            connect();
          }, delay);
        };

        wsRef.current = ws;
      } catch (e: unknown) {
        const error = e instanceof Error ? e : new Error(String(e));
        // Failed to connect - error state already set
        setError("Failed to establish WebSocket connection");
      }
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [isAuthenticated, mode]);

  const requestPortfolio = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "get_portfolio",
          mode: mode,
        })
      );
    }
  };

  const subscribe = (mode: "paper" | "real") => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "subscribe",
          mode: mode,
        })
      );
    }
  };

  return {
    portfolio,
    isConnected,
    error,
    requestPortfolio,
    subscribe,
  };
}
