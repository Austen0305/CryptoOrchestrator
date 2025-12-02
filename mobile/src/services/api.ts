/**
 * API Service for CryptoOrchestrator Mobile
 */

import axios from 'axios';
import { API_BASE_URL } from '@env';

const api = axios.create({
  baseURL: API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add authentication token if available
    // const token = await getStoredToken();
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      console.log('Unauthorized access - redirect to login');
    }
    return Promise.reject(error);
  }
);

export default api;

// API Methods
export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),

  // Portfolio
  getPortfolio: (userId: string) => 
    api.get(`/api/portfolio?user_id=${userId}`),

  // Trading
  getTrades: (userId: string) => 
    api.get(`/api/trades?user_id=${userId}`),

  // Market data
  getMarketData: (symbols: string[]) => 
    api.get(`/api/market/prices?symbols=${symbols.join(',')}`),

  // Rebalancing
  analyzeRebalance: (data: any) =>
    api.post('/api/portfolio/rebalance/analyze', data),

  // Backtesting
  runBacktest: (data: any) =>
    api.post('/api/backtest/run', data),

  // Arbitrage
  getArbitrageOpportunities: () =>
    api.get('/api/arbitrage/opportunities'),

  // Marketplace
  getSignals: () =>
    api.get('/api/marketplace/signals'),
};
