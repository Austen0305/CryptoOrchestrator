/**
 * Import.meta extensions for Vite environment variables
 * Provides type-safe access to Vite environment variables
 */

interface ImportMetaEnv {
  /**
   * API base URL for backend requests
   * Default: http://localhost:8000
   */
  readonly VITE_API_BASE_URL?: string;

  /**
   * WebSocket base URL for real-time connections
   * Default: ws://localhost:8000
   */
  readonly VITE_WS_BASE_URL?: string;

  /**
   * Development mode flag
   * Set by Vite automatically
   */
  readonly DEV: boolean;

  /**
   * Production mode flag
   * Set by Vite automatically
   */
  readonly PROD: boolean;

  /**
   * Mode (development, production, etc.)
   * Set by Vite automatically
   */
  readonly MODE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

export {};
