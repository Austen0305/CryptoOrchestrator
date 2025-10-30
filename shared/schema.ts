import { z } from "zod";

export const tradingModeSchema = z.enum(["paper", "live"]);
export type TradingMode = z.infer<typeof tradingModeSchema>;

export const orderSideSchema = z.enum(["buy", "sell"]);
export type OrderSide = z.infer<typeof orderSideSchema>;

export const orderTypeSchema = z.enum(["market", "limit", "stop-loss"]);
export type OrderType = z.infer<typeof orderTypeSchema>;

export const orderStatusSchema = z.enum(["pending", "completed", "failed", "cancelled"]);
export type OrderStatus = z.infer<typeof orderStatusSchema>;

export const botStatusSchema = z.enum(["running", "stopped", "paused"]);
export type BotStatus = z.infer<typeof botStatusSchema>;

export const tradingPairSchema = z.object({
  symbol: z.string(),
  baseAsset: z.string(),
  quoteAsset: z.string(),
  currentPrice: z.number(),
  change24h: z.number(),
  volume24h: z.number(),
  high24h: z.number(),
  low24h: z.number(),
});
export type TradingPair = z.infer<typeof tradingPairSchema>;

export const krakenFeeSchema = z.object({
  maker: z.number(),
  taker: z.number(),
});
export type KrakenFee = z.infer<typeof krakenFeeSchema>;

export const tradeSchema = z.object({
  id: z.string(),
  botId: z.string().optional(),
  pair: z.string(),
  side: orderSideSchema,
  type: orderTypeSchema,
  amount: z.number(),
  price: z.number(),
  fee: z.number(),
  total: z.number(),
  totalWithFee: z.number(),
  status: orderStatusSchema,
  mode: tradingModeSchema,
  timestamp: z.number(),
});
export type Trade = z.infer<typeof tradeSchema>;

export const insertTradeSchema = tradeSchema.omit({ id: true, timestamp: true });
export type InsertTrade = z.infer<typeof insertTradeSchema>;

export const portfolioSchema = z.object({
  totalBalance: z.number(),
  availableBalance: z.number(),
  positions: z.record(z.object({
    asset: z.string(),
    amount: z.number(),
    averagePrice: z.number(),
    currentPrice: z.number(),
    totalValue: z.number(),
    profitLoss: z.number(),
    profitLossPercent: z.number(),
  })),
  profitLoss24h: z.number(),
  profitLossTotal: z.number(),
});
export type Portfolio = z.infer<typeof portfolioSchema>;

export const mlModelStateSchema = z.object({
  id: z.string(),
  botId: z.string(),
  qTable: z.record(z.record(z.number())),
  learningRate: z.number(),
  discountFactor: z.number(),
  epsilon: z.number(),
  trainingEpisodes: z.number(),
  totalReward: z.number(),
  averageReward: z.number(),
  lastUpdated: z.number(),
});
export type MLModelState = z.infer<typeof mlModelStateSchema>;

export const insertMLModelStateSchema = mlModelStateSchema.omit({ id: true, lastUpdated: true });
export type InsertMLModelState = z.infer<typeof insertMLModelStateSchema>;

export const botConfigSchema = z.object({
  id: z.string(),
  name: z.string(),
  strategy: z.string(),
  status: botStatusSchema,
  mode: tradingModeSchema,
  tradingPair: z.string(),
  maxPositionSize: z.number(),
  stopLoss: z.number(),
  takeProfit: z.number(),
  riskPerTrade: z.number(),
  profitLoss: z.number(),
  winRate: z.number(),
  totalTrades: z.number(),
  successfulTrades: z.number(),
  failedTrades: z.number(),
  createdAt: z.number(),
  updatedAt: z.number(),
});
export type BotConfig = z.infer<typeof botConfigSchema>;

export const insertBotConfigSchema = botConfigSchema.omit({ id: true, createdAt: true, updatedAt: true, profitLoss: true, winRate: true, totalTrades: true, successfulTrades: true, failedTrades: true });
export type InsertBotConfig = z.infer<typeof insertBotConfigSchema>;

export const marketDataSchema = z.object({
  pair: z.string(),
  timestamp: z.number(),
  open: z.number(),
  high: z.number(),
  low: z.number(),
  close: z.number(),
  volume: z.number(),
});
export type MarketData = z.infer<typeof marketDataSchema>;

export const performanceMetricsSchema = z.object({
  botId: z.string(),
  period: z.string(),
  totalReturn: z.number(),
  sharpeRatio: z.number(),
  maxDrawdown: z.number(),
  winRate: z.number(),
  averageWin: z.number(),
  averageLoss: z.number(),
  profitFactor: z.number(),
  totalTrades: z.number(),
});
export type PerformanceMetrics = z.infer<typeof performanceMetricsSchema>;
