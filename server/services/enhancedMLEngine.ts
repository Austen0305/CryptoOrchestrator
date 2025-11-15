import * as tf from '@tensorflow/tfjs';
import type { MarketData } from '@shared/schema';
import logger from './logger';
import { storage } from '../storage';

interface TechnicalIndicators {
  rsi: number;
  macd: { value: number; signal: number; histogram: number };
  bollingerBands: { upper: number; middle: number; lower: number };
  ema: { fast: number; slow: number };
  atr: number;
  volumeOscillator: number;
  stochastic: { k: number; d: number };
  adx: number;
  obv: number;
}

interface MLPrediction {
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  strength: number;
  indicators: TechnicalIndicators;
  reasoning: string[];
}

export class EnhancedMLEngine {
  private model: tf.LayersModel | null = null;
  private isTraining: boolean = false;
  private predictionHistory: { predicted: string; actual: string; timestamp: number }[] = [];
  private readonly MAX_HISTORY = 1000;
  private readonly LOOKBACK_PERIOD = 50;
  private readonly FEATURE_COUNT = 25;

  constructor() {
    this.initializeModel();
  }

  private initializeModel(): void {
    try {
      this.model = tf.sequential({
        layers: [
          // Input layer
          tf.layers.dense({
            inputShape: [this.LOOKBACK_PERIOD * this.FEATURE_COUNT],
            units: 128,
            activation: 'relu',
            kernelInitializer: 'heNormal',
          }),
          tf.layers.dropout({ rate: 0.3 }),
          
          // Hidden layers with batch normalization
          tf.layers.dense({
            units: 256,
            activation: 'relu',
            kernelInitializer: 'heNormal',
          }),
          tf.layers.batchNormalization(),
          tf.layers.dropout({ rate: 0.3 }),
          
          tf.layers.dense({
            units: 128,
            activation: 'relu',
            kernelInitializer: 'heNormal',
          }),
          tf.layers.batchNormalization(),
          tf.layers.dropout({ rate: 0.2 }),
          
          tf.layers.dense({
            units: 64,
            activation: 'relu',
            kernelInitializer: 'heNormal',
          }),
          tf.layers.dropout({ rate: 0.2 }),
          
          // Output layer - 3 classes (buy, sell, hold)
          tf.layers.dense({
            units: 3,
            activation: 'softmax',
          }),
        ],
      });

      this.model.compile({
        optimizer: tf.train.adam(0.001),
        loss: 'categoricalCrossentropy',
        metrics: ['accuracy'],
      });

      logger.info('Enhanced ML model initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize ML model', { error });
      throw error;
    }
  }

  private calculateTechnicalIndicators(data: MarketData[], index: number): TechnicalIndicators {
    const rsi = this.calculateRSI(data, index);
    const macd = this.calculateMACD(data, index);
    const bollingerBands = this.calculateBollingerBands(data, index);
    const ema = this.calculateEMA(data, index);
    const atr = this.calculateATR(data, index);
    const volumeOscillator = this.calculateVolumeOscillator(data, index);
    const stochastic = this.calculateStochastic(data, index);
    const adx = this.calculateADX(data, index);
    const obv = this.calculateOBV(data, index);

    return {
      rsi,
      macd,
      bollingerBands,
      ema,
      atr,
      volumeOscillator,
      stochastic,
      adx,
      obv,
    };
  }

  private calculateRSI(data: MarketData[], index: number, period: number = 14): number {
    if (index < period) return 50;

    let gains = 0;
    let losses = 0;

    for (let i = index - period + 1; i <= index; i++) {
      const change = data[i].close - data[i - 1].close;
      if (change > 0) gains += change;
      else losses += Math.abs(change);
    }

    const avgGain = gains / period;
    const avgLoss = losses / period;
    if (avgLoss === 0) return 100;

    const rs = avgGain / avgLoss;
    return 100 - 100 / (1 + rs);
  }

