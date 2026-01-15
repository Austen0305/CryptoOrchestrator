/**
 * Portfolio Screen for Mobile App
 * Displays user portfolio with multi-chain wallet support and real-time updates
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  // ScrollView, // Removed as we use FlashList
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView, // kept for horizontal scroll in header
} from "react-native";
import { FlashList } from "@shopify/flash-list";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { useQuery } from "@tanstack/react-query";
import { useWebSocket } from "../hooks/useWebSocket";
import { api } from "../services/api";
import AsyncStorage from "@react-native-async-storage/async-storage";

import { useOffline } from "../hooks/useOffline";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";

interface Position {
  asset: string;
  amount: number;
  averagePrice: number;
  currentPrice: number;
  totalValue: number;
  profitLoss: number;
  profitLossPercent: number;
}

interface Wallet {
  id: string;
  address: string;
  chain_id: number;
  chain_name: string;
  balance: number;
  balance_usd: number;
  token_balances?: Array<{
    symbol: string;
    balance: number;
    balance_usd: number;
  }>;
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
  wallets?: Wallet[];
}

interface PortfolioScreenProps {
  mode?: "paper" | "real" | "live";
}

export default function PortfolioScreen({ mode = "paper" }: PortfolioScreenProps) {
  const { isOnline } = useOffline();
  const [refreshing, setRefreshing] = useState(false);
  const [selectedChain, setSelectedChain] = useState<number | null>(null);

  // Fetch portfolio data
  const {
    data: portfolio,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["portfolio", mode],
    queryFn: async () => {
      const normalizedMode = mode === "live" ? "real" : mode;
      return await api.get<Portfolio>("portfolio/" + normalizedMode);
    },
    refetchInterval: isOnline ? 30000 : false, // Only refresh when online
    enabled: isOnline, // Only fetch when online
  });

  // Fetch wallets
  const { data: wallets } = useQuery({
    queryKey: ["wallets"],
    queryFn: async () => {
      return await api.get<Wallet[]>("wallets");
    },
    enabled: isOnline, // Only fetch when online
  });

  // WebSocket for real-time updates
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    AsyncStorage.getItem("auth_token").then(setToken);
  }, []);

  const wsBaseUrl = API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://");
  const { isConnected, lastMessage } = useWebSocket(
    token && isOnline ? `${wsBaseUrl}/api/ws/portfolio?token=${token}` : undefined
  );

  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage);
        if (data.type === "portfolio_update" && data.data) {
          // Invalidate query to refetch
          refetch();
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    }
  }, [lastMessage, refetch]);

  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
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
          <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const positions = Object.values(portfolio.positions);
  const displayWallets = wallets ?? portfolio.wallets ?? [];
  const uniqueChains = Array.from(new Set(displayWallets.map((w: Wallet) => w.chain_id))).sort();

  return (
    // @ts-ignore
    <FlashList
      data={positions}
      renderItem={({ item: position }) => (
        <View style={styles.positionItem}>
          <View style={styles.positionHeader}>
            <Text style={styles.positionAsset}>{position.asset}</Text>
            <View style={styles.positionValue}>
              <Text style={styles.positionValueText}>
                $
                {position.totalValue.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
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
                $
                {position.averagePrice.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>
            <View style={styles.positionDetailItem}>
              <Text style={styles.positionDetailLabel}>Current</Text>
              <Text style={styles.positionDetailValue}>
                $
                {position.currentPrice.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>
          </View>
          <View style={styles.positionPnl}>
            <MaterialCommunityIcons
              name={position.profitLoss >= 0 ? "trending-up" : "trending-down"}
              size={16}
              color={position.profitLoss >= 0 ? "#22c55e" : "#ef4444"}
            />
            <Text
              style={[
                styles.positionPnlText,
                position.profitLoss >= 0 ? styles.positive : styles.negative,
              ]}
            >
              {position.profitLoss >= 0 ? "+" : ""}${position.profitLoss.toFixed(2)} (
              {position.profitLossPercent >= 0 ? "+" : ""}
              {position.profitLossPercent.toFixed(2)}%)
            </Text>
          </View>
        </View>
      )}
      // @ts-ignore
      estimatedItemSize={140}
      contentContainerStyle={{ paddingBottom: 20 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      ListHeaderComponent={
        <>
          {/* Connection Status */}
          {isConnected && (
            <View style={styles.statusBar}>
              <MaterialCommunityIcons name="cloud-check" size={16} color="#22c55e" />
              <Text style={styles.statusBarText}>Live updates enabled</Text>
            </View>
          )}

          {/* Portfolio Summary */}
          <View style={styles.summaryCard}>
            <Text style={styles.summaryLabel}>Total Balance</Text>
            <Text style={styles.summaryValue}>
              $
              {portfolio.totalBalance.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </Text>

            <View style={styles.summaryRow}>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryItemLabel}>Available</Text>
                <Text style={styles.summaryItemValue}>
                  $
                  {portfolio.availableBalance.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </Text>
              </View>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryItemLabel}>24h P&L</Text>
                <Text
                  style={[
                    styles.summaryItemValue,
                    portfolio.profitLoss24h >= 0 ? styles.positive : styles.negative,
                  ]}
                >
                  {portfolio.profitLoss24h >= 0 ? "+" : ""}$
                  {portfolio.profitLoss24h.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </Text>
              </View>
            </View>
          </View>

          {/* Multi-Chain Wallets */}
          {displayWallets.length > 0 && (
            <View style={styles.walletsCard}>
              <Text style={styles.cardTitle}>Multi-Chain Wallets</Text>

              {/* Chain Filter */}
              {uniqueChains.length > 1 && (
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  style={styles.chainFilter}
                >
                  <TouchableOpacity
                    style={[styles.chainChip, selectedChain === null && styles.chainChipActive]}
                    onPress={() => setSelectedChain(null)}
                  >
                    <Text
                      style={[
                        styles.chainChipText,
                        selectedChain === null && styles.chainChipTextActive,
                      ]}
                    >
                      All Chains
                    </Text>
                  </TouchableOpacity>
                  {uniqueChains.map((chainId) => {
                    const wallet = displayWallets.find((w) => w.chain_id === chainId);
                    return (
                      <TouchableOpacity
                        key={chainId}
                        style={[
                          styles.chainChip,
                          selectedChain === chainId && styles.chainChipActive,
                        ]}
                        onPress={() => setSelectedChain(chainId)}
                      >
                        <Text
                          style={[
                            styles.chainChipText,
                            selectedChain === chainId && styles.chainChipTextActive,
                          ]}
                        >
                          {wallet?.chain_name ?? `Chain ${chainId}`}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </ScrollView>
              )}

              {/* Wallet List */}
              {displayWallets
                .filter((w) => selectedChain === null || w.chain_id === selectedChain)
                .map((wallet) => (
                  <View key={wallet.id} style={styles.walletItem}>
                    <View style={styles.walletHeader}>
                      <View style={styles.walletInfo}>
                        <MaterialCommunityIcons name="wallet" size={24} color="#3b82f6" />
                        <View style={styles.walletDetails}>
                          <Text style={styles.walletChain}>{wallet.chain_name}</Text>
                          <Text style={styles.walletAddress} numberOfLines={1}>
                            {wallet.address.slice(0, 6)}...{wallet.address.slice(-4)}
                          </Text>
                        </View>
                      </View>
                      <View style={styles.walletBalance}>
                        <Text style={styles.walletBalanceValue}>
                          $
                          {wallet.balance_usd.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </Text>
                        <Text style={styles.walletBalanceNative}>
                          {wallet.balance.toFixed(4)}{" "}
                          {wallet.chain_name === "Ethereum" ? "ETH" : "Native"}
                        </Text>
                      </View>
                    </View>

                    {/* Token Balances */}
                    {wallet.token_balances && wallet.token_balances.length > 0 && (
                      <View style={styles.tokenBalances}>
                        {wallet.token_balances.map(
                          (tokenBal: { symbol: string; balance_usd: number }, idx: number) => (
                            <View key={idx} style={styles.tokenItem}>
                              <Text style={styles.tokenSymbol}>{tokenBal.symbol}</Text>
                              <Text style={styles.tokenBalance}>
                                ${tokenBal.balance_usd.toFixed(2)}
                              </Text>
                            </View>
                          )
                        )}
                      </View>
                    )}
                  </View>
                ))}
            </View>
          )}

          {/* Trading Stats */}
          {portfolio.totalTrades !== undefined && portfolio.totalTrades > 0 && (
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
                    {portfolio.winRate ? (portfolio.winRate * 100).toFixed(1) : "0"}%
                  </Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>Avg Win</Text>
                  <Text style={[styles.statValue, styles.positive]}>
                    ${portfolio.averageWin?.toFixed(2) ?? "0.00"}
                  </Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>Avg Loss</Text>
                  <Text style={[styles.statValue, styles.negative]}>
                    ${portfolio.averageLoss?.toFixed(2) ?? "0.00"}
                  </Text>
                </View>
              </View>
            </View>
          )}

          <View style={{ marginHorizontal: 16, marginTop: 16, marginBottom: 8 }}>
            <Text style={styles.cardTitle}>Positions</Text>
          </View>
        </>
      }
      ListEmptyComponent={
        <View style={styles.emptyState}>
          <MaterialCommunityIcons name="wallet-outline" size={48} color="#6b7280" />
          <Text style={styles.emptyText}>No positions</Text>
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    color: "#9ca3af",
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  errorText: {
    color: "#ef4444",
    marginTop: 16,
    fontSize: 16,
  },
  retryButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: "#3b82f6",
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#fff",
    fontWeight: "600",
  },
  statusBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 8,
    backgroundColor: "#22c55e",
    opacity: 0.1,
  },
  statusBarText: {
    color: "#22c55e",
    fontSize: 12,
    marginLeft: 4,
  },
  summaryCard: {
    backgroundColor: "#1e293b",
    margin: 16,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
  },
  summaryLabel: {
    color: "#9ca3af",
    fontSize: 14,
    marginBottom: 8,
  },
  summaryValue: {
    color: "#fff",
    fontSize: 32,
    fontWeight: "bold",
    marginBottom: 16,
  },
  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  summaryItem: {
    flex: 1,
  },
  summaryItemLabel: {
    color: "#9ca3af",
    fontSize: 12,
    marginBottom: 4,
  },
  summaryItemValue: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "600",
  },
  walletsCard: {
    backgroundColor: "#1e293b",
    margin: 16,
    marginTop: 0,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
  },
  cardTitle: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "600",
    marginBottom: 16,
  },
  chainFilter: {
    marginBottom: 16,
  },
  chainChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: "#0f172a",
    borderWidth: 1,
    borderColor: "#334155",
    marginRight: 8,
  },
  chainChipActive: {
    backgroundColor: "#3b82f6",
    borderColor: "#3b82f6",
  },
  chainChipText: {
    color: "#9ca3af",
    fontSize: 14,
    fontWeight: "500",
  },
  chainChipTextActive: {
    color: "#fff",
  },
  walletItem: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#334155",
  },
  walletHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  walletInfo: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  walletDetails: {
    marginLeft: 12,
    flex: 1,
  },
  walletChain: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  walletAddress: {
    color: "#9ca3af",
    fontSize: 12,
    marginTop: 4,
  },
  walletBalance: {
    alignItems: "flex-end",
  },
  walletBalanceValue: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "600",
  },
  walletBalanceNative: {
    color: "#9ca3af",
    fontSize: 12,
    marginTop: 4,
  },
  tokenBalances: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#334155",
  },
  tokenItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  tokenSymbol: {
    color: "#9ca3af",
    fontSize: 14,
  },
  tokenBalance: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "500",
  },
  statsCard: {
    backgroundColor: "#1e293b",
    margin: 16,
    marginTop: 0,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
  },
  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  statItem: {
    width: "48%",
    marginBottom: 16,
  },
  statLabel: {
    color: "#9ca3af",
    fontSize: 12,
    marginBottom: 4,
  },
  statValue: {
    color: "#fff",
    fontSize: 20,
    fontWeight: "600",
  },
  positionsCard: {
    backgroundColor: "#1e293b",
    margin: 16,
    marginTop: 0,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
  },
  positionItem: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#334155",
  },
  positionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  positionAsset: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "600",
  },
  positionValue: {
    alignItems: "flex-end",
  },
  positionValueText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "600",
  },
  positionDetails: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  positionDetailItem: {
    flex: 1,
  },
  positionDetailLabel: {
    color: "#9ca3af",
    fontSize: 12,
    marginBottom: 4,
  },
  positionDetailValue: {
    color: "#fff",
    fontSize: 14,
  },
  positionPnl: {
    flexDirection: "row",
    alignItems: "center",
  },
  positionPnlText: {
    fontSize: 16,
    fontWeight: "600",
    marginLeft: 4,
  },
  positive: {
    color: "#22c55e",
  },
  negative: {
    color: "#ef4444",
  },
  emptyState: {
    alignItems: "center",
    padding: 32,
  },
  emptyText: {
    color: "#9ca3af",
    marginTop: 16,
  },
});
