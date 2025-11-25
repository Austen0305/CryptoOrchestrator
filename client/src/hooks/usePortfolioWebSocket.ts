/**
 * WebSocket Hook for Real-time Portfolio Updates
 */

import { useEffect, useState, useRef } from 'react';
import { useAuth } from './useAuth';

interface PortfolioData {
  totalBalance: number;
  availableBalance: number;
  positions: Record<string, any>;
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
        const baseUrl = (globalThis as any).VITE_API_URL || 'http://localhost:8000';
        const wsUrl = baseUrl.replace('http://', 'ws://').replace('https://', 'wss://');
        const token = localStorage.getItem('auth_token');
        
        if (!token) {
          setError('No authentication token found');
          return;
        }

        const fullUrl = `${wsUrl}/api/ws/portfolio?token=${encodeURIComponent(token)}`;
        const ws = new WebSocket(fullUrl);

        ws.onopen = () => {
          console.log('[Portfolio WS] Connected');
          setIsConnected(true);
          setError(null);
          
          // Send authentication message if needed
          ws.send(JSON.stringify({
            type: 'auth',
            token: token,
          }));
        };

        ws.onmessage = (event) => {
          try {
            const message: PortfolioUpdate = JSON.parse(event.data);
            
            if (message.type === 'portfolio_update' && message.data) {
              setPortfolio(message.data);
            } else if (message.type === 'pong') {
              // Heartbeat response
            } else if (message.type === 'error') {
              setError(message.data as any);
            }
          } catch (e) {
            console.error('[Portfolio WS] Failed to parse message:', e);
          }
        };

        ws.onerror = (error) => {
          console.error('[Portfolio WS] Error:', error);
          setError('WebSocket connection error');
        };

        ws.onclose = () => {
          console.log('[Portfolio WS] Disconnected');
          setIsConnected(false);
          
          // Attempt to reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        };

        wsRef.current = ws;
      } catch (e) {
        console.error('[Portfolio WS] Failed to connect:', e);
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