  private calculateMACD(
    data: MarketData[],
    index: number,
    fastPeriod: number = 12,
    slowPeriod: number = 26,
    signalPeriod: number = 9
  ): { value: number; signal: number; histogram: number } {
    if (index < slowPeriod) {
      return { value: 0, signal: 0, histogram: 0 };
    }

    const fastEMA = this.calculateEMAValue(data, index, fastPeriod);
    const slowEMA = this.calculateEMAValue(data, index, slowPeriod);
    const macdValue = fastEMA - slowEMA;

    // Calculate signal line (EMA of MACD)
    const signal = macdValue * 0.2; // Simplified signal calculation
    const histogram = macdValue - signal;

    return { value: macdValue, signal, histogram };
  }

  private calculateEMAValue(data: MarketData[], index: number, period: number): number {
    if (index < period) return data[index].close;

    const multiplier = 2 / (period + 1);
    let ema = data[index - period].close;

    for (let i = index - period + 1; i <= index; i++) {
      ema = (data[i].close - ema) * multiplier + ema;
    }

    return ema;
  }

  private calculateBollingerBands(
    data: MarketData[],
    index: number,
    period: number = 20,
    stdDev: number = 2
  ): { upper: number; middle: number; lower: number } {
    if (index < period) {
      const current = data[index].close;
      return { upper: current, middle: current, lower: current };
    }

    const prices = data.slice(index - period + 1, index + 1).map(d => d.close);
    const middle = prices.reduce((sum, p) => sum + p, 0) / period;
    
    const variance = prices.reduce((sum, p) => sum + Math.pow(p - middle, 2), 0) / period;
    const std = Math.sqrt(variance);

    return {
      upper: middle + stdDev * std,
      middle,
      lower: middle - stdDev * std,
    };
  }

  private calculateEMA(data: MarketData[], index: number): { fast: number; slow: number } {
    return {
      fast: this.calculateEMAValue(data, index, 12),
      slow: this.calculateEMAValue(data, index, 26),
    };
  }

  private calculateATR(data: MarketData[], index: number, period: number = 14): number {
    if (index < period) return 0;

    let sum = 0;
    for (let i = index - period + 1; i <= index; i++) {
      const high = data[i].high;
      const low = data[i].low;
      const prevClose = i > 0 ? data[i - 1].close : data[i].close;
      
      const tr = Math.max(
        high - low,
        Math.abs(high - prevClose),
        Math.abs(low - prevClose)
      );
      sum += tr;
    }

    return sum / period;
  }

  private calculateVolumeOscillator(data: MarketData[], index: number): number {
    if (index < 26) return 0;

    const shortVolEMA = this.calculateVolumeEMA(data, index, 5);
    const longVolEMA = this.calculateVolumeEMA(data, index, 10);

    return ((shortVolEMA - longVolEMA) / longVolEMA) * 100;
  }

  private calculateVolumeEMA(data: MarketData[], index: number, period: number): number {
    if (index < period) return data[index].volume;

    const multiplier = 2 / (period + 1);
    let ema = data[index - period].volume;

    for (let i = index - period + 1; i <= index; i++) {
      ema = (data[i].volume - ema) * multiplier + ema;
    }

    return ema;
  }

  private calculateStochastic(
    data: MarketData[],
    index: number,
    period: number = 14
  ): { k: number; d: number } {
    if (index < period) return { k: 50, d: 50 };

    const recentData = data.slice(index - period + 1, index + 1);
    const high = Math.max(...recentData.map(d => d.high));
    const low = Math.min(...recentData.map(d => d.low));
    const close = data[index].close;

    const k = ((close - low) / (high - low)) * 100;
    const d = k; // Simplified D calculation

    return { k, d };
  }

  private calculateADX(data: MarketData[], index: number, period: number = 14): number {
    if (index < period + 1) return 25; // Neutral value

    let plusDM = 0;
    let minusDM = 0;
    let tr = 0;

    for (let i = index - period + 1; i <= index; i++) {
      const highDiff = data[i].high - data[i - 1].high;
      const lowDiff = data[i - 1].low - data[i].low;

      plusDM += highDiff > lowDiff && highDiff > 0 ? highDiff : 0;
      minusDM += lowDiff > highDiff && lowDiff > 0 ? lowDiff : 0;

      const trueRange = Math.max(
        data[i].high - data[i].low,
        Math.abs(data[i].high - data[i - 1].close),
        Math.abs(data[i].low - data[i - 1].close)
      );
      tr += trueRange;
    }

    const plusDI = (plusDM / tr) * 100;
    const minusDI = (minusDM / tr) * 100;
    const dx = Math.abs(plusDI - minusDI) / (plusDI + minusDI) * 100;

    return dx;
  }

