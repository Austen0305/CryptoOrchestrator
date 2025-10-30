import type { MLModelState, MarketData } from "@shared/schema";
import { storage } from "../storage";

interface State {
  priceDirection: "up" | "down" | "stable";
  rsi: "oversold" | "neutral" | "overbought";
  volume: "low" | "medium" | "high";
}

type Action = "buy" | "sell" | "hold";

export class MLEngine {
  private learningRate: number;
  private discountFactor: number;
  private epsilon: number;
  private epsilonDecay: number = 0.995;
  private epsilonMin: number = 0.01;

  constructor(
    learningRate: number = 0.1,
    discountFactor: number = 0.95,
    epsilon: number = 1.0
  ) {
    this.learningRate = learningRate;
    this.discountFactor = discountFactor;
    this.epsilon = epsilon;
  }

  private getStateKey(state: State): string {
    return `${state.priceDirection}_${state.rsi}_${state.volume}`;
  }

  private initializeQValue(qTable: Record<string, Record<string, number>>, stateKey: string, action: Action): void {
    if (!qTable[stateKey]) {
      qTable[stateKey] = {};
    }
    if (qTable[stateKey][action] === undefined) {
      qTable[stateKey][action] = 0;
    }
  }

  private getQValue(qTable: Record<string, Record<string, number>>, stateKey: string, action: Action): number {
    this.initializeQValue(qTable, stateKey, action);
    return qTable[stateKey][action];
  }

  private getBestAction(qTable: Record<string, Record<string, number>>, stateKey: string): Action {
    const actions: Action[] = ["buy", "sell", "hold"];
    let bestAction: Action = "hold";
    let bestValue = -Infinity;

    for (const action of actions) {
      const value = this.getQValue(qTable, stateKey, action);
      if (value > bestValue) {
        bestValue = value;
        bestAction = action;
      }
    }

    return bestAction;
  }

  chooseAction(qTable: Record<string, Record<string, number>>, state: State): Action {
    if (Math.random() < this.epsilon) {
      const actions: Action[] = ["buy", "sell", "hold"];
      return actions[Math.floor(Math.random() * actions.length)];
    }

    const stateKey = this.getStateKey(state);
    return this.getBestAction(qTable, stateKey);
  }

  updateQValue(
    qTable: Record<string, Record<string, number>>,
    state: State,
    action: Action,
    reward: number,
    nextState: State
  ): void {
    const stateKey = this.getStateKey(state);
    const nextStateKey = this.getStateKey(nextState);

    const currentQ = this.getQValue(qTable, stateKey, action);
    const maxNextQ = Math.max(
      this.getQValue(qTable, nextStateKey, "buy"),
      this.getQValue(qTable, nextStateKey, "sell"),
      this.getQValue(qTable, nextStateKey, "hold")
    );

    const newQ = currentQ + this.learningRate * (reward + this.discountFactor * maxNextQ - currentQ);

    this.initializeQValue(qTable, stateKey, action);
    qTable[stateKey][action] = newQ;
  }

  calculateReward(
    action: Action,
    entryPrice: number,
    exitPrice: number,
    position: "long" | "short" | null
  ): number {
    if (action === "hold") {
      return -0.01;
    }

    const priceChange = (exitPrice - entryPrice) / entryPrice;

    if (action === "buy" && position === null) {
      return priceChange > 0 ? priceChange * 10 : priceChange * 5;
    }

    if (action === "sell" && position === "long") {
      return priceChange > 0 ? priceChange * 10 : priceChange * 5;
    }

    if (action === "sell" && position === null) {
      return -priceChange > 0 ? -priceChange * 10 : -priceChange * 5;
    }

    if (action === "buy" && position === "short") {
      return -priceChange > 0 ? -priceChange * 10 : -priceChange * 5;
    }

    return -1;
  }

  deriveState(marketData: MarketData[], currentIndex: number): State {
    const current = marketData[currentIndex];
    const previous = currentIndex > 0 ? marketData[currentIndex - 1] : current;

    const priceChange = (current.close - previous.close) / previous.close;
    const priceDirection: State["priceDirection"] =
      priceChange > 0.001 ? "up" : priceChange < -0.001 ? "down" : "stable";

    const rsi = this.calculateRSI(marketData, currentIndex);
    const rsiState: State["rsi"] =
      rsi < 30 ? "oversold" : rsi > 70 ? "overbought" : "neutral";

    const avgVolume = marketData.slice(Math.max(0, currentIndex - 20), currentIndex).reduce((sum, d) => sum + d.volume, 0) / 20;
    const volumeState: State["volume"] =
      current.volume > avgVolume * 1.5 ? "high" : current.volume < avgVolume * 0.5 ? "low" : "medium";

    return {
      priceDirection,
      rsi: rsiState,
      volume: volumeState,
    };
  }

  private calculateRSI(data: MarketData[], currentIndex: number, period: number = 14): number {
    if (currentIndex < period) return 50;

    let gains = 0;
    let losses = 0;

    for (let i = currentIndex - period + 1; i <= currentIndex; i++) {
      const change = data[i].close - data[i - 1].close;
      if (change > 0) {
        gains += change;
      } else {
        losses += Math.abs(change);
      }
    }

    const avgGain = gains / period;
    const avgLoss = losses / period;

    if (avgLoss === 0) return 100;

    const rs = avgGain / avgLoss;
    return 100 - 100 / (1 + rs);
  }

  decayEpsilon(): void {
    this.epsilon = Math.max(this.epsilonMin, this.epsilon * this.epsilonDecay);
  }

  async saveModel(botId: string, qTable: Record<string, Record<string, number>>, trainingEpisodes: number, totalReward: number): Promise<void> {
    await storage.saveMLModelState({
      botId,
      qTable,
      learningRate: this.learningRate,
      discountFactor: this.discountFactor,
      epsilon: this.epsilon,
      trainingEpisodes,
      totalReward,
      averageReward: totalReward / Math.max(1, trainingEpisodes),
    });
  }

  async loadModel(botId: string): Promise<MLModelState | null> {
    const model = await storage.getMLModelState(botId);
    if (model) {
      this.learningRate = model.learningRate;
      this.discountFactor = model.discountFactor;
      this.epsilon = model.epsilon;
      return model;
    }
    return null;
  }
}

export const mlEngine = new MLEngine();
