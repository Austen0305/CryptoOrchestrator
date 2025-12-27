/**
 * Frontend Constants
 * Shared constants for the frontend application
 */

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login',
    REGISTER: '/api/auth/register',
    LOGOUT: '/api/auth/logout',
    REFRESH: '/api/auth/refresh',
  },
  BOTS: {
    LIST: '/api/bots',
    CREATE: '/api/bots',
    UPDATE: (id: string) => `/api/bots/${id}`,
    DELETE: (id: string) => `/api/bots/${id}`,
  },
  TRADES: {
    LIST: '/api/trades',
    CREATE: '/api/trades',
    GET: (id: string) => `/api/trades/${id}`,
  },
  PORTFOLIO: {
    GET: (mode: string) => `/api/portfolio?mode=${mode}`,
    SUMMARY: '/api/portfolio/summary',
  },
} as const;

export const QUERY_KEYS = {
  BOTS: ['bots'] as const,
  BOT: (id: string) => ['bots', id] as const,
  TRADES: ['trades'] as const,
  TRADE: (id: string) => ['trades', id] as const,
  PORTFOLIO: (mode: string) => ['portfolio', mode] as const,
  USER: ['user'] as const,
} as const;

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'auth_user',
  THEME: 'theme',
  PREFERENCES: 'preferences',
} as const;

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  BOTS: '/bots',
  MARKETS: '/markets',
  ANALYTICS: '/analytics',
  SETTINGS: '/settings',
} as const;

export const BREAKPOINTS = {
  MOBILE: 768,
  TABLET: 1024,
  DESKTOP: 1280,
} as const;

export const ANIMATION_DURATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
} as const;

export const DEBOUNCE_DELAY = {
  SEARCH: 300,
  INPUT: 500,
  SCROLL: 100,
} as const;

export const THROTTLE_DELAY = {
  RESIZE: 100,
  SCROLL: 16,
  MOUSEMOVE: 16,
} as const;