  private calculateOBV(data: MarketData[], index: number): number {
    if (index === 0) return data[0].volume;

    let obv = 0;
    for (let i = 1; i <= index; i++) {
      if (data[i].close > data[i - 1].close) {
        obv += data[i].volume;
      } else if (data[i].close < data[i - 1].close) {
        obv -= data[i].volume;
      }
    }

    return obv;
  }

  private extractFeatures(data: MarketData[], index: number): number[] {
    const features: number[] = [];
    const indicators = this.calculateTechnicalIndicators(data, index);

    // Price-based features (normalized)
    const currentPrice = data[index].close;
    const priceChange = index > 0 ? (currentPrice - data[index - 1].close) / data[index - 1].close : 0;
    features.push(priceChange);

    // Volume features
    const avgVolume = data.slice(Math.max(0, index - 20), index + 1)
      .reduce((sum, d) => sum + d.volume, 0) / Math.min(20, index + 1);
    const volumeRatio = data[index].volume / avgVolume;
    features.push(Math.min(volumeRatio, 5)); // Cap at 5x

    // Technical indicators
    features.push(indicators.rsi / 100);
    features.push(Math.tanh(indicators.macd.value / currentPrice));
    features.push(Math.tanh(indicators.macd.histogram / currentPrice));
    features.push((currentPrice - indicators.bollingerBands.lower) / 
                  (indicators.bollingerBands.upper - indicators.bollingerBands.lower));
    features.push(Math.tanh((indicators.ema.fast - indicators.ema.slow) / currentPrice));
    features.push(Math.min(indicators.atr / currentPrice, 0.1) * 10);
    features.push(Math.tanh(indicators.volumeOscillator / 100));
    features.push(indicators.stochastic.k / 100);
    features.push(indicators.stochastic.d / 100);
    features.push(indicators.adx / 100);
    features.push(Math.tanh(indicators.obv / 1000000));

    // Price momentum features
    const momentum5 = index >= 5 ? (currentPrice - data[index - 5].close) / data[index - 5].close : 0;
    const momentum10 = index >= 10 ? (currentPrice - data[index - 10].close) / data[index - 10].close : 0;
    const momentum20 = index >= 20 ? (currentPrice - data[index - 20].close) / data[index - 20].close : 0;
    features.push(Math.tanh(momentum5 * 10));
    features.push(Math.tanh(momentum10 * 5));
    features.push(Math.tanh(momentum20 * 2));

    // Volatility features
    const returns = data.slice(Math.max(0, index - 20), index + 1)
      .map((d, i, arr) => i > 0 ? (d.close - arr[i - 1].close) / arr[i - 1].close : 0);
    const volatility = Math.sqrt(returns.reduce((sum, r) => sum + r * r, 0) / returns.length);
    features.push(Math.min(volatility * 100, 1));

    // Price position relative to recent high/low
    const recentHigh = Math.max(...data.slice(Math.max(0, index - 20), index + 1).map(d => d.high));
    const recentLow = Math.min(...data.slice(Math.max(0, index - 20), index + 1).map(d => d.low));
    const pricePosition = (currentPrice - recentLow) / (recentHigh - recentLow);
    features.push(pricePosition);

    // Time-based features
    const hourOfDay = new Date(data[index].timestamp).getHours() / 24;
    const dayOfWeek = new Date(data[index].timestamp).getDay() / 7;
    features.push(hourOfDay);
    features.push(dayOfWeek);

    // Trend strength
    const sma20 = data.slice(Math.max(0, index - 19), index + 1)
      .reduce((sum, d) => sum + d.close, 0) / Math.min(20, index + 1);
    const trendStrength = (currentPrice - sma20) / sma20;
    features.push(Math.tanh(trendStrength * 10));

    // Support/Resistance levels
    const supportLevel = Math.min(...data.slice(Math.max(0, index - 50), index + 1).map(d => d.low));
    const resistanceLevel = Math.max(...data.slice(Math.max(0, index - 50), index + 1).map(d => d.high));
    const distanceToSupport = (currentPrice - supportLevel) / currentPrice;
    const distanceToResistance = (resistanceLevel - currentPrice) / currentPrice;
    features.push(Math.min(distanceToSupport * 10, 1));
    features.push(Math.min(distanceToResistance * 10, 1));

    return features;
  }

