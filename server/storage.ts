import {
  type Trade,
  type InsertTrade,
  type BotConfig,
  type InsertBotConfig,
  type MLModelState,
  type InsertMLModelState,
  type Portfolio,
  type TradingPair,
  type PerformanceMetrics,
  type MarketData,
  type TradingMode,
} from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  getTrades(botId?: string, mode?: TradingMode): Promise<Trade[]>;
  getTradeById(id: string): Promise<Trade | undefined>;
  createTrade(trade: InsertTrade): Promise<Trade>;
  
  getBots(): Promise<BotConfig[]>;
  getBotById(id: string): Promise<BotConfig | undefined>;
  createBot(bot: InsertBotConfig): Promise<BotConfig>;
  updateBot(id: string, updates: Partial<BotConfig>): Promise<BotConfig | undefined>;
  deleteBot(id: string): Promise<boolean>;
  
  getMLModelState(botId: string): Promise<MLModelState | undefined>;
  saveMLModelState(state: InsertMLModelState): Promise<MLModelState>;
  updateMLModelState(id: string, updates: Partial<MLModelState>): Promise<MLModelState | undefined>;
  
  getPortfolio(mode: TradingMode): Promise<Portfolio>;
  updatePortfolio(mode: TradingMode, portfolio: Portfolio): Promise<Portfolio>;
  
  getTradingPairs(): Promise<TradingPair[]>;
  updateTradingPairs(pairs: TradingPair[]): Promise<void>;
  
  getPerformanceMetrics(botId: string): Promise<PerformanceMetrics | undefined>;
  savePerformanceMetrics(metrics: PerformanceMetrics): Promise<void>;
  
  getMarketData(pair: string, limit?: number): Promise<MarketData[]>;
  saveMarketData(data: MarketData): Promise<void>;
}

export class MemStorage implements IStorage {
  private trades: Map<string, Trade>;
  private bots: Map<string, BotConfig>;
  private mlModels: Map<string, MLModelState>;
  private portfolios: Map<TradingMode, Portfolio>;
  private tradingPairs: TradingPair[];
  private performanceMetrics: Map<string, PerformanceMetrics>;
  private marketData: Map<string, MarketData[]>;

  constructor() {
    this.trades = new Map();
    this.bots = new Map();
    this.mlModels = new Map();
    this.portfolios = new Map();
    this.tradingPairs = [];
    this.performanceMetrics = new Map();
    this.marketData = new Map();
    
    this.portfolios.set("paper", {
      totalBalance: 100000,
      availableBalance: 100000,
      positions: {},
      profitLoss24h: 0,
      profitLossTotal: 0,
    });
    
    this.portfolios.set("live", {
      totalBalance: 0,
      availableBalance: 0,
      positions: {},
      profitLoss24h: 0,
      profitLossTotal: 0,
    });
  }

  async getTrades(botId?: string, mode?: TradingMode): Promise<Trade[]> {
    let trades = Array.from(this.trades.values());
    if (botId) {
      trades = trades.filter((t) => t.botId === botId);
    }
    if (mode) {
      trades = trades.filter((t) => t.mode === mode);
    }
    return trades.sort((a, b) => b.timestamp - a.timestamp);
  }

  async getTradeById(id: string): Promise<Trade | undefined> {
    return this.trades.get(id);
  }

  async createTrade(insertTrade: InsertTrade): Promise<Trade> {
    const id = randomUUID();
    const trade: Trade = {
      ...insertTrade,
      id,
      timestamp: Date.now(),
    };
    this.trades.set(id, trade);
    return trade;
  }

  async getBots(): Promise<BotConfig[]> {
    return Array.from(this.bots.values()).sort((a, b) => b.updatedAt - a.updatedAt);
  }

  async getBotById(id: string): Promise<BotConfig | undefined> {
    return this.bots.get(id);
  }

  async createBot(insertBot: InsertBotConfig): Promise<BotConfig> {
    const id = randomUUID();
    const now = Date.now();
    const bot: BotConfig = {
      ...insertBot,
      id,
      profitLoss: 0,
      winRate: 0,
      totalTrades: 0,
      successfulTrades: 0,
      failedTrades: 0,
      createdAt: now,
      updatedAt: now,
    };
    this.bots.set(id, bot);
    return bot;
  }

  async updateBot(id: string, updates: Partial<BotConfig>): Promise<BotConfig | undefined> {
    const bot = this.bots.get(id);
    if (!bot) return undefined;
    
    const updated = {
      ...bot,
      ...updates,
      updatedAt: Date.now(),
    };
    this.bots.set(id, updated);
    return updated;
  }

  async deleteBot(id: string): Promise<boolean> {
    return this.bots.delete(id);
  }

  async getMLModelState(botId: string): Promise<MLModelState | undefined> {
    return Array.from(this.mlModels.values()).find((m) => m.botId === botId);
  }

  async saveMLModelState(insertState: InsertMLModelState): Promise<MLModelState> {
    const existing = await this.getMLModelState(insertState.botId);
    if (existing) {
      const updated: MLModelState = {
        ...existing,
        ...insertState,
        lastUpdated: Date.now(),
      };
      this.mlModels.set(existing.id, updated);
      return updated;
    }
    
    const id = randomUUID();
    const state: MLModelState = {
      ...insertState,
      id,
      lastUpdated: Date.now(),
    };
    this.mlModels.set(id, state);
    return state;
  }

  async updateMLModelState(id: string, updates: Partial<MLModelState>): Promise<MLModelState | undefined> {
    const state = this.mlModels.get(id);
    if (!state) return undefined;
    
    const updated: MLModelState = {
      ...state,
      ...updates,
      lastUpdated: Date.now(),
    };
    this.mlModels.set(id, updated);
    return updated;
  }

  async getPortfolio(mode: TradingMode): Promise<Portfolio> {
    return this.portfolios.get(mode) || {
      totalBalance: 0,
      availableBalance: 0,
      positions: {},
      profitLoss24h: 0,
      profitLossTotal: 0,
    };
  }

  async updatePortfolio(mode: TradingMode, portfolio: Portfolio): Promise<Portfolio> {
    this.portfolios.set(mode, portfolio);
    return portfolio;
  }

  async getTradingPairs(): Promise<TradingPair[]> {
    return this.tradingPairs;
  }

  async updateTradingPairs(pairs: TradingPair[]): Promise<void> {
    this.tradingPairs = pairs;
  }

  async getPerformanceMetrics(botId: string): Promise<PerformanceMetrics | undefined> {
    return this.performanceMetrics.get(botId);
  }

  async savePerformanceMetrics(metrics: PerformanceMetrics): Promise<void> {
    this.performanceMetrics.set(metrics.botId, metrics);
  }

  async getMarketData(pair: string, limit: number = 100): Promise<MarketData[]> {
    const data = this.marketData.get(pair) || [];
    return data.slice(-limit);
  }

  async saveMarketData(data: MarketData): Promise<void> {
    const existing = this.marketData.get(data.pair) || [];
    existing.push(data);
    if (existing.length > 1000) {
      existing.shift();
    }
    this.marketData.set(data.pair, existing);
  }
}

export const storage = new MemStorage();
