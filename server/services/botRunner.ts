import type { BotConfig, MarketData } from "@shared/schema";
import { storage } from "../storage";
import { krakenService } from "./krakenService";
import { mlEngine, MLEngine } from "./mlEngine";
import { paperTradingService } from "./paperTradingService";

interface RunningBot {
  config: BotConfig;
  mlEngine: MLEngine;
  intervalId: NodeJS.Timeout | null;
  qTable: Record<string, Record<string, number>>;
  position: "long" | "short" | null;
  entryPrice: number | null;
  trainingEpisodes: number;
  totalReward: number;
}

export class BotRunner {
  private runningBots: Map<string, RunningBot>;

  constructor() {
    this.runningBots = new Map();
  }

  async startBot(botId: string): Promise<{ success: boolean; message: string }> {
    try {
      const config = await storage.getBotById(botId);
      if (!config) {
        return { success: false, message: "Bot not found" };
      }

      if (this.runningBots.has(botId)) {
        return { success: false, message: "Bot is already running" };
      }

      const engine = new MLEngine(0.1, 0.95, 1.0);
      const existingModel = await engine.loadModel(botId);

      const runningBot: RunningBot = {
        config,
        mlEngine: engine,
        intervalId: null,
        qTable: existingModel?.qTable || {},
        position: null,
        entryPrice: null,
        trainingEpisodes: existingModel?.trainingEpisodes || 0,
        totalReward: existingModel?.totalReward || 0,
      };

      await storage.updateBot(botId, { status: "running" });

      runningBot.intervalId = setInterval(async () => {
        await this.executeBotCycle(botId);
      }, 60000);

      this.runningBots.set(botId, runningBot);

      return { success: true, message: "Bot started successfully" };
    } catch (error) {
      console.error("Error starting bot:", error);
      return { success: false, message: error instanceof Error ? error.message : "Unknown error" };
    }
  }

  async stopBot(botId: string): Promise<{ success: boolean; message: string }> {
    const runningBot = this.runningBots.get(botId);
    if (!runningBot) {
      return { success: false, message: "Bot is not running" };
    }

    if (runningBot.intervalId) {
      clearInterval(runningBot.intervalId);
    }

    await runningBot.mlEngine.saveModel(
      botId,
      runningBot.qTable,
      runningBot.trainingEpisodes,
      runningBot.totalReward
    );

    await storage.updateBot(botId, { status: "stopped" });

    this.runningBots.delete(botId);

    return { success: true, message: "Bot stopped successfully" };
  }

  private async executeBotCycle(botId: string): Promise<void> {
    const runningBot = this.runningBots.get(botId);
    if (!runningBot) return;

    try {
      const { config, mlEngine: engine, qTable } = runningBot;

      const marketData = await storage.getMarketData(config.tradingPair, 50);
      if (marketData.length < 20) {
        console.log(`Not enough market data for bot ${botId}`);
        return;
      }

      const currentIndex = marketData.length - 1;
      const state = engine.deriveState(marketData, currentIndex);
      const action = engine.chooseAction(qTable, state);

      const currentPrice = marketData[currentIndex].close;

      if (action === "buy" && runningBot.position === null) {
        const result = await paperTradingService.executeTrade(
          config.tradingPair,
          "buy",
          "market",
          config.maxPositionSize / currentPrice,
          undefined,
          botId
        );

        if (result.success) {
          runningBot.position = "long";
          runningBot.entryPrice = currentPrice;
          console.log(`Bot ${botId} opened long position at ${currentPrice}`);
        }
      } else if (action === "sell" && runningBot.position === "long") {
        const result = await paperTradingService.executeTrade(
          config.tradingPair,
          "sell",
          "market",
          config.maxPositionSize / (runningBot.entryPrice || currentPrice),
          undefined,
          botId
        );

        if (result.success && runningBot.entryPrice) {
          const reward = engine.calculateReward(action, runningBot.entryPrice, currentPrice, runningBot.position);
          runningBot.totalReward += reward;

          if (currentIndex < marketData.length - 1) {
            const nextState = engine.deriveState(marketData, currentIndex + 1);
            engine.updateQValue(qTable, state, action, reward, nextState);
          }

          runningBot.position = null;
          runningBot.entryPrice = null;
          runningBot.trainingEpisodes++;

          console.log(`Bot ${botId} closed position at ${currentPrice}, reward: ${reward.toFixed(4)}`);

          const profitLoss = runningBot.entryPrice ? (currentPrice - runningBot.entryPrice) * (config.maxPositionSize / runningBot.entryPrice) : 0;
          const trades = await storage.getTrades(botId);
          const successfulTrades = trades.filter(t => {
            if (t.side === "sell") {
              const buyTrade = trades.find(bt => bt.id !== t.id && bt.side === "buy" && bt.timestamp < t.timestamp);
              return buyTrade && t.price > buyTrade.price;
            }
            return false;
          }).length;

          await storage.updateBot(botId, {
            profitLoss: config.profitLoss + profitLoss,
            totalTrades: config.totalTrades + 1,
            successfulTrades: config.successfulTrades + (profitLoss > 0 ? 1 : 0),
            failedTrades: config.failedTrades + (profitLoss <= 0 ? 1 : 0),
            winRate: ((config.successfulTrades + (profitLoss > 0 ? 1 : 0)) / (config.totalTrades + 1)) * 100,
          });
        }
      }

      engine.decayEpsilon();

      if (runningBot.trainingEpisodes % 10 === 0) {
        await engine.saveModel(botId, qTable, runningBot.trainingEpisodes, runningBot.totalReward);
      }
    } catch (error) {
      console.error(`Error in bot cycle for ${botId}:`, error);
    }
  }

  async getRunningBots(): Promise<string[]> {
    return Array.from(this.runningBots.keys());
  }

  isRunning(botId: string): boolean {
    return this.runningBots.has(botId);
  }
}

export const botRunner = new BotRunner();