  private prepareTrainingData(data: MarketData[]): { inputs: number[][]; labels: number[][] } {
    const inputs: number[][] = [];
    const labels: number[][] = [];

    for (let i = this.LOOKBACK_PERIOD; i < data.length - 1; i++) {
      const features: number[] = [];
      
      // Collect features for lookback period
      for (let j = 0; j < this.LOOKBACK_PERIOD; j++) {
        const periodFeatures = this.extractFeatures(data, i - this.LOOKBACK_PERIOD + j);
        features.push(...periodFeatures);
      }

      inputs.push(features);

      // Label based on future price movement
      const futurePrice = data[i + 1].close;
      const currentPrice = data[i].close;
      const priceChange = (futurePrice - currentPrice) / currentPrice;

      // Classify: buy (0), hold (1), sell (2)
      if (priceChange > 0.005) {
        labels.push([1, 0, 0]); // Buy
      } else if (priceChange < -0.005) {
        labels.push([0, 0, 1]); // Sell
      } else {
        labels.push([0, 1, 0]); // Hold
      }
    }

    return { inputs, labels };
  }

  async train(data: MarketData[], epochs: number = 50): Promise<void> {
    if (this.isTraining) {
      logger.warn('Training already in progress');
      return;
    }

    try {
      this.isTraining = true;
      logger.info('Starting ML model training', { dataPoints: data.length, epochs });

      const { inputs, labels } = this.prepareTrainingData(data);
      
      if (inputs.length === 0) {
        throw new Error('Insufficient data for training');
      }

      // Use tf.tidy for automatic memory management
      const history = await tf.tidy(() => {
        const inputTensor = tf.tensor2d(inputs);
        const labelTensor = tf.tensor2d(labels);

        return this.model!.fit(inputTensor, labelTensor, {
          epochs,
          batchSize: 32,
          validationSplit: 0.2,
          shuffle: true,
          callbacks: {
            onEpochEnd: (epoch, logs) => {
              if (epoch % 10 === 0) {
                logger.info(`Training epoch ${epoch}`, logs);
              }
            },
          },
        });
      });

      logger.info('ML model training completed', {
        finalAccuracy: history.history.acc?.[history.history.acc.length - 1],
        finalLoss: history.history.loss?.[history.history.loss.length - 1],
      });
    } catch (error) {
      logger.error('Error training ML model', { error });
      throw error;
    } finally {
      this.isTraining = false;
    }
  }

  async predict(data: MarketData[]): Promise<MLPrediction> {
    if (!this.model) {
      throw new Error('Model not initialized');
    }

    if (data.length < this.LOOKBACK_PERIOD) {
      throw new Error(`Insufficient data for prediction. Need at least ${this.LOOKBACK_PERIOD} data points`);
    }

    try {
      const features: number[] = [];
      
      // Collect features for lookback period
      for (let i = data.length - this.LOOKBACK_PERIOD; i < data.length; i++) {
        const periodFeatures = this.extractFeatures(data, i);
        features.push(...periodFeatures);
      }

      // Use tf.tidy for automatic memory management
      const predictionArray = await tf.tidy(() => {
        const inputTensor = tf.tensor2d([features]);
        const prediction = this.model!.predict(inputTensor) as tf.Tensor;
        // Use dataSync() inside tidy for automatic cleanup
        return prediction.dataSync();
      });

      // Convert to action
      const buyProb = predictionArray[0];
      const holdProb = predictionArray[1];
      const sellProb = predictionArray[2];

      let action: 'buy' | 'sell' | 'hold';
      let confidence: number;

      if (buyProb > holdProb && buyProb > sellProb) {
        action = 'buy';
        confidence = buyProb;
      } else if (sellProb > holdProb && sellProb > buyProb) {
        action = 'sell';
        confidence = sellProb;
      } else {
        action = 'hold';
        confidence = holdProb;
      }

      // Get technical indicators for reasoning
      const indicators = this.calculateTechnicalIndicators(data, data.length - 1);
      const reasoning = this.generateReasoning(action, indicators, confidence);

      return {
        action,
        confidence,
        strength: Math.max(buyProb, sellProb) - holdProb,
        indicators,
        reasoning,
      };
    } catch (error) {
      logger.error('Error making prediction', { error });
      throw error;
    }
  }

