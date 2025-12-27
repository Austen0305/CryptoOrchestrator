/**
 * API Service for CryptoOrchestrator Mobile
 * Complete API client with authentication and error handling
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '@env';

const API_URL = API_BASE_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error getting auth token:', error);
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      await AsyncStorage.removeItem('auth_token');
      // Could dispatch event to trigger login screen
    }
    return Promise.reject(error);
  }
);

export default api;

// API Service Methods
export const apiService = {
  // Authentication
  login: (email: string, password: string) =>
    api.post('/api/auth/login', { email, password }),
  
  register: (data: {
    email: string;
    password: string;
    username?: string;
    first_name?: string;
    last_name?: string;
  }) => api.post('/api/auth/register', data),
  
  logout: () => api.post('/api/auth/logout'),
  
  getCurrentUser: () => api.get('/api/auth/me'),
  
  // Portfolio
  getPortfolio: (mode: 'paper' | 'real' | 'live') => {
    const normalizedMode = mode === 'live' ? 'real' : mode;
    return api.get(`/api/portfolio/${normalizedMode}`);
  },
  
  // Wallets
  getWallets: () => api.get('/api/wallet/'),
  
  getWalletBalance: (walletId: string, tokenAddress?: string) => {
    const url = `/api/wallet/${walletId}/balance`;
    return api.get(url, {
      params: tokenAddress ? { token_address: tokenAddress } : {},
    });
  },
  
  getDepositAddress: (chainId: number) =>
    api.get(`/api/wallet/deposit-address/${chainId}`),
  
  // Trading
  getTrades: (params?: {
    mode?: 'paper' | 'real';
    limit?: number;
    offset?: number;
  }) => api.get('/api/trades', { params }),
  
  createTrade: (data: {
    pair: string;
    side: 'buy' | 'sell';
    type: 'market' | 'limit';
    amount: number;
    price?: number;
    mode?: 'paper' | 'real';
  }) => api.post('/api/trades', data),
  
  // DEX Trading
  getDexQuote: (data: {
    token_in: string;
    token_out: string;
    amount: number;
    chain_id: number;
  }) => api.post('/api/dex/quote', data),
  
  executeDexSwap: (data: {
    token_in: string;
    token_out: string;
    amount: number;
    chain_id: number;
    slippage?: number;
    aggregator?: string;
  }) => api.post('/api/dex/swap', data),
  
  // Bots
  getBots: () => api.get('/api/bots'),
  
  getBot: (botId: string) => api.get(`/api/bots/${botId}`),
  
  createBot: (data: {
    name: string;
    strategy: string;
    trading_pair: string;
    initial_balance?: number;
    risk_limits?: Record<string, number>;
  }) => api.post('/api/bots', data),
  
  updateBot: (botId: string, data: Partial<{
    name: string;
    status: string;
    risk_limits: Record<string, number>;
  }>) => api.patch(`/api/bots/${botId}`, data),
  
  startBot: (botId: string) => api.post(`/api/bots/${botId}/start`),
  
  stopBot: (botId: string) => api.post(`/api/bots/${botId}/stop`),
  
  deleteBot: (botId: string) => api.delete(`/api/bots/${botId}`),
  
  // Market Data
  getMarketData: (symbols?: string[]) =>
    api.get('/api/markets/prices', {
      params: symbols ? { symbols: symbols.join(',') } : {},
    }),
  
  // User Profile
  getUserProfile: () => api.get('/api/auth/me'),
  
  updateUserProfile: (data: {
    username?: string;
    first_name?: string;
    last_name?: string;
    email?: string;
  }) => api.patch('/api/auth/me', data),
  
  changePassword: (data: {
    current_password: string;
    new_password: string;
  }) => api.post('/api/auth/change-password', data),
  
  // Settings
  getPreferences: () => api.get('/api/preferences'),
  
  updatePreferences: (data: Record<string, any>) =>
    api.patch('/api/preferences', data),
  
  // Notifications
  subscribePushNotifications: (data: {
    expo_push_token?: string;
    endpoint?: string;
    keys?: {
      p256dh: string;
      auth: string;
    };
    platform?: string;
    device_id?: string;
    app_version?: string;
  }) => api.post('/api/notifications/subscribe', data),
  
  unsubscribePushNotifications: (data: { 
    endpoint?: string;
    expo_push_token?: string;
  }) => api.post('/api/notifications/unsubscribe', data),
  
  // Health
  healthCheck: () => api.get('/health'),
};
