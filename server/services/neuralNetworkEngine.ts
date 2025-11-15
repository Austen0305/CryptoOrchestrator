import * as tf from '@tensorflow/tfjs';
import type { MarketData, MLModelState } from "@shared/schema";
import { storage } from "../storage";

interface NeuralNetworkConfig {
  inputSize: number;
  hiddenLayers: number[];
  outputSize: number;
  learningRate: number;
  epochs: number;
  batchSize: number;
}

export class NeuralNetworkEngine {
  private model: tf.Sequential | null = null;
  private config: NeuralNetworkConfig;
  private isTrained: boolean = false;
  private recentPredictions: { predicted: string; actual: string }[] = [];
  private maxRecentPredictions = 100;
  private validationHistory: { loss: number; accuracy: number }[] = [];

  constructor(config: Partial<NeuralNetworkConfig> = {}) {
    this.config = {
      inputSize: 50, // Lookback period for technical indicators
      hiddenLayers: [128, 64, 32],
      outputSize: 3, // buy, sell, hold
      learningRate: 0.001,
      epochs: 100,
      batchSize: 32,
      ...config,
    };
  }

  getRecentAccuracy(): number {
    if (this.recentPredictions.length === 0) return 0.5; // Default to neutral weight
    const correct = this.recentPredictions.filter(p => p.predicted === p.actual).length;
    return correct / this.recentPredictions.length;
  }

  recordPredictionResult(predicted: string, actual: string): void {
    this.recentPredictions.push({ predicted, actual });
    if (this.recentPredictions.length > this.maxRecentPredictions) {
      this.recentPredictions.shift();
    }
  }

  private createModel(): tf.Sequential {
    const model = tf.sequential();

    // Input layer
    model.add(tf.layers.dense({
      inputShape: [this.config.inputSize],
      units: this.config.hiddenLayers[0],
      activation: 'relu',
      kernelInitializer: 'glorotUniform',
    }));

    // Hidden layers
    for (let i = 1; i < this.config.hiddenLayers.length; i++) {
      model.add(tf.layers.dense({
        units: this.config.hiddenLayers[i],
        activation: 'relu',
        kernelInitializer: 'glorotUniform',
      }));
      model.add(tf.layers.dropout({ rate: 0.2 }));
    }

    // Output layer
    model.add(tf.layers.dense({
      units: this.config.outputSize,
      activation: 'softmax',
      kernelInitializer: 'glorotUniform',
    }));

    model.compile({
      optimizer: tf.train.adam(this.config.learningRate),
      loss: 'categoricalCrossentropy',
      metrics: ['accuracy'],
    });

    return model;
  }

  private preprocessData(marketData: MarketData[]): { inputs: tf.Tensor2D; labels: tf.Tensor2D } {
    const inputs: number[][] = [];
    const labels: number[][] = [];

    for (let i = this.config.inputSize; i < marketData.length - 1; i++) {
      // Create input features from technical indicators
      const inputFeatures = this.extractFeatures(marketData, i);
      inputs.push(inputFeatures);

      // Create labels based on future price movement
      const currentPrice = marketData[i].close;
      const futurePrice = marketData[i + 1].close;
      const priceChange = (futurePrice - currentPrice) / currentPrice;

      // Label: 0=buy, 1=sell, 2=hold
      let label = [0, 0, 1]; // Default to hold
      if (priceChange > 0.002) {
        label = [1, 0, 0]; // Buy signal
      } else if (priceChange < -0.002) {
        label = [0, 1, 0]; // Sell signal
      }

      labels.push(label);
    }

    // Use tf.tidy for automatic memory management
    return tf.tidy(() => ({
      inputs: tf.tensor2d(inputs),
      labels: tf.tensor2d(labels),
    }));
  }

  private extractFeatures(marketData: MarketData[], index: number): number[] {
    const features: number[] = [];
    const lookback = Math.min(this.config.inputSize, index);

    // Price data (normalized)
    for (let i = index - lookback; i < index; i++) {
      const data = marketData[i];
      const basePrice = marketData[index - lookback].close;
      features.push(
        (data.open - basePrice) / basePrice,
        (data.high - basePrice) / basePrice,
        (data.low - basePrice) / basePrice,
        (data.close - basePrice) / basePrice,
        data.volume / 1000000 // Normalize volume
      );
    }

    // Fill remaining features with zeros if not enough data
    while (features.length < this.config.inputSize) {
      features.push(0);
    }

    return features.slice(0, this.config.inputSize);
  }

  async train(marketData: MarketData[]): Promise<void> {
    if (marketData.length < this.config.inputSize + 10) {
      throw new Error('Insufficient data for training');
    }

    this.model = this.createModel();
    const { inputs, labels } = this.preprocessData(marketData);

    try {
      await this.model.fit(inputs, labels, {
        epochs: this.config.epochs,
        batchSize: this.config.batchSize,
        validationSplit: 0.2,
        callbacks: {
          onEpochEnd: (epoch, logs) => {
            if (epoch % 10 === 0) {
              console.log(`Epoch ${epoch}: loss = ${logs?.loss.toFixed(4)}, accuracy = ${logs?.acc.toFixed(4)}`);
            }
          },
        },
      });

      this.isTrained = true;
    } finally {
      // Clean up tensors
      inputs.dispose();
      labels.dispose();
    }
  }

  predict(marketData: MarketData[]): { action: 'buy' | 'sell' | 'hold'; confidence: number } {
    if (!this.model || !this.isTrained) {
      return { action: 'hold', confidence: 0 };
    }

    const features = this.extractFeatures(marketData, marketData.length - 1);
    
    // Use tf.tidy for automatic memory management
    return tf.tidy(() => {
      const input = tf.tensor2d([features]);
      const prediction = this.model!.predict(input) as tf.Tensor;
      const probabilities = prediction.dataSync();

      const actions = ['buy', 'sell', 'hold'] as const;
      const maxIndex = Array.from(probabilities).indexOf(Math.max(...Array.from(probabilities)));

      return {
        action: actions[maxIndex],
        confidence: probabilities[maxIndex],
      };
    });
  }

  async saveModel(botId: string): Promise<void> {
    if (!this.model) return;

    const modelData = {
      modelJSON: await this.model.toJSON(),
      modelWeights: this.model.getWeights().map(w => w.arraySync()),
      format: "layers-model",
      generatedBy: "CryptoOrchestrator",
      convertedBy: null,
      modelArtifactsInfo: {
        dateSaved: new Date(),
        modelTopologyType: "Sequential",
      }
    };

    await storage.saveMLModelState({
      botId,
      neuralNetworkWeights: modelData,
      config: this.config,
      isTrained: this.isTrained,
      trainingEpisodes: 0,
      totalReward: 0,
      averageReward: 0,
      learningRate: 0,
      discountFactor: 0,
      epsilon: 0,
      qTable: {},
    });
  }

  async loadModel(botId: string): Promise<boolean> {
    const modelState = await storage.getMLModelState(botId);
    if (!modelState?.neuralNetworkWeights) {
      return false;
    }

    try {
      const loadedModel = await tf.loadLayersModel(tf.io.fromMemory(modelState.neuralNetworkWeights));
      this.model = tf.sequential();
      this.model.add(loadedModel.layers[0]); // Transfer layers from loaded model
      this.config = modelState.config || this.config;
      this.isTrained = modelState.isTrained || false;
      return true;
    } catch (error) {
      console.error('Error loading neural network model:', error);
      return false;
    }
  }

  dispose(): void {
    if (this.model) {
      this.model.dispose();
      this.model = null;
    }
  }
}

export const neuralNetworkEngine = new NeuralNetworkEngine();
