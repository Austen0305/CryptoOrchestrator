/**
 * Portfolio Screen for Mobile App
 * Displays user portfolio with real-time updates
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useWebSocket } from '../hooks/useWebSocket';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

interface Position {
  asset: string;
  amount: number;
  averagePrice: number;
  currentPrice: number;
  totalValue: number;
  profitLoss: number;
  profitLossPercent: number;
}

interface Portfolio {
  totalBalance: number;
  availableBalance: number;
  positions: Record<string, Position>;
  profitLoss24h: number;
  profitLossTotal: number;
  successfulTrades?: number;
  failedTrades?: number;
  totalTrades?: number;
  winRate?: number;
  averageWin?: number;
  averageLoss?: number;
}

export default function PortfolioScreen({ mode = 'paper' }: { mode?: 'paper' | 'real' }) {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // WebSocket for real-time updates
  const apiBaseUrl = API_BASE_URL;
  const wsBaseUrl = apiBaseUrl.replace('http://', 'ws://').replace('https://', 'wss://');
  const token = require('@react-native-async-storage/async-storage').default.getItem('auth_token');
  const { isConnected, lastMessage } = useWebSocket(
    token ? `${wsBaseUrl}/api/ws/portfolio?token=${token}` : undefined
  );

  useEffect(() => {
    fetchPortfolio();
  }, [mode]);

  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage);
        if (data.type === 'portfolio_update' && data.data) {
          setPortfolio(data.data);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      const token = await require('@react-native-async-storage/async-storage').default.getItem('auth_token');
      const normalizedMode = mode === 'live' ? 'real' : mode;
      
      const response = await fetch(`${API_BASE_URL}/api/portfolio/${normalizedMode}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch portfolio');
      }

      const data = await response.json();
      setPortfolio(data);
    } catch (error) {
      console.error('Failed to fetch portfolio:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchPortfolio();
  };

  if (loading && !portfolio) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <MaterialCommunityIcons name="loading" size={48} color="#6b7280" />
          <Text style={styles.loadingText}>Loading portfolio...</Text>
        </View>
      </View>
    );
  }

  if (!portfolio) {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <MaterialCommunityIcons name="alert-circle" size={48} color="#ef4444" />
          <Text style={styles.errorText}>Failed to load portfolio</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchPortfolio}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const positions = Object.values(portfolio.positions || {});

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Connection Status */}
      {isConnected && (
        <View style={styles.statusBar}>
          <MaterialCommunityIcons
            name="cloud-check"
            size={16}
            color="#22c55e"
          />
          <Text style={styles.statusBarText}>Live updates enabled</Text>
        </View>
      )}

      {/* Portfolio Summary */}
      <View style={styles.summaryCard}>
        <Text style={styles.summaryLabel}>Total Balance</Text>
        <Text style={styles.summaryValue}>
          ${portfolio.totalBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Text>
        
        <View style={styles.summaryRow}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryItemLabel}>Available</Text>
            <Text style={styles.summaryItemValue}>
              ${portfolio.availableBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Text>
          </View>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryItemLabel}>24h P&L</Text>
            <Text style={[styles.summaryItemValue, portfolio.profitLoss24h >= 0 ? styles.positive : styles.negative]}>
              {portfolio.profitLoss24h >= 0 ? '+' : ''}${portfolio.profitLoss24h.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Text>
          </View>
        </View>
      </View>

      {/* Trading Stats */}
      {(portfolio.totalTrades !== undefined && portfolio.totalTrades > 0) && (
        <View style={styles.statsCard}>
          <Text style={styles.cardTitle}>Trading Stats</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Total Trades</Text>
              <Text style={styles.statValue}>{portfolio.totalTrades}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Win Rate</Text>
              <Text style={styles.statValue}>
                {portfolio.winRate ? (portfolio.winRate * 100).toFixed(1) : '0'}%
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Avg Win</Text>
              <Text style={[styles.statValue, styles.positive]}>
                ${portfolio.averageWin?.toFixed(2) || '0.00'}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Avg Loss</Text>
              <Text style={[styles.statValue, styles.negative]}>
                ${portfolio.averageLoss?.toFixed(2) || '0.00'}
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* Positions */}
      <View style={styles.positionsCard}>
        <Text style={styles.cardTitle}>Positions</Text>
        {positions.length === 0 ? (
          <View style={styles.emptyState}>
            <MaterialCommunityIcons name="wallet-outline" size={48} color="#6b7280" />
            <Text style={styles.emptyText}>No positions</Text>
          </View>
        ) : (
          positions.map((position) => (
            <View key={position.asset} style={styles.positionItem}>
              <View style={styles.positionHeader}>
                <Text style={styles.positionAsset}>{position.asset}</Text>
                <View style={styles.positionValue}>
                  <Text style={styles.positionValueText}>
                    ${position.totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Text>
                </View>
              </View>
              <View style={styles.positionDetails}>
                <View style={styles.positionDetailItem}>
                  <Text style={styles.positionDetailLabel}>Amount</Text>
                  <Text style={styles.positionDetailValue}>{position.amount}</Text>
                </View>
                <View style={styles.positionDetailItem}>
                  <Text style={styles.positionDetailLabel}>Avg Price</Text>
                  <Text style={styles.positionDetailValue}>
                    ${position.averagePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Text>
                </View>
                <View style={styles.positionDetailItem}>
                  <Text style={styles.positionDetailLabel}>Current</Text>
                  <Text style={styles.positionDetailValue}>
                    ${position.currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Text>
                </View>
              </View>
              <View style={styles.positionPnl}>
                <MaterialCommunityIcons
                  name={position.profitLoss >= 0 ? 'trending-up' : 'trending-down'}
                  size={16}
                  color={position.profitLoss >= 0 ? '#22c55e' : '#ef4444'}
                />
                <Text
                  style={[
                    styles.positionPnlText,
                    position.profitLoss >= 0 ? styles.positive : styles.negative,
                  ]}
                >
                  {position.profitLoss >= 0 ? '+' : ''}${position.profitLoss.toFixed(2)} (
                  {position.profitLossPercent >= 0 ? '+' : ''}
                  {position.profitLossPercent.toFixed(2)}%)
                </Text>
              </View>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#9ca3af',
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  errorText: {
    color: '#ef4444',
    marginTop: 16,
    fontSize: 16,
  },
  retryButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#f7931a',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  statusBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    backgroundColor: '#22c55e',
    opacity: 0.1,
  },
  statusBarText: {
    color: '#22c55e',
    fontSize: 12,
    marginLeft: 4,
  },
  summaryCard: {
    backgroundColor: '#1e293b',
    margin: 16,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  summaryLabel: {
    color: '#9ca3af',
    fontSize: 14,
    marginBottom: 8,
  },
  summaryValue: {
    color: '#fff',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  summaryItem: {
    flex: 1,
  },
  summaryItemLabel: {
    color: '#9ca3af',
    fontSize: 12,
    marginBottom: 4,
  },
  summaryItemValue: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  statsCard: {
    backgroundColor: '#1e293b',
    margin: 16,
    marginTop: 0,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  cardTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statItem: {
    width: '48%',
    marginBottom: 16,
  },
  statLabel: {
    color: '#9ca3af',
    fontSize: 12,
    marginBottom: 4,
  },
  statValue: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '600',
  },
  positionsCard: {
    backgroundColor: '#1e293b',
    margin: 16,
    marginTop: 0,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  positionItem: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  positionAsset: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  positionValue: {
    alignItems: 'flex-end',
  },
  positionValueText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  positionDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  positionDetailItem: {
    flex: 1,
  },
  positionDetailLabel: {
    color: '#9ca3af',
    fontSize: 12,
    marginBottom: 4,
  },
  positionDetailValue: {
    color: '#fff',
    fontSize: 14,
  },
  positionPnl: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  positionPnlText: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 4,
  },
  positive: {
    color: '#22c55e',
  },
  negative: {
    color: '#ef4444',
  },
  emptyState: {
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    color: '#9ca3af',
    marginTop: 16,
  },
});

