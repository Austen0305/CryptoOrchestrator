/**
 * WebSocket Hook for Real-time Updates
 */
import { useEffect, useRef, useState } from 'react';

interface UseWebSocketResult {
  isConnected: boolean;
  lastMessage: string | null;
  sendMessage: (message: any) => void;
}

export const useWebSocket = (url?: string): UseWebSocketResult => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!url) return;

    try {
      // Construct full WebSocket URL
      const wsUrl = url.startsWith('ws://') || url.startsWith('wss://') 
        ? url 
        : `ws://localhost:8000${url.startsWith('/') ? url : '/' + url}`;
      
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      ws.current.onmessage = (event) => {
        try {
          // Store raw message string for parsing in components
          setLastMessage(event.data);
        } catch (error) {
          console.error('Failed to handle WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      };

      return () => {
        if (ws.current) {
          ws.current.close();
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      return undefined;
    }
  }, [url]);

  const sendMessage = (message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  return {
    isConnected,
    lastMessage,
    sendMessage,
  };
};
