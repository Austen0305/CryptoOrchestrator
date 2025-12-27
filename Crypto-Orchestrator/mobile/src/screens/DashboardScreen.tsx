/**
 * Dashboard Screen - Main overview of portfolio and active bots
 */
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import OfflineIndicator from '../components/OfflineIndicator';

const { width } = Dimensions.get('window');

interface PortfolioStats {
  totalValue: number;
  change24h: number;
  changePercent24h: number;
  activeBots: number;
  totalProfit: number;
}

interface Bot {
  id: string;
  name?: string;
  status?: string;
  active?: boolean;
  is_active?: boolean;
  profit24h?: number;
  profitPercent?: number;
  performance_data?: any;
  [key: string]: any; // Allow additional properties
}

export const DashboardScreen: React.FC = () => {
  const [refreshing, setRefreshing] = useState(false);
  const [portfolioHistory, setPortfolioHistory] = useState<number[]>([]);

  // Fetch portfolio stats (paper trading mode)
  const { data: portfolioResponse, refetch: refetchStats } = useQuery({
    queryKey: ['portfolio', 'paper'],
    queryFn: async () => {
      try {
        const response = await api.get('/api/portfolio/paper');
        return response.data;
      } catch (error) {
        console.error('Failed to fetch portfolio:', error);
        // Return empty portfolio on error (no mock data)
        return {
          totalBalance: 0.0,
          availableBalance: 0.0,
          positions: {},
          profitLoss24h: 0,
          profitLossTotal: 0,
        };
      }
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Extract portfolio stats from response
  const stats: PortfolioStats | undefined = portfolioResponse ? {
    totalValue: portfolioResponse.totalBalance || 0,
    change24h: portfolioResponse.profitLoss24h || 0,
    changePercent24h: portfolioResponse.totalBalance 
      ? ((portfolioResponse.profitLoss24h || 0) / (portfolioResponse.totalBalance - (portfolioResponse.profitLoss24h || 0))) * 100 
      : 0,
    activeBots: 0, // Will be updated from bots query
    totalProfit: portfolioResponse.profitLossTotal || 0,
  } : undefined;

  // Fetch active bots
  const { data: botsResponse, refetch: refetchBots } = useQuery({
    queryKey: ['bots', 'active'],
    queryFn: async () => {
      try {
        const response = await api.get('/api/bots');
        // Filter active bots from response
        const bots = Array.isArray(response.data) ? response.data : [];
        return bots.filter((bot: Bot) => bot.is_active || bot.status === 'active');
      } catch (error) {
        console.error('Failed to fetch bots:', error);
        return [];
      }
    },
    refetchInterval: 30000,
  });

  // Extract bots from response
  const bots: Bot[] = botsResponse || [];
  
  // Update stats with active bots count
  if (stats && bots.length !== undefined) {
    stats.activeBots = bots.length;
  }

  // WebSocket for real-time updates - construct URL from API base URL
  // Note: WebSocket connection is managed by useWebSocket hook
  const apiBaseUrl = process.env.API_BASE_URL || 'http://localhost:8000';
  const wsBaseUrl = apiBaseUrl.replace('http://', 'ws://').replace('https://', 'wss://');
  const { isConnected, lastMessage } = useWebSocket(`${wsBaseUrl}/ws`);

  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage);
        if (data.type === 'portfolio_update' || data.type === 'market_data') {
          const value = data.value || data.totalBalance || data.price || 0;
          setPortfolioHistory(prev => {
            const newHistory = [...prev, value];
            return newHistory.slice(-20); // Keep last 20 values
          });
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([refetchStats(), refetchBots()]);
    setRefreshing(false);
  };

  const chartData = {
    labels: portfolioHistory.map((_, i) => i.toString()).slice(-7),
    datasets: [
      {
        data: portfolioHistory.length > 0 ? portfolioHistory.slice(-7) : [0],
        color: (opacity = 1) => `rgba(34, 197, 94, ${opacity})`,
        strokeWidth: 2,
      },
    ],
  };

  const isPositive = (stats?.change24h ?? 0) >= 0;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }
    >
      {/* Offline Indicator */}
      <OfflineIndicator />

      {/* Connection Status */}
      <View style={styles.statusBar}>
        <MaterialCommunityIcons
          name={isConnected ? 'cloud-check' : 'cloud-off-outline'}
          size={16}
          color={isConnected ? '#22c55e' : '#ef4444'}
        />
        <Text style={styles.statusBarText}>
          {isConnected ? 'Live' : 'Reconnecting...'}
        </Text>
      </View>

      {/* Portfolio Value Card */}
      <View style={styles.portfolioCard}>
        <Text style={styles.label}>Total Portfolio Value</Text>
        <Text style={styles.portfolioValue}>
          ${(stats?.totalValue ?? 0).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </Text>
        <View style={styles.changeRow}>
          <MaterialCommunityIcons
            name={isPositive ? 'trending-up' : 'trending-down'}
            size={20}
            color={isPositive ? '#22c55e' : '#ef4444'}
          />
          <Text style={[styles.change, { color: isPositive ? '#22c55e' : '#ef4444' }]}>
            ${Math.abs(stats?.change24h ?? 0).toFixed(2)} (
            {Math.abs(stats?.changePercent24h ?? 0).toFixed(2)}%)
          </Text>
        </View>
      </View>

      {/* Portfolio Chart */}
      {portfolioHistory.length > 0 && (
        <View style={styles.chartCard}>
          <Text style={styles.cardTitle}>24H Performance</Text>
          <LineChart
            data={chartData}
            width={width - 40}
            height={200}
            chartConfig={{
              backgroundColor: '#1e293b',
              backgroundGradientFrom: '#1e293b',
              backgroundGradientTo: '#0f172a',
              decimalPlaces: 0,
              color: (opacity = 1) => `rgba(34, 197, 94, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(148, 163, 184, ${opacity})`,
              style: {
                borderRadius: 16,
              },
              propsForDots: {
                r: '4',
                strokeWidth: '2',
                stroke: '#22c55e',
              },
            }}
            bezier
            style={styles.chart}
          />
        </View>
      )}

      {/* Quick Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <MaterialCommunityIcons name="robot" size={24} color="#3b82f6" />
          <Text style={styles.statValue}>{bots?.length ?? 0}</Text>
          <Text style={styles.statLabel}>Active Bots</Text>
        </View>
        <View style={styles.statCard}>
          <MaterialCommunityIcons name="currency-usd" size={24} color="#22c55e" />
          <Text style={styles.statValue}>
            ${(stats?.totalProfit ?? 0).toFixed(2)}
          </Text>
          <Text style={styles.statLabel}>Total Profit</Text>
        </View>
      </View>

      {/* Active Bots */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Active Bots</Text>
          <TouchableOpacity>
            <Text style={styles.seeAll}>See All</Text>
          </TouchableOpacity>
        </View>
        {bots && bots.length > 0 ? (
          bots.slice(0, 3).map((bot) => {
            const profit24h = bot.profit24h || 0;
            const profitPercent = bot.profitPercent || 0;
            const status = bot.status || (bot.active ? 'active' : bot.is_active ? 'active' : 'stopped');
            const botName = bot.name || 'Unnamed Bot';
            
            return (
              <TouchableOpacity key={bot.id} style={styles.botCard}>
                <View style={styles.botHeader}>
                  <View style={styles.botInfo}>
                    <Text style={styles.botName}>{botName}</Text>
                    <View style={[styles.statusBadge, styles[`status_${status}`] || styles.status_stopped]}>
                      <Text style={styles.statusText}>{status}</Text>
                    </View>
                  </View>
                  <View style={styles.botProfit}>
                    <Text
                      style={[
                        styles.profitText,
                        { color: profit24h >= 0 ? '#22c55e' : '#ef4444' },
                      ]}
                    >
                      {profit24h >= 0 ? '+' : ''}${profit24h.toFixed(2)}
                    </Text>
                    <Text style={styles.profitPercent}>
                      ({profitPercent.toFixed(2)}%)
                    </Text>
                  </View>
                </View>
              </TouchableOpacity>
            );
          })
        ) : (
          <View style={styles.emptyState}>
            <MaterialCommunityIcons name="robot-off" size={48} color="#6b7280" />
            <Text style={styles.emptyText}>No active bots</Text>
            <Text style={styles.emptySubtext}>Create a bot to start trading</Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  statusBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    backgroundColor: '#1e293b',
  },
  statusBarText: {
    color: '#94a3b8',
    fontSize: 12,
    marginLeft: 6,
    fontWeight: '600',
  },
  portfolioCard: {
    margin: 20,
    padding: 24,
    backgroundColor: '#1e293b',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  label: {
    color: '#94a3b8',
    fontSize: 14,
    marginBottom: 8,
  },
  portfolioValue: {
    color: '#ffffff',
    fontSize: 36,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  changeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  change: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 6,
  },
  chartCard: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 16,
    backgroundColor: '#1e293b',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  cardTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  statsRow: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginBottom: 20,
    gap: 12,
  },
  statCard: {
    flex: 1,
    padding: 20,
    backgroundColor: '#1e293b',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#334155',
    alignItems: 'center',
  },
  statValue: {
    color: '#ffffff',
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 8,
  },
  statLabel: {
    color: '#94a3b8',
    fontSize: 12,
    marginTop: 4,
  },
  section: {
    marginHorizontal: 20,
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  seeAll: {
    color: '#3b82f6',
    fontSize: 14,
    fontWeight: '600',
  },
  botCard: {
    padding: 16,
    backgroundColor: '#1e293b',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
    marginBottom: 12,
  },
  botHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  botInfo: {
    flex: 1,
  },
  botName: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  status_active: {
    backgroundColor: '#22c55e20',
  },
  status_paused: {
    backgroundColor: '#f59e0b20',
  },
  status_stopped: {
    backgroundColor: '#ef444420',
  },
  statusText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  botProfit: {
    alignItems: 'flex-end',
  },
  profitText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  profitPercent: {
    color: '#94a3b8',
    fontSize: 12,
    marginTop: 2,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
    backgroundColor: '#1e293b',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
    marginTop: 12,
  },
  emptyText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
  },
  emptySubtext: {
    color: '#94a3b8',
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
  },
});
