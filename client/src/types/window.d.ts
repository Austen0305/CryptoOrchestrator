/**
 * Window object extensions for CryptoOrchestrator
 * Provides type-safe access to custom window properties
 */

interface Window {
  /**
   * Custom API base URL (for Electron or custom deployments)
   * Set via: window.__API_BASE__ = 'https://api.example.com'
   */
  __API_BASE__?: string;

  /**
   * Custom WebSocket base URL (for Electron or custom deployments)
   * Set via: window.__WS_BASE__ = 'wss://ws.example.com'
   */
  __WS_BASE__?: string;

  /**
   * Vite API URL (set by Vite or Electron)
   */
  VITE_API_URL?: string;

  /**
   * React Query state for debugging (set by React Query DevTools)
   */
  __REACT_QUERY_STATE__?: unknown;
}

/**
 * Extended ImportMeta for Vite environment variables
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_WS_BASE_URL?: string;
  readonly VITE_API_URL?: string;
  readonly VITE_WS_URL?: string;
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_APP_VERSION?: string;
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly MODE: string;
  readonly SSR: boolean;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

export {};
