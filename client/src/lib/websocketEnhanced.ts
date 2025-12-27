/**
 * Enhanced WebSocket Client
 * Provides WebSocket connection with request correlation and error handling
 */

import { getCorrelationIds } from "@/utils/requestCorrelation";

export interface WebSocketMessage {
  type: string;
  data: unknown;
  request_id?: string;
  trace_id?: string;
  timestamp?: string;
}

export class EnhancedWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private listeners: Map<string, Set<(data: unknown) => void>> = new Map();
  private onConnectCallbacks: Set<() => void> = new Set();
  private onDisconnectCallbacks: Set<() => void> = new Set();
  private onErrorCallbacks: Set<(error: Event) => void> = new Set();

  constructor(url: string) {
    this.url = url;
  }

  /**
   * Connect to WebSocket server
   */
  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Add correlation IDs to connection
        const correlationIds = getCorrelationIds();
        const params = new URLSearchParams();
        
        if (token) {
          params.append("token", token);
        }
        
        if (correlationIds.traceId) {
          params.append("trace_id", correlationIds.traceId);
        }
        
        if (correlationIds.requestId) {
          params.append("request_id", correlationIds.requestId);
        }

        const wsUrl = params.toString() 
          ? `${this.url}?${params.toString()}`
          : this.url;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          this.reconnectAttempts = 0;
          this.onConnectCallbacks.forEach((callback) => callback());
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        this.ws.onerror = (error) => {
          this.onErrorCallbacks.forEach((callback) => callback(error));
          reject(error);
        };

        this.ws.onclose = () => {
          this.onDisconnectCallbacks.forEach((callback) => callback());
          this.attemptReconnect(token);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Send message through WebSocket
   */
  send(type: string, data: unknown): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not connected");
    }

    const correlationIds = getCorrelationIds();
    const message: WebSocketMessage = {
      type,
      data,
      request_id: correlationIds.requestId || undefined,
      trace_id: correlationIds.traceId || undefined,
      timestamp: new Date().toISOString(),
    };

    this.ws.send(JSON.stringify(message));
  }

  /**
   * Subscribe to message type
   */
  on(type: string, callback: (data: unknown) => void): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)!.add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(type);
      if (callbacks) {
        callbacks.delete(callback);
      }
    };
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WebSocketMessage): void {
    const callbacks = this.listeners.get(message.type);
    if (callbacks) {
      callbacks.forEach((callback) => callback(message.data));
    }

    // Also trigger wildcard listeners
    const wildcardCallbacks = this.listeners.get("*");
    if (wildcardCallbacks) {
      wildcardCallbacks.forEach((callback) => callback(message));
    }
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(token?: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      this.connect(token).catch((error) => {
        console.error("Reconnection failed:", error);
      });
    }, delay);
  }

  /**
   * Register connection callback
   */
  onConnect(callback: () => void): () => void {
    this.onConnectCallbacks.add(callback);
    return () => {
      this.onConnectCallbacks.delete(callback);
    };
  }

  /**
   * Register disconnection callback
   */
  onDisconnect(callback: () => void): () => void {
    this.onDisconnectCallbacks.add(callback);
    return () => {
      this.onDisconnectCallbacks.delete(callback);
    };
  }

  /**
   * Register error callback
   */
  onError(callback: (error: Event) => void): () => void {
    this.onErrorCallbacks.add(callback);
    return () => {
      this.onErrorCallbacks.delete(callback);
    };
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection state
   */
  getState(): "connecting" | "open" | "closing" | "closed" {
    if (!this.ws) return "closed";
    
    const states = ["connecting", "open", "closing", "closed"];
    return states[this.ws.readyState] as "connecting" | "open" | "closing" | "closed";
  }
}

// Global WebSocket client instance
let wsClient: EnhancedWebSocketClient | null = null;

/**
 * Get or create WebSocket client
 */
export function getWebSocketClient(baseUrl?: string): EnhancedWebSocketClient {
  if (!wsClient) {
    const wsUrl = baseUrl 
      ? baseUrl.replace("http://", "ws://").replace("https://", "wss://")
      : "ws://localhost:8000/ws";
    wsClient = new EnhancedWebSocketClient(wsUrl);
  }
  return wsClient;
}

