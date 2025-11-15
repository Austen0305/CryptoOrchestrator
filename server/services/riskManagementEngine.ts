import type { BotConfig, Trade, Portfolio, MarketData } from "@shared/schema";
import { storage } from "../storage";
import { VolatilityAnalyzer } from "./volatilityAnalyzer";
import { getDefaultExchange } from './exchangeManager';

interface RiskMetrics {
  currentDrawdown: number;
  maxDrawdown: number;
  dailyLoss: number;
  positionSize: number;
  totalExposure: number;
  riskPerTrade: number;
}

interface RiskLimits {
  maxDrawdown: number;
  maxDailyLoss: number;
  maxPositionSize: number;
  maxTotalExposure: number;
  stopLossMultiplier: number;
  takeProfitMultiplier: number;
  minPositionSize: number; // Minimum position size for micro trading
  microModeEnabled: boolean; // Enable micro trading mode
  persistentMode: boolean; // Enable persistent mode - bots don't stop automatically
}

export class RiskManagementEngine {
  private defaultLimits: RiskLimits = {
    maxDrawdown: 0.10, // 10% max drawdown
    maxDailyLoss: 0.05, // 5% max daily loss
    maxPositionSize: 0.10, // 10% of portfolio per position
    maxTotalExposure: 0.50, // 50% max total exposure
    stopLossMultiplier: 1.5, // Stop loss at 1.5x risk per trade
    takeProfitMultiplier: 3.0, // Take profit at 3x risk per trade
    minPositionSize: 0.0001, // Minimum position size for micro trading (0.01% of portfolio)
    microModeEnabled: true, // Enable micro trading mode by default
    persistentMode: true, // Enable persistent mode - bots don't stop automatically
  };

  private volatilityAnalyzer: VolatilityAnalyzer;
  private historicalVolatility: number = 0;
  private lastVolatilityUpdate: number = 0;
  private volatilityUpdateInterval = 1000 * 60 * 15; // 15 minutes

  constructor() {
    this.volatilityAnalyzer = new VolatilityAnalyzer();
    this.updateHistoricalVolatility();
  }

  private async updateHistoricalVolatility() {
    const now = Date.now();
    if (now - this.lastVolatilityUpdate < this.volatilityUpdateInterval) {
      return;
    }

    try {
      const exchange = getDefaultExchange();
      const historicalData = await exchange.getHistoricalData("BTC/USD", "1h", 168); // 1 week of hourly data
      this.historicalVolatility = this.volatilityAnalyzer.calculateVolatilityIndex(historicalData);
      this.lastVolatilityUpdate = now;
    } catch (error) {
      console.error("Failed to update historical volatility:", error);
    }
  }

  async calculateRiskMetrics(botId: string, portfolio: Portfolio): Promise<RiskMetrics> {
    const trades = await storage.getTrades(botId, 'paper');
    const bot = await storage.getBotById(botId);

    if (!bot) {
      throw new Error('Bot not found');
    }

    // Calculate current drawdown
    const equityCurve = this.calculateEquityCurve(trades, portfolio.totalBalance);
    const currentDrawdown = this.calculateCurrentDrawdown(equityCurve);

    // Calculate max drawdown
    const maxDrawdown = this.calculateMaxDrawdown(equityCurve);

    // Calculate daily P&L
    const dailyPnL = this.calculateDailyPnL(trades);
    const dailyLoss = Math.abs(Math.min(...dailyPnL));

    // Calculate position metrics
    const positionSize = this.calculateCurrentPositionSize(portfolio);
    const totalExposure = this.calculateTotalExposure(portfolio);

    return {
      currentDrawdown,
      maxDrawdown,
      dailyLoss,
      positionSize,
      totalExposure,
      riskPerTrade: bot.riskPerTrade,
    };
  }

  shouldStopTrading(botId: string, portfolio: Portfolio): Promise<{ shouldStop: boolean; reason?: string }> {
    return this.calculateRiskMetrics(botId, portfolio).then(metrics => {
      const limits = this.defaultLimits;

      // If persistent mode is enabled, never stop trading automatically
      if (limits.persistentMode) {
        return { shouldStop: false };
      }

      if (metrics.currentDrawdown >= limits.maxDrawdown) {
        return { shouldStop: true, reason: `Max drawdown exceeded: ${metrics.currentDrawdown.toFixed(2)} >= ${limits.maxDrawdown}` };
      }

      if (metrics.dailyLoss >= limits.maxDailyLoss) {
        return { shouldStop: true, reason: `Daily loss limit exceeded: ${metrics.dailyLoss.toFixed(2)} >= ${limits.maxDailyLoss}` };
      }

      if (metrics.totalExposure >= limits.maxTotalExposure) {
        return { shouldStop: true, reason: `Total exposure limit exceeded: ${metrics.totalExposure.toFixed(2)} >= ${limits.maxTotalExposure}` };
      }

      return { shouldStop: false };
    });
  }

