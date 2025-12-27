/// <reference types="vite/client" />

// Window global properties for Electron/injected globals
interface Window {
  __API_BASE__?: string;
  __WS_BASE__?: string;
}

// Extend ImportMeta for Vite environment variables
interface ImportMetaEnv {
  readonly VITE_APP_VERSION?: string;
  readonly VITE_API_URL?: string;
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_WS_URL?: string;
  readonly VITE_WS_BASE_URL?: string;
  readonly VITE_SENTRY_DSN?: string;
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly MODE: string;
  readonly SSR: boolean;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
