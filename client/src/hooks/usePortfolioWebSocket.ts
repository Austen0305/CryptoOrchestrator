/**
 * WebSocket Hook for Real-time Portfolio Updates
 */

import { useEffect, useState, useRef } from 'react';
import { useAuth } from './useAuth';

interface WindowWithGlobals extends Window {
  __WS_BASE__?: string;
  __API_BASE__?: string;
  VITE_API_URL?: string;
}
interface ImportMetaWithEnv extends ImportMeta {
  env?: {
    VITE_API_BASE_URL?: string;
    VITE_API_URL?: string;
  };
}

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

export function usePortfolioWebSocket(mode: 'paper' | 'real' = 'paper') {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    const connect = () => {
      try {
        const baseUrl = (globalThis as WindowWithGlobals).VITE_API_URL || (import.meta as ImportMetaWithEnv)?.env?.VITE_API_BASE_URL || 'http://localhost:8000';
        const wsUrl = baseUrl.replace('http://', 'ws://').replace('https://', 'wss://');
        const token = localStorage.getItem('auth_token');
        
        if (!token) {
          setError('No authentication token found');
          return;
        }

        const fullUrl = `${wsUrl}/api/ws/portfolio?token=${encodeURIComponent(token)}`;
        const ws = new WebSocket(fullUrl);

        ws.onopen = () => {
          // Connection opened - token is already in query string
          // Backend will authenticate automatically
          setIsConnected(true);
          setError(null);
        };

        ws.onmessage = (event) => {
          try {
            const message: PortfolioUpdate = JSON.parse(event.data);
            
            // Handle auth success message
            if (message.type === 'auth_success') {
              setIsConnected(true);
              setError(null);
              return;
            }
            
            // Handle error messages
            if (message.type === 'error') {
              const errorMsg = (message as any).error || message.data;
              setError(typeof errorMsg === 'string' ? errorMsg : 'WebSocket error');
              if (errorMsg === 'Authentication required') {
                setIsConnected(false);
                ws.close();
              }
              return;
            }
            
            // Handle portfolio updates
            if (message.type === 'portfolio_update' && message.data) {
              setPortfolio(message.data as PortfolioData);
            } else if (message.type === 'pong') {
              // Heartbeat response
            }
          } catch (e: unknown) {
            const error = e instanceof Error ? e : new Error(String(e));
            // Failed to parse message - log silently
          }
        };

        ws.onerror = (error) => {
          // WebSocket error - handled by onerror
          setError('WebSocket connection error');
        };

        ws.onclose = () => {
          // WebSocket disconnected
          setIsConnected(false);
          
          // Attempt to reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        };

        wsRef.current = ws;
      } catch (e: unknown) {
        const error = e instanceof Error ? e : new Error(String(e));
        // Failed to connect - error state already set
        setError('Failed to establish WebSocket connection');
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
      wsRef.current.send(JSON.stringify({
        type: 'get_portfolio',
        mode: mode,
      }));
    }
  };

  const subscribe = (mode: 'paper' | 'real') => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        mode: mode,
      }));
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