  calculatePositionSizeForTrade(botConfig: BotConfig, portfolio: Portfolio, currentPrice: number): number {
    const availableBalance = portfolio.availableBalance;
    
    // Calculate Kelly Criterion
    const wins = portfolio.successfulTrades || 0;
    const losses = portfolio.failedTrades || 0;
    const totalTrades = wins + losses;
    
    let kellyFraction = 0;
    if (totalTrades > 0) {
      const winRate = wins / totalTrades;
      const winMultiplier = botConfig.takeProfit / botConfig.stopLoss;
      const lossMultiplier = 1;
      
      kellyFraction = (winRate * winMultiplier - (1 - winRate) * lossMultiplier) / winMultiplier;
      // Use half-Kelly for more conservative sizing
      kellyFraction = Math.max(0, kellyFraction * 0.5);
    } else {
      // Start conservative with 1% if no trade history
      kellyFraction = 0.01;
    }
    
    // Calculate position size based on risk and Kelly Criterion
    const riskAmount = availableBalance * botConfig.riskPerTrade * kellyFraction;
    const stopLossAmount = currentPrice * botConfig.stopLoss;

    if (stopLossAmount === 0) return 0;

    const positionSize = riskAmount / stopLossAmount;
    const maxPositionSize = availableBalance * this.defaultLimits.maxPositionSize / currentPrice;

    // Apply micro trading limits if enabled
    let finalPositionSize = Math.min(positionSize, maxPositionSize);

    if (this.defaultLimits.microModeEnabled) {
      // Ensure position size doesn't go below minimum for micro trading
      const minPositionValue = availableBalance * this.defaultLimits.minPositionSize;
      const minPositionSize = minPositionValue / currentPrice;

      // For small balances, allow micro positions but cap at a reasonable maximum
      if (availableBalance < 1000) { // Less than $1000 balance
        finalPositionSize = Math.max(finalPositionSize, minPositionSize);
        // Cap at 1% of available balance for safety
        finalPositionSize = Math.min(finalPositionSize, availableBalance * 0.01 / currentPrice);
      }
    }

    return finalPositionSize;
  }

  // Backwards-compatible alias expected by some callers
  public calculatePositionSize(botConfig: BotConfig, portfolio: Portfolio, currentPrice: number): number {
    return this.calculatePositionSizeForTrade(botConfig, portfolio, currentPrice);
  }

  calculateDynamicStopLoss(entryPrice: number, currentPrice: number, botConfig: BotConfig): number {
    const riskAmount = entryPrice * botConfig.riskPerTrade;
    const stopLossDistance = riskAmount / (entryPrice * this.defaultLimits.stopLossMultiplier);

    // Trailing stop loss
    const trailingStop = currentPrice * (1 - stopLossDistance);

    // Ensure stop loss is below entry for long positions
    return Math.min(trailingStop, entryPrice * (1 - botConfig.stopLoss));
  }

  calculateTakeProfit(entryPrice: number, botConfig: BotConfig): number {
    return entryPrice * (1 + botConfig.takeProfit * this.defaultLimits.takeProfitMultiplier);
  }

  private calculateEquityCurve(trades: Trade[], initialBalance: number): number[] {
    let balance = initialBalance;
    const equity: number[] = [balance];

    // Group trades by day (simplified)
    const dailyTrades = new Map<number, Trade[]>();

    trades.forEach(trade => {
      const day = Math.floor(trade.timestamp / (24 * 60 * 60 * 1000));
      if (!dailyTrades.has(day)) {
        dailyTrades.set(day, []);
      }
      dailyTrades.get(day)!.push(trade);
    });

    // Calculate daily equity
    Array.from(dailyTrades.keys()).sort().forEach(day => {
      const dayTrades = dailyTrades.get(day)!;
      dayTrades.forEach(trade => {
        if (trade.side === 'buy') {
          balance -= trade.totalWithFee;
        } else {
          balance += trade.total - trade.fee;
        }
      });
      equity.push(balance);
    });

    return equity;
  }

  private calculateCurrentDrawdown(equityCurve: number[]): number {
    if (equityCurve.length === 0) return 0;

    const peak = Math.max(...equityCurve);
    const current = equityCurve[equityCurve.length - 1];

    return peak > 0 ? (peak - current) / peak : 0;
  }

  private calculateMaxDrawdown(equityCurve: number[]): number {
    if (equityCurve.length < 2) return 0;

    let maxDrawdown = 0;
    let peak = equityCurve[0];

    for (let i = 1; i < equityCurve.length; i++) {
      if (equityCurve[i] > peak) {
        peak = equityCurve[i];
      }

      const drawdown = (peak - equityCurve[i]) / peak;
      maxDrawdown = Math.max(maxDrawdown, drawdown);
    }

    return maxDrawdown;
  }

  private calculateDailyPnL(trades: Trade[]): number[] {
    const dailyPnL = new Map<number, number>();

    trades.forEach(trade => {
      const day = Math.floor(trade.timestamp / (24 * 60 * 60 * 1000));
      const pnl = trade.side === 'buy' ? -trade.totalWithFee : trade.total - trade.fee;

      dailyPnL.set(day, (dailyPnL.get(day) || 0) + pnl);
    });

    return Array.from(dailyPnL.values());
  }

  private calculateCurrentPositionSize(portfolio: Portfolio): number {
      const totalValue = Object.values(portfolio.positions).reduce((sum, pos) => {
        if (typeof sum === 'number' && typeof pos.totalValue === 'number') {
          return sum + pos.totalValue;
        }
        return sum;
      }, 0);
    return portfolio.totalBalance > 0 ? totalValue / portfolio.totalBalance : 0;
  }

  private calculateTotalExposure(portfolio: Portfolio): number {
    return this.calculateCurrentPositionSize(portfolio);
  }

  updateRiskLimits(limits: Partial<RiskLimits>): void {
    this.defaultLimits = { ...this.defaultLimits, ...limits };
  }

  getRiskLimits(): RiskLimits {
    return { ...this.defaultLimits };
  }
}

export const riskManagementEngine = new RiskManagementEngine();
