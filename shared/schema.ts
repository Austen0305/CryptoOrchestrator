import { z } from "zod";

export const userProfileSchema = z.object({
  id: z.string().optional(),
  email: z.string().email(),
  name: z.string().min(2),
  password: z.string().min(8),
  role: z.enum(["user", "admin"]).default("user"),
  mfaEnabled: z.boolean().optional(),
  createdAt: z.date().optional(),
  updatedAt: z.date().optional(),
});

export const userLoginSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

export type UserProfile = z.infer<typeof userProfileSchema>;
export type UserLogin = z.infer<typeof userLoginSchema>;

export const tradingModeSchema = z.enum(["paper", "live"]);
export type TradingMode = z.infer<typeof tradingModeSchema>;

export const orderSideSchema = z.enum(["buy", "sell"]);
export type OrderSide = z.infer<typeof orderSideSchema>;

export const orderTypeSchema = z.enum(["market", "limit", "stop-loss"]);
export type OrderType = z.infer<typeof orderTypeSchema>;

export const orderStatusSchema = z.enum(["pending", "completed", "failed", "cancelled"]);

export const rateLimitInfoSchema = z.object({
  remaining: z.number(),
  reset: z.number(),
});

export const botSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  active: z.boolean(),
  tradingMode: tradingModeSchema,
  tradingPairs: z.array(z.string()),
  strategy: z.object({
    name: z.string(),
    parameters: z.record(z.string(), z.any()),
  }),
  riskLimits: z.object({
    maxPosition: z.number(),
    maxLoss: z.number(),
    stopLoss: z.number().optional(),
    takeProfit: z.number().optional(),
  }),
});

export type Bot = z.infer<typeof botSchema>;
export type RateLimitInfo = z.infer<typeof rateLimitInfoSchema>;
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
    positions: z.record(z.string(), z.object({
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
  successfulTrades: z.number().optional(),
  failedTrades: z.number().optional(),
  totalTrades: z.number().optional(),
  winRate: z.number().optional(),
  averageWin: z.number().optional(),
  averageLoss: z.number().optional(),
});
export type Portfolio = z.infer<typeof portfolioSchema>;

export const mlModelStateSchema = z.object({
  id: z.string(),
  botId: z.string(),
  // Q-learning state table: stateKey -> actionKey -> numeric value
  qTable: z.record(z.string(), z.record(z.string(), z.number())),
  learningRate: z.number(),
  discountFactor: z.number(),
  epsilon: z.number(),
  trainingEpisodes: z.number(),
  totalReward: z.number(),
  averageReward: z.number(),
  neuralNetworkWeights: z.any().optional(),
  config: z.any().optional(),
  isTrained: z.boolean().optional(),
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

// User authentication schemas
// User schemas
export const userSchema = z.object({
  id: z.string(),
  // support both username and email based accounts
  username: z.string().min(3).max(50).optional(),
  email: z.string().email().optional(),
  // common profile fields
  name: z.string().min(2).optional(),
  // password hash stored in DB
  passwordHash: z.string().optional(),
  // sometimes code refers to plain password (e.g. during flow) - keep optional for typing
  password: z.string().optional(),
  // MFA fields
  mfaEnabled: z.boolean().optional(),
  mfaSecret: z.string().optional(),
  // account flags
  isActive: z.boolean().optional(),
  emailVerified: z.boolean().optional(),
  emailVerificationToken: z.string().optional(),
  passwordResetToken: z.string().optional(),
  passwordResetExpires: z.number().optional(),
  createdAt: z.number(),
  updatedAt: z.number(),
    settings: z.record(z.string(), z.unknown()).optional(),
});

export const userAuthSchema = z.object({
  // allow login by email or username
  email: z.string().email().optional(),
  username: z.string().min(3).max(50).optional(),
  password: z.string().min(8),
});

export type UserAuth = z.infer<typeof userAuthSchema>;
export type User = z.infer<typeof userSchema>;

export const insertUserSchema = userSchema.omit({ id: true, createdAt: true, updatedAt: true });
export type InsertUser = z.infer<typeof insertUserSchema>;

// Backwards-compatible aliases for route imports
export const loginSchema = userAuthSchema;

export const apiKeySchema = z.object({
  id: z.string(),
  userId: z.string(),
  key: z.string(),
  name: z.string(),
  createdAt: z.number(),
  expiresAt: z.number().optional(),
  lastUsed: z.number().optional(),
  permissions: z.array(z.string()),
  isActive: z.boolean(),
});
export type ApiKey = z.infer<typeof apiKeySchema>;

export const insertApiKeySchema = apiKeySchema.omit({ id: true, createdAt: true });
export type InsertApiKey = z.infer<typeof insertApiKeySchema>;

export const loginRequestSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});
export type LoginRequest = z.infer<typeof loginRequestSchema>;

export const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  name: z.string().min(2),
});
export type RegisterRequest = z.infer<typeof registerSchema>;

// Notification schemas
export const notificationTypeSchema = z.enum(["trade_executed", "bot_status_change", "market_alert", "system"]);
export type NotificationType = z.infer<typeof notificationTypeSchema>;

export const notificationSchema = z.object({
  id: z.string(),
  userId: z.string(),
  type: notificationTypeSchema,
  title: z.string(),
  message: z.string(),
    data: z.record(z.string(), z.any()).optional(),
  read: z.boolean(),
  createdAt: z.number(),
});
export type Notification = z.infer<typeof notificationSchema>;

export const insertNotificationSchema = notificationSchema.omit({ id: true, createdAt: true });
export type InsertNotification = z.infer<typeof insertNotificationSchema>;

// Backtesting schemas
export const backtestConfigSchema = z.object({
  botId: z.string(),
  startDate: z.number(),
  endDate: z.number(),
  initialBalance: z.number(),
  commission: z.number(),
});
export type BacktestConfig = z.infer<typeof backtestConfigSchema>;

export const backtestResultSchema = z.object({
  id: z.string(),
  botId: z.string(),
  totalReturn: z.number(),
  sharpeRatio: z.number(),
  maxDrawdown: z.number(),
  winRate: z.number(),
  totalTrades: z.number(),
  profitFactor: z.number(),
  trades: z.array(tradeSchema),
  equityCurve: z.array(z.object({ timestamp: z.number(), balance: z.number() })),
  createdAt: z.number(),
});
export type BacktestResult = z.infer<typeof backtestResultSchema>;
