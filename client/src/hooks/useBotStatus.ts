import { useEffect, useRef, useState } from 'react';

interface BotStatusMessage {
  type: 'auth_success' | 'bot_status' | 'pong' | 'error';
  bot_id?: string;
  status?: string;
  message?: string;
}

export function useBotStatus() {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [botStatuses, setBotStatuses] = useState<Record<string, string>>({});

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (!token) return;

    const wsBase = (typeof window !== 'undefined' && window.__WS_BASE__)
      || import.meta.env.VITE_WS_BASE_URL
      || import.meta.env.VITE_WS_URL
      || (() => {
        const api = (typeof window !== 'undefined' && window.__API_BASE__) || import.meta.env.VITE_API_URL || '';
        if (api.startsWith('http')) {
          // Convert HTTPS to WSS, HTTP to WS
          return api.replace(/^https?/, (match) => match === 'https' ? 'wss' : 'ws');
        }
        return 'wss://gets-wise-sheets-rick.trycloudflare.com';
      })();

    const ws = new WebSocket(`${wsBase}/ws/bot-status`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'auth', token }));
    };

    ws.onmessage = (event) => {
      try {
        const msg: BotStatusMessage = JSON.parse(event.data);
        if (msg.type === 'auth_success') {
          setIsConnected(true);
          return;
        }
        if (msg.type === 'bot_status' && msg.bot_id && msg.status) {
          setBotStatuses(prev => ({ ...prev, [msg.bot_id!]: msg.status! }));
        }
      } catch (e) {
        // ignore
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // simple reconnect
      setTimeout(() => {
        if (token) {
          // trigger effect by resetting ref? Simply call again by setting state
          // noop; rely on component remount or page lifecycle
        }
      }, 7000);
    };

    return () => {
      ws.close();
    };
  }, []);

  const runningBots = Object.values(botStatuses).filter(s => s === 'running' || s === 'started').length;

  return { isConnected, botStatuses, runningBots };
}
