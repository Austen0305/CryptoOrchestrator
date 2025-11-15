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
  name: string;
  status: 'active' | 'paused' | 'stopped';
  profit24h: number;
  profitPercent: number;
}

export const DashboardScreen: React.FC = () => {
  const [refreshing, setRefreshing] = useState(false);
  const [portfolioHistory, setPortfolioHistory] = useState<number[]>([]);

  // Fetch portfolio stats
  const { data: stats, refetch: refetchStats } = useQuery<PortfolioStats>({
    queryKey: ['portfolio', 'stats'],
    queryFn: () => api.get('/portfolio/stats'),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch active bots
  const { data: bots, refetch: refetchBots } = useQuery<Bot[]>({
    queryKey: ['bots', 'active'],
    queryFn: () => api.get('/bots?status=active'),
    refetchInterval: 30000,
  });

  // WebSocket for real-time updates
  const { isConnected, lastMessage } = useWebSocket('/ws/portfolio');

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage);
      if (data.type === 'portfolio_update') {
        setPortfolioHistory(prev => [...prev.slice(-20), data.value]);
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
      {/* Connection Status */}
      <View style={styles.statusBar}>
        <Icon
          name={isConnected ? 'cloud-check' : 'cloud-off-outline'}
          size={16}
          color={isConnected ? '#22c55e' : '#ef4444'}
        />
        <Text style={styles.statusText}>
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
          <Icon
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
          <Text style={styles.statValue}>{stats?.activeBots ?? 0}</Text>
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
        {bots?.slice(0, 3).map((bot) => (
          <TouchableOpacity key={bot.id} style={styles.botCard}>
            <View style={styles.botHeader}>
              <View style={styles.botInfo}>
                <Text style={styles.botName}>{bot.name}</Text>
                <View style={[styles.statusBadge, styles[`status_${bot.status}`]]}>
                  <Text style={styles.statusText}>{bot.status}</Text>
                </View>
              </View>
              <View style={styles.botProfit}>
                <Text
                  style={[
                    styles.profitText,
                    { color: bot.profit24h >= 0 ? '#22c55e' : '#ef4444' },
                  ]}
                >
                  {bot.profit24h >= 0 ? '+' : ''}${bot.profit24h.toFixed(2)}
                </Text>
                <Text style={styles.profitPercent}>
                  ({bot.profitPercent.toFixed(2)}%)
                </Text>
              </View>
            </View>
          </TouchableOpacity>
        ))}
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
  statusText: {
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
});
