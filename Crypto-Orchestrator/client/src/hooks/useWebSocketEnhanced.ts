/**
 * Enhanced WebSocket Hook
 * Provides React hook for WebSocket connection with backend integration
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { getWebSocketClient, EnhancedWebSocketClient } from "@/lib/websocketEnhanced";

export interface UseWebSocketOptions {
  enabled?: boolean;
  token?: string;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export interface UseWebSocketReturn {
  ws: EnhancedWebSocketClient | null;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  send: (type: string, data: unknown) => void;
  subscribe: (type: string, callback: (data: unknown) => void) => () => void;
  state: "connecting" | "open" | "closing" | "closed";
}

/**
 * Hook for WebSocket connection
 */
export function useWebSocketEnhanced(
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const {
    enabled = true,
    token,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [state, setState] = useState<"connecting" | "open" | "closing" | "closed">("closed");
  const wsRef = useRef<EnhancedWebSocketClient | null>(null);

  const connect = useCallback(async () => {
    if (wsRef.current && wsRef.current.isConnected()) {
      return;
    }

    const ws = getWebSocketClient(url);
    wsRef.current = ws;

    // Register callbacks
    if (onConnect) {
      ws.onConnect(() => {
        setIsConnected(true);
        setState("open");
        onConnect();
      });
    }

    if (onDisconnect) {
      ws.onDisconnect(() => {
        setIsConnected(false);
        setState("closed");
        onDisconnect();
      });
    }

    if (onError) {
      ws.onError(onError);
    }

    try {
      setState("connecting");
      await ws.connect(token);
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      setState("closed");
    }
  }, [url, token, onConnect, onDisconnect, onError]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect();
      setIsConnected(false);
      setState("closed");
    }
  }, []);

  const send = useCallback((type: string, data: unknown) => {
    if (wsRef.current && wsRef.current.isConnected()) {
      wsRef.current.send(type, data);
    } else {
      console.warn("WebSocket is not connected");
    }
  }, []);

  const subscribe = useCallback(
    (type: string, callback: (data: unknown) => void) => {
      if (wsRef.current) {
        return wsRef.current.on(type, callback);
      }
      return () => {}; // No-op unsubscribe
    },
    []
  );

  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  // Update state from WebSocket
  useEffect(() => {
    if (!wsRef.current) return;

    const interval = setInterval(() => {
      if (wsRef.current) {
        const currentState = wsRef.current.getState();
        setState(currentState);
        setIsConnected(currentState === "open");
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return {
    ws: wsRef.current,
    isConnected,
    connect,
    disconnect,
    send,
    subscribe,
    state,
  };
}

