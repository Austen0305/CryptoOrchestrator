import { useEffect, useRef, useState } from "react";
import { useAuth } from "./useAuth";
import logger from "@/lib/logger";

export interface WalletUpdate {
  type: "wallet_update" | "initial_balance" | "balance_response" | "error" | "pong";
  data?: unknown;
  timestamp?: string;
  message?: string;
}

export function useWalletWebSocket(currency: string = "USD") {
  const { isAuthenticated } = useAuth();
  const [balance, setBalance] = useState<unknown>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token') : null;
    if (!token) {
      return;
    }

    const connect = () => {
      try {
        // Derive WebSocket URL from API URL or use explicit WS URL
        const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const wsUrl = import.meta.env.VITE_WS_URL || 
          (apiUrl.startsWith('http') 
            ? apiUrl.replace(/^https?/, (match) => match === 'https' ? 'wss' : 'ws')
            : "ws://localhost:8000");
        const ws = new WebSocket(`${wsUrl}/ws/wallet?token=${token}`);
        
        ws.onopen = () => {
          logger.debug("Wallet WebSocket connected");
          setIsConnected(true);
          reconnectAttempts.current = 0;
          
          // Request initial balance
          ws.send(JSON.stringify({
            type: "get_balance",
            currency: currency
          }));
        };

        ws.onmessage = (event) => {
          try {
            const message: WalletUpdate = JSON.parse(event.data);
            
            if (message.type === "wallet_update" || message.type === "initial_balance" || message.type === "balance_response") {
              if (message.data) {
                setBalance(message.data);
              }
            } else if (message.type === "error") {
              logger.error("Wallet WebSocket error:", message.message);
            } else if (message.type === "pong") {
              // Heartbeat response
            }
          } catch (error) {
            logger.error("Error parsing wallet WebSocket message:", error);
          }
        };

        ws.onerror = (error) => {
          logger.error("Wallet WebSocket error:", error);
          setIsConnected(false);
        };

        ws.onclose = () => {
          logger.debug("Wallet WebSocket disconnected");
          setIsConnected(false);
          
          // Attempt to reconnect
          if (reconnectAttempts.current < maxReconnectAttempts) {
            reconnectAttempts.current++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
            reconnectTimeoutRef.current = setTimeout(() => {
              connect();
            }, delay);
          }
        };

        wsRef.current = ws;
      } catch (error) {
        logger.error("Error creating wallet WebSocket:", error);
        setIsConnected(false);
      }
    };

    connect();

    // Heartbeat to keep connection alive
    const heartbeatInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000); // Every 30 seconds

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      clearInterval(heartbeatInterval);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [isAuthenticated, currency]);

  return {
    balance,
    isConnected,
    requestBalance: (curr: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: "get_balance",
          currency: curr
        }));
      }
    }
  };
}

