/**
 * Trading Screen for Mobile App
 * Allows users to place trades and execute DEX swaps on mobile
 */

import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Switch,
} from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { Picker } from "@react-native-picker/picker";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import BiometricAuth from "../services/BiometricAuth";

import OfflineIndicator from "../components/OfflineIndicator";

interface TradingScreenProps {
  mode?: "paper" | "real" | "live";
}

interface DexQuote {
  token_in: string;
  token_out: string;
  amount_in: number;
  amount_out: number;
  price_impact: number;
  fee: number;
  aggregator: string;
  route?: string[];
}

export default function TradingScreen({ mode = "paper" }: TradingScreenProps) {
  const [tradingType, setTradingType] = useState<"exchange" | "dex">("exchange");
  const [pair, setPair] = useState("BTC/USD");
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [orderType, setOrderType] = useState<"market" | "limit">("market");
  const [amount, setAmount] = useState("");
  const [price, setPrice] = useState("");

  // DEX Trading State
  const [chainId, setChainId] = useState(1); // Ethereum
  const [tokenIn, setTokenIn] = useState("USDC");
  const [tokenOut, setTokenOut] = useState("ETH");
  const [dexAmount, setDexAmount] = useState("");
  const [slippage, setSlippage] = useState("0.5");
  const [requireBiometric, setRequireBiometric] = useState(true);

  // Fetch DEX quote
  const { data: dexQuote, isLoading: quoteLoading } = useQuery({
    queryKey: ["dexQuote", tokenIn, tokenOut, dexAmount, chainId],
    queryFn: async () => {
      if (!dexAmount || parseFloat(dexAmount) <= 0) return null;
      const response = await api.getDexQuote({
        token_in: tokenIn,
        token_out: tokenOut,
        amount: parseFloat(dexAmount),
        chain_id: chainId,
      });
      return response.data as DexQuote;
    },
    enabled: tradingType === "dex" && !!dexAmount && parseFloat(dexAmount) > 0,
    refetchInterval: 10000, // Refresh quote every 10 seconds
  });

  // Execute trade mutation
  const executeTradeMutation = useMutation({
    mutationFn: (data: {
      pair: string;
      side: "buy" | "sell";
      type: "market" | "limit";
      amount: number;
      price?: number;
      mode?: "paper" | "real";
    }) => api.createTrade(data),
    onSuccess: () => {
      Alert.alert("Success", "Trade executed successfully");
      setAmount("");
      setPrice("");
    },
    onError: (err: unknown) => {
      const errorData = (err as { response?: { data?: { detail?: string } } }).response?.data;
      Alert.alert("Trade Failed", errorData?.detail ?? (err as Error).message);
    },
  });

  // Execute DEX swap mutation
  const executeDexSwapMutation = useMutation({
    mutationFn: (data: {
      token_in: string;
      token_out: string;
      amount: number;
      chain_id: number;
      slippage?: number;
      aggregator?: string;
    }) => api.executeDexSwap(data),
    onSuccess: () => {
      Alert.alert("Success", "Swap executed successfully");
      setDexAmount("");
    },
    onError: (err: unknown) => {
      const errorData = (err as { response?: { data?: { detail?: string } } }).response?.data;
      Alert.alert("Swap Failed", errorData?.detail ?? (err as Error).message);
    },
  });

  const handleTrade = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      Alert.alert("Error", "Please enter a valid amount");
      return;
    }

    if (orderType === "limit" && (!price || parseFloat(price) <= 0)) {
      Alert.alert("Error", "Please enter a valid price for limit orders");
      return;
    }

    // Biometric confirmation for real money trades
    if (mode === "real" && requireBiometric) {
      try {
        const result = await BiometricAuth.authenticate("Confirm Real Money Trade");
        if (!result.success) {
          Alert.alert("Authentication Failed", result.error ?? "Biometric authentication required");
          return;
        }
      } catch (error) {
        Alert.alert("Error", "Biometric authentication failed");
        return;
      }
    }

    // Confirmation for real money trades
    if (mode === "real" || mode === "live") {
      Alert.alert(
        "Confirm Real Money Trade",
        `Are you sure you want to ${side} ${amount} ${pair}?`,
        [
          { text: "Cancel", style: "cancel" },
          {
            text: "Confirm",
            style: "destructive",
            onPress: () => {
              const normalizedMode = mode === "live" ? "real" : mode;
              executeTradeMutation.mutate({
                pair,
                side,
                type: orderType,
                amount: parseFloat(amount),
                price: orderType === "limit" ? parseFloat(price) : undefined,
                mode: normalizedMode,
              });
            },
          },
        ]
      );
    } else {
      executeTradeMutation.mutate({
        pair,
        side,
        type: orderType,
        amount: parseFloat(amount),
        price: orderType === "limit" ? parseFloat(price) : undefined,
        mode: mode,
      });
    }
  };

  const handleDexSwap = async () => {
    if (!dexAmount || parseFloat(dexAmount) <= 0) {
      Alert.alert("Error", "Please enter a valid amount");
      return;
    }

    if (!dexQuote) {
      Alert.alert("Error", "Please wait for quote to load");
      return;
    }

    // Price impact warning
    if (dexQuote.price_impact > 0.01) {
      Alert.alert(
        "High Price Impact Warning",
        `Price impact is ${(dexQuote.price_impact * 100).toFixed(2)}%. This may result in unfavorable execution. Continue?`,
        [
          { text: "Cancel", style: "cancel" },
          {
            text: "Continue",
            onPress: () => executeSwap(),
          },
        ]
      );
      return;
    }

    executeSwap();
  };

  const executeSwap = async () => {
    // Biometric confirmation for real money swaps
    if (mode === "real" && requireBiometric) {
      try {
        const result = await BiometricAuth.authenticate("Confirm DEX Swap");
        if (!result.success) {
          Alert.alert("Authentication Failed", result.error ?? "Biometric authentication required");
          return;
        }
      } catch (error) {
        Alert.alert("Error", "Biometric authentication failed");
        return;
      }
    }

    executeDexSwapMutation.mutate({
      token_in: tokenIn,
      token_out: tokenOut,
      amount: parseFloat(dexAmount),
      chain_id: chainId,
      slippage: parseFloat(slippage),
      aggregator: dexQuote?.aggregator,
    });
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Offline Indicator */}
        <OfflineIndicator />

        {/* Mode Indicator */}
        <View style={styles.modeIndicator}>
          <MaterialCommunityIcons
            name={mode === "real" ? "shield-alert" : "shield-check"}
            size={20}
            color={mode === "real" ? "#ef4444" : "#22c55e"}
          />
          <Text style={[styles.modeText, mode === "real" && styles.modeTextReal]}>
            {mode === "real" ? "Real Money Trading" : "Paper Trading"}
          </Text>
        </View>

        {/* Trading Type Toggle */}
        <View style={styles.section}>
          <Text style={styles.label}>Trading Type</Text>
          <View style={styles.toggleContainer}>
            <TouchableOpacity
              style={[styles.toggleButton, tradingType === "exchange" && styles.toggleButtonActive]}
              onPress={() => setTradingType("exchange")}
            >
              <Text
                style={[
                  styles.toggleButtonText,
                  tradingType === "exchange" && styles.toggleButtonTextActive,
                ]}
              >
                Exchange
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toggleButton, tradingType === "dex" && styles.toggleButtonActive]}
              onPress={() => setTradingType("dex")}
            >
              <Text
                style={[
                  styles.toggleButtonText,
                  tradingType === "dex" && styles.toggleButtonTextActive,
                ]}
              >
                DEX Swap
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {tradingType === "exchange" ? (
          <>
            {/* Exchange Trading Form */}
            <View style={styles.section}>
              <Text style={styles.label}>Trading Pair</Text>
              <View style={styles.pickerContainer}>
                <Picker selectedValue={pair} onValueChange={setPair} style={styles.picker}>
                  <Picker.Item label="BTC/USD" value="BTC/USD" />
                  <Picker.Item label="ETH/USD" value="ETH/USD" />
                  <Picker.Item label="BTC/USDT" value="BTC/USDT" />
                  <Picker.Item label="ETH/USDT" value="ETH/USDT" />
                </Picker>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.label}>Side</Text>
              <View style={styles.sideContainer}>
                <TouchableOpacity
                  style={[
                    styles.sideButton,
                    side === "buy" && styles.sideButtonActive,
                    side === "buy" && styles.sideButtonBuy,
                  ]}
                  onPress={() => setSide("buy")}
                >
                  <MaterialCommunityIcons
                    name="arrow-down"
                    size={20}
                    color={side === "buy" ? "#fff" : "#9ca3af"}
                  />
                  <Text
                    style={[styles.sideButtonText, side === "buy" && styles.sideButtonTextActive]}
                  >
                    Buy
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.sideButton,
                    side === "sell" && styles.sideButtonActive,
                    side === "sell" && styles.sideButtonSell,
                  ]}
                  onPress={() => setSide("sell")}
                >
                  <MaterialCommunityIcons
                    name="arrow-up"
                    size={20}
                    color={side === "sell" ? "#fff" : "#9ca3af"}
                  />
                  <Text
                    style={[styles.sideButtonText, side === "sell" && styles.sideButtonTextActive]}
                  >
                    Sell
                  </Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.label}>Order Type</Text>
              <View style={styles.sideContainer}>
                <TouchableOpacity
                  style={[styles.sideButton, orderType === "market" && styles.sideButtonActive]}
                  onPress={() => setOrderType("market")}
                >
                  <Text
                    style={[
                      styles.sideButtonText,
                      orderType === "market" && styles.sideButtonTextActive,
                    ]}
                  >
                    Market
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.sideButton, orderType === "limit" && styles.sideButtonActive]}
                  onPress={() => setOrderType("limit")}
                >
                  <Text
                    style={[
                      styles.sideButtonText,
                      orderType === "limit" && styles.sideButtonTextActive,
                    ]}
                  >
                    Limit
                  </Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.label}>Amount</Text>
              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="0.00"
                  placeholderTextColor="#9ca3af"
                  value={amount}
                  onChangeText={setAmount}
                  keyboardType="decimal-pad"
                />
              </View>
            </View>

            {orderType === "limit" && (
              <View style={styles.section}>
                <Text style={styles.label}>Price</Text>
                <View style={styles.inputContainer}>
                  <TextInput
                    style={styles.input}
                    placeholder="0.00"
                    placeholderTextColor="#9ca3af"
                    value={price}
                    onChangeText={setPrice}
                    keyboardType="decimal-pad"
                  />
                </View>
              </View>
            )}

            <TouchableOpacity
              style={[
                styles.executeButton,
                side === "buy" ? styles.executeButtonBuy : styles.executeButtonSell,
                executeTradeMutation.isPending && styles.executeButtonDisabled,
              ]}
              onPress={handleTrade}
              disabled={executeTradeMutation.isPending}
            >
              {executeTradeMutation.isPending ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <MaterialCommunityIcons
                    name={side === "buy" ? "arrow-down" : "arrow-up"}
                    size={20}
                    color="#fff"
                  />
                  <Text style={styles.executeButtonText}>
                    {side === "buy" ? "Buy" : "Sell"} {pair}
                  </Text>
                </>
              )}
            </TouchableOpacity>
          </>
        ) : (
          <>
            {/* DEX Trading Form */}
            <View style={styles.section}>
              <Text style={styles.label}>Blockchain Network</Text>
              <View style={styles.pickerContainer}>
                <Picker selectedValue={chainId} onValueChange={setChainId} style={styles.picker}>
                  <Picker.Item label="Ethereum" value={1} />
                  <Picker.Item label="Base" value={8453} />
                  <Picker.Item label="Arbitrum" value={42161} />
                  <Picker.Item label="Polygon" value={137} />
                </Picker>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.label}>Token In</Text>
              <View style={styles.pickerContainer}>
                <Picker selectedValue={tokenIn} onValueChange={setTokenIn} style={styles.picker}>
                  <Picker.Item label="USDC" value="USDC" />
                  <Picker.Item label="USDT" value="USDT" />
                  <Picker.Item label="ETH" value="ETH" />
                  <Picker.Item label="BTC" value="BTC" />
                </Picker>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.label}>Token Out</Text>
              <View style={styles.pickerContainer}>
                <Picker selectedValue={tokenOut} onValueChange={setTokenOut} style={styles.picker}>
                  <Picker.Item label="ETH" value="ETH" />
                  <Picker.Item label="USDC" value="USDC" />
                  <Picker.Item label="USDT" value="USDT" />
                  <Picker.Item label="BTC" value="BTC" />
                </Picker>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={styles.label}>Amount</Text>
              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="0.00"
                  placeholderTextColor="#9ca3af"
                  value={dexAmount}
                  onChangeText={setDexAmount}
                  keyboardType="decimal-pad"
                />
              </View>
            </View>

            {/* DEX Quote Display */}
            {quoteLoading && (
              <View style={styles.quoteContainer}>
                <ActivityIndicator size="small" color="#3b82f6" />
                <Text style={styles.quoteText}>Loading quote...</Text>
              </View>
            )}

            {!quoteLoading && dexQuote && (
              <View style={styles.quoteCard}>
                <Text style={styles.quoteTitle}>Swap Quote</Text>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>You Pay</Text>
                  <Text style={styles.quoteValue}>
                    {dexQuote.amount_in.toFixed(4)} {tokenIn}
                  </Text>
                </View>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>You Receive</Text>
                  <Text style={styles.quoteValue}>
                    {dexQuote.amount_out.toFixed(4)} {tokenOut}
                  </Text>
                </View>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>Price Impact</Text>
                  <Text
                    style={[
                      styles.quoteValue,
                      dexQuote.price_impact > 0.01 ? styles.warning : styles.success,
                    ]}
                  >
                    {(dexQuote.price_impact * 100).toFixed(2)}%
                  </Text>
                </View>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>Fee</Text>
                  <Text style={styles.quoteValue}>${dexQuote.fee.toFixed(2)}</Text>
                </View>
                <View style={styles.quoteRow}>
                  <Text style={styles.quoteLabel}>Aggregator</Text>
                  <Text style={styles.quoteValue}>{dexQuote.aggregator}</Text>
                </View>
              </View>
            )}

            <View style={styles.section}>
              <Text style={styles.label}>Slippage Tolerance (%)</Text>
              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="0.5"
                  placeholderTextColor="#9ca3af"
                  value={slippage}
                  onChangeText={setSlippage}
                  keyboardType="decimal-pad"
                />
              </View>
            </View>

            {mode === "real" && (
              <View style={styles.section}>
                <View style={styles.switchRow}>
                  <View style={styles.switchInfo}>
                    <MaterialCommunityIcons name="fingerprint" size={20} color="#3b82f6" />
                    <Text style={styles.switchLabel}>Require Biometric Confirmation</Text>
                  </View>
                  <Switch
                    value={requireBiometric}
                    onValueChange={setRequireBiometric}
                    trackColor={{ false: "#374151", true: "#3b82f6" }}
                    thumbColor="#fff"
                  />
                </View>
              </View>
            )}

            <TouchableOpacity
              style={[
                styles.executeButton,
                styles.executeButtonDex,
                (executeDexSwapMutation.isPending || !dexQuote) && styles.executeButtonDisabled,
              ]}
              onPress={handleDexSwap}
              disabled={executeDexSwapMutation.isPending || !dexQuote}
            >
              {executeDexSwapMutation.isPending ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <MaterialCommunityIcons name="swap-horizontal" size={20} color="#fff" />
                  <Text style={styles.executeButtonText}>Execute Swap</Text>
                </>
              )}
            </TouchableOpacity>
          </>
        )}

        {/* Warning for real money */}
        {mode === "real" && (
          <View style={styles.warningContainer}>
            <MaterialCommunityIcons name="alert" size={20} color="#ef4444" />
            <Text style={styles.warningText}>
              You are trading with real money. Please verify all details before confirming.
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
  },
  content: {
    padding: 16,
  },
  modeIndicator: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 12,
    backgroundColor: "#1e293b",
    borderRadius: 8,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: "#334155",
  },
  modeText: {
    color: "#22c55e",
    fontSize: 14,
    fontWeight: "600",
    marginLeft: 8,
  },
  modeTextReal: {
    color: "#ef4444",
  },
  section: {
    marginBottom: 24,
  },
  label: {
    color: "#9ca3af",
    fontSize: 14,
    marginBottom: 8,
  },
  toggleContainer: {
    flexDirection: "row",
    gap: 12,
    backgroundColor: "#1e293b",
    borderRadius: 8,
    padding: 4,
    borderWidth: 1,
    borderColor: "#334155",
  },
  toggleButton: {
    flex: 1,
    padding: 12,
    borderRadius: 6,
    alignItems: "center",
    justifyContent: "center",
  },
  toggleButtonActive: {
    backgroundColor: "#3b82f6",
  },
  toggleButtonText: {
    color: "#9ca3af",
    fontSize: 14,
    fontWeight: "600",
  },
  toggleButtonTextActive: {
    color: "#fff",
  },
  pickerContainer: {
    backgroundColor: "#1e293b",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  picker: {
    color: "#fff",
  },
  sideContainer: {
    flexDirection: "row",
    gap: 12,
  },
  sideButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    backgroundColor: "#1e293b",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#334155",
    gap: 8,
    minHeight: 44,
  },
  sideButtonActive: {
    borderWidth: 2,
  },
  sideButtonBuy: {
    borderColor: "#22c55e",
    backgroundColor: "#22c55e",
  },
  sideButtonSell: {
    borderColor: "#ef4444",
    backgroundColor: "#ef4444",
  },
  sideButtonText: {
    color: "#9ca3af",
    fontSize: 16,
    fontWeight: "600",
  },
  sideButtonTextActive: {
    color: "#fff",
  },
  inputContainer: {
    backgroundColor: "#1e293b",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  input: {
    color: "#fff",
    fontSize: 18,
    padding: 16,
    minHeight: 44,
  },
  executeButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    borderRadius: 8,
    marginTop: 8,
    gap: 8,
    minHeight: 44,
  },
  executeButtonBuy: {
    backgroundColor: "#22c55e",
  },
  executeButtonSell: {
    backgroundColor: "#ef4444",
  },
  executeButtonDex: {
    backgroundColor: "#3b82f6",
  },
  executeButtonDisabled: {
    opacity: 0.6,
  },
  executeButtonText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "600",
  },
  warningContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 24,
    padding: 12,
    backgroundColor: "#ef4444",
    opacity: 0.1,
    borderRadius: 8,
    gap: 8,
  },
  warningText: {
    flex: 1,
    color: "#ef4444",
    fontSize: 12,
  },
  quoteContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    backgroundColor: "#1e293b",
    borderRadius: 8,
    marginBottom: 16,
    gap: 8,
  },
  quoteText: {
    color: "#9ca3af",
    fontSize: 14,
  },
  quoteCard: {
    backgroundColor: "#1e293b",
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#334155",
  },
  quoteTitle: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 12,
  },
  quoteRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  quoteLabel: {
    color: "#9ca3af",
    fontSize: 14,
  },
  quoteValue: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "500",
  },
  warning: {
    color: "#ef4444",
  },
  success: {
    color: "#22c55e",
  },
  switchRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 12,
    backgroundColor: "#1e293b",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  switchInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    flex: 1,
  },
  switchLabel: {
    color: "#fff",
    fontSize: 14,
  },
});
