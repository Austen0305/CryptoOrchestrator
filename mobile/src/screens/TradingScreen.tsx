/**
 * Trading Screen for Mobile App
 * Allows users to place trades on mobile
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Picker } from '@react-native-picker/picker';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

interface TradingScreenProps {
  mode?: 'paper' | 'real';
}

export default function TradingScreen({ mode = 'paper' }: TradingScreenProps) {
  const [pair, setPair] = useState('BTC/USD');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTrade = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    if (orderType === 'limit' && (!price || parseFloat(price) <= 0)) {
      Alert.alert('Error', 'Please enter a valid price for limit orders');
      return;
    }

    // Confirmation for real money trades
    if (mode === 'real') {
      Alert.alert(
        'Confirm Real Money Trade',
        `Are you sure you want to ${side} ${amount} ${pair}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Confirm',
            style: 'destructive',
            onPress: executeTrade,
          },
        ]
      );
    } else {
      executeTrade();
    }
  };

  const executeTrade = async () => {
    setLoading(true);
    try {
      const token = await require('@react-native-async-storage/async-storage').default.getItem('auth_token');
      
      const response = await fetch(`${API_BASE_URL}/api/trades`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          pair,
          side,
          type: orderType,
          amount: parseFloat(amount),
          price: orderType === 'limit' ? parseFloat(price) : null,
          mode: mode,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Trade execution failed');
      }

      const data = await response.json();
      Alert.alert('Success', `Trade ${data.status === 'completed' ? 'executed' : 'placed'} successfully`);
      
      // Reset form
      setAmount('');
      setPrice('');
    } catch (error: any) {
      Alert.alert('Trade Failed', error.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Mode Indicator */}
        <View style={styles.modeIndicator}>
          <MaterialCommunityIcons
            name={mode === 'real' ? 'shield-alert' : 'shield-check'}
            size={20}
            color={mode === 'real' ? '#ef4444' : '#22c55e'}
          />
          <Text style={[styles.modeText, mode === 'real' && styles.modeTextReal]}>
            {mode === 'real' ? 'Real Money Trading' : 'Paper Trading'}
          </Text>
        </View>

        {/* Trading Pair */}
        <View style={styles.section}>
          <Text style={styles.label}>Trading Pair</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={pair}
              onValueChange={setPair}
              style={styles.picker}
            >
              <Picker.Item label="BTC/USD" value="BTC/USD" />
              <Picker.Item label="ETH/USD" value="ETH/USD" />
              <Picker.Item label="BTC/USDT" value="BTC/USDT" />
              <Picker.Item label="ETH/USDT" value="ETH/USDT" />
            </Picker>
          </View>
        </View>

        {/* Side Selection */}
        <View style={styles.section}>
          <Text style={styles.label}>Side</Text>
          <View style={styles.sideContainer}>
            <TouchableOpacity
              style={[
                styles.sideButton,
                side === 'buy' && styles.sideButtonActive,
                side === 'buy' && styles.sideButtonBuy,
              ]}
              onPress={() => setSide('buy')}
            >
              <MaterialCommunityIcons name="arrow-down" size={20} color={side === 'buy' ? '#fff' : '#9ca3af'} />
              <Text style={[styles.sideButtonText, side === 'buy' && styles.sideButtonTextActive]}>
                Buy
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.sideButton,
                side === 'sell' && styles.sideButtonActive,
                side === 'sell' && styles.sideButtonSell,
              ]}
              onPress={() => setSide('sell')}
            >
              <MaterialCommunityIcons name="arrow-up" size={20} color={side === 'sell' ? '#fff' : '#9ca3af'} />
              <Text style={[styles.sideButtonText, side === 'sell' && styles.sideButtonTextActive]}>
                Sell
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Order Type */}
        <View style={styles.section}>
          <Text style={styles.label}>Order Type</Text>
          <View style={styles.sideContainer}>
            <TouchableOpacity
              style={[
                styles.sideButton,
                orderType === 'market' && styles.sideButtonActive,
              ]}
              onPress={() => setOrderType('market')}
            >
              <Text style={[styles.sideButtonText, orderType === 'market' && styles.sideButtonTextActive]}>
                Market
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.sideButton,
                orderType === 'limit' && styles.sideButtonActive,
              ]}
              onPress={() => setOrderType('limit')}
            >
              <Text style={[styles.sideButtonText, orderType === 'limit' && styles.sideButtonTextActive]}>
                Limit
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Amount */}
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

        {/* Price (for limit orders) */}
        {orderType === 'limit' && (
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

        {/* Execute Button */}
        <TouchableOpacity
          style={[
            styles.executeButton,
            side === 'buy' ? styles.executeButtonBuy : styles.executeButtonSell,
            loading && styles.executeButtonDisabled,
          ]}
          onPress={handleTrade}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <MaterialCommunityIcons
                name={side === 'buy' ? 'arrow-down' : 'arrow-up'}
                size={20}
                color="#fff"
              />
              <Text style={styles.executeButtonText}>
                {side === 'buy' ? 'Buy' : 'Sell'} {pair}
              </Text>
            </>
          )}
        </TouchableOpacity>

        {/* Warning for real money */}
        {mode === 'real' && (
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
    backgroundColor: '#0f172a',
  },
  content: {
    padding: 16,
  },
  modeIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    backgroundColor: '#1e293b',
    borderRadius: 8,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#334155',
  },
  modeText: {
    color: '#22c55e',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  modeTextReal: {
    color: '#ef4444',
  },
  section: {
    marginBottom: 24,
  },
  label: {
    color: '#9ca3af',
    fontSize: 14,
    marginBottom: 8,
  },
  pickerContainer: {
    backgroundColor: '#1e293b',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  picker: {
    color: '#fff',
  },
  sideContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  sideButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    backgroundColor: '#1e293b',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 8,
  },
  sideButtonActive: {
    borderWidth: 2,
  },
  sideButtonBuy: {
    borderColor: '#22c55e',
    backgroundColor: '#22c55e',
  },
  sideButtonSell: {
    borderColor: '#ef4444',
    backgroundColor: '#ef4444',
  },
  sideButtonText: {
    color: '#9ca3af',
    fontSize: 16,
    fontWeight: '600',
  },
  sideButtonTextActive: {
    color: '#fff',
  },
  inputContainer: {
    backgroundColor: '#1e293b',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  input: {
    color: '#fff',
    fontSize: 18,
    padding: 16,
  },
  executeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 8,
    marginTop: 8,
    gap: 8,
  },
  executeButtonBuy: {
    backgroundColor: '#22c55e',
  },
  executeButtonSell: {
    backgroundColor: '#ef4444',
  },
  executeButtonDisabled: {
    opacity: 0.6,
  },
  executeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  warningContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 24,
    padding: 12,
    backgroundColor: '#ef4444',
    opacity: 0.1,
    borderRadius: 8,
    gap: 8,
  },
  warningText: {
    flex: 1,
    color: '#ef4444',
    fontSize: 12,
  },
});