  private generateReasoning(
    action: 'buy' | 'sell' | 'hold',
    indicators: TechnicalIndicators,
    confidence: number
  ): string[] {
    const reasoning: string[] = [];

    // RSI analysis
    if (indicators.rsi < 30) {
      reasoning.push('RSI indicates oversold conditions');
    } else if (indicators.rsi > 70) {
      reasoning.push('RSI indicates overbought conditions');
    }

    // MACD analysis
    if (indicators.macd.histogram > 0) {
      reasoning.push('MACD histogram shows bullish momentum');
    } else if (indicators.macd.histogram < 0) {
      reasoning.push('MACD histogram shows bearish momentum');
    }

    // Bollinger Bands analysis
    if (indicators.bollingerBands.lower > 0) {
      const currentPrice = indicators.bollingerBands.middle;
      const lowerDist = currentPrice - indicators.bollingerBands.lower;
      const upperDist = indicators.bollingerBands.upper - currentPrice;
      
      if (lowerDist < upperDist * 0.5) {
        reasoning.push('Price near lower Bollinger Band (potential bounce)');
      } else if (upperDist < lowerDist * 0.5) {
        reasoning.push('Price near upper Bollinger Band (potential reversal)');
      }
    }

    // EMA analysis
    if (indicators.ema.fast > indicators.ema.slow) {
      reasoning.push('Fast EMA above slow EMA (bullish signal)');
    } else {
      reasoning.push('Fast EMA below slow EMA (bearish signal)');
    }

    // Stochastic analysis
    if (indicators.stochastic.k < 20) {
      reasoning.push('Stochastic indicates oversold');
    } else if (indicators.stochastic.k > 80) {
      reasoning.push('Stochastic indicates overbought');
    }

    // ADX analysis
    if (indicators.adx > 25) {
      reasoning.push('Strong trend detected (ADX > 25)');
    } else {
      reasoning.push('Weak trend or ranging market (ADX < 25)');
    }

    // Action-specific reasoning
    reasoning.push(`${action.toUpperCase()} signal with ${(confidence * 100).toFixed(1)}% confidence`);

    return reasoning;
  }

  recordPredictionResult(predicted: string, actual: string): void {
    this.predictionHistory.push({
      predicted,
      actual,
      timestamp: Date.now(),
    });

    if (this.predictionHistory.length > this.MAX_HISTORY) {
      this.predictionHistory.shift();
    }
  }

  getAccuracy(): number {
    if (this.predictionHistory.length === 0) return 0;

    const correct = this.predictionHistory.filter(p => p.predicted === p.actual).length;
    return correct / this.predictionHistory.length;
  }

  async saveModel(botId: string): Promise<void> {
    try {
      const modelPath = `file://./models/${botId}`;
      await this.model!.save(modelPath);
      logger.info('ML model saved successfully', { botId, modelPath });
    } catch (error) {
      logger.error('Failed to save ML model', { error, botId });
      throw error;
    }
  }

  async loadModel(botId: string): Promise<boolean> {
    try {
      const modelPath = `file://./models/${botId}/model.json`;
      this.model = await tf.loadLayersModel(modelPath);
      logger.info('ML model loaded successfully', { botId });
      return true;
    } catch (error) {
      logger.warn('Failed to load ML model, using new model', { error, botId });
      return false;
    }
  }

  dispose(): void {
    if (this.model) {
      this.model.dispose();
    }
  }
}

export const enhancedMLEngine = new EnhancedMLEngine();
