import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { botApi, tradeApi, portfolioApi, marketApi, feeApi, statusApi, integrationsApi, runRiskScenario, activityApi, performanceApi, gridTradingApi, dcaTradingApi, infinityGridApi, trailingBotApi, futuresTradingApi, walletApi, withdrawalApi, type WithdrawalStatusResponse } from "@/lib/api";
import type { BotConfig, Trade, Portfolio } from "../../../shared/schema";
import { useAuth } from "@/hooks/useAuth";
import { usePortfolioWebSocket } from "@/hooks/usePortfolioWebSocket";
import { normalizeTradingMode } from "@/lib/tradingUtils";

// Bot hooks
export const useBots = () => {
  const { isAuthenticated } = useAuth();
  const { isConnected: isPortfolioConnected } = usePortfolioWebSocket("paper");
  // Disable polling when WebSocket is connected (real-time updates)
  const shouldPoll = isAuthenticated && !isPortfolioConnected;
  return useQuery<BotConfig[]>({
    queryKey: ["bots"],
    queryFn: botApi.getBots,
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000, // 2min staleTime for bot status (optimized)
    refetchInterval: shouldPoll ? 10000 : false, // Poll every 10s when authenticated and WebSocket not connected
  });
};

export const useBot = (id: string) => {
  return useQuery<BotConfig>({
    queryKey: ["bots", id],
    queryFn: () => botApi.getBot(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2min staleTime for bot status (optimized)
  });
};

export const useCreateBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: botApi.createBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (newBot) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["bots"] });
      
      // Snapshot the previous value
      const previousBots = queryClient.getQueryData<BotConfig[]>(["bots"]);
      
      // Optimistically update to the new value
      if (previousBots) {
        const optimisticBot: BotConfig = {
          ...newBot,
          id: `temp-${Date.now()}`,
          status: "stopped" as const,
          createdAt: Date.now(),
          updatedAt: Date.now(),
          profitLoss: 0,
          winRate: 0,
          totalTrades: 0,
          successfulTrades: 0,
          failedTrades: 0,
        };
        queryClient.setQueryData<BotConfig[]>(["bots"], (old) => [
          ...(old || []),
          optimisticBot,
        ]);
      }
      
      // Return a context object with the snapshotted value
      return { previousBots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousBots) {
        queryClient.setQueryData(["bots"], context.previousBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["bots"] });
    },
  });
};

export const useUpdateBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<BotConfig> }) =>
      botApi.updateBot(id, updates),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async ({ id, updates }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["bots"] });
      await queryClient.cancelQueries({ queryKey: ["bots", id] });
      
      // Snapshot the previous values
      const previousBots = queryClient.getQueryData<BotConfig[]>(["bots"]);
      const previousBot = queryClient.getQueryData<BotConfig>(["bots", id]);
      
      // Optimistically update to the new value
      if (previousBots) {
        queryClient.setQueryData<BotConfig[]>(["bots"], (old) =>
          old?.map((bot) => (bot.id === id ? { ...bot, ...updates, updatedAt: Date.now() } : bot)) ?? []
        );
      }
      if (previousBot) {
        queryClient.setQueryData<BotConfig>(["bots", id], (old) =>
          old ? { ...old, ...updates, updatedAt: Date.now() } : old
        );
      }
      
      // Return a context object with the snapshotted values
      return { previousBots, previousBot };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousBots) {
        queryClient.setQueryData(["bots"], context.previousBots);
      }
      if (context?.previousBot) {
        queryClient.setQueryData(["bots", variables.id], context.previousBot);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["bots"] });
    },
  });
};

export const useDeleteBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: botApi.deleteBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["bots"] });
      await queryClient.cancelQueries({ queryKey: ["bots", botId] });
      
      // Snapshot the previous values
      const previousBots = queryClient.getQueryData<BotConfig[]>(["bots"]);
      const previousBot = queryClient.getQueryData<BotConfig>(["bots", botId]);
      
      // Optimistically update to the new value (remove the bot)
      if (previousBots) {
        queryClient.setQueryData<BotConfig[]>(["bots"], (old) => old?.filter((bot) => bot.id !== botId) ?? []);
      }
      
      // Return a context object with the snapshotted values
      return { previousBots, previousBot };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousBots) {
        queryClient.setQueryData(["bots"], context.previousBots);
      }
      if (context?.previousBot) {
        queryClient.setQueryData(["bots", botId], context.previousBot);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["bots"] });
    },
  });
};

export const useStartBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: botApi.startBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({ queryKey: ["bots"] });
      
      // Snapshot the previous value
      const previousBots = queryClient.getQueryData<BotConfig[]>(["bots"]);
      
      // Optimistically update to the new value
      if (previousBots) {
        queryClient.setQueryData<BotConfig[]>(["bots"], (old) =>
          old?.map((bot) =>
            bot.id === botId ? { ...bot, status: "running" as const } : bot
          ) ?? []
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousBots };
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousBots) {
        queryClient.setQueryData(["bots"], context.previousBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["bots"] });
      queryClient.invalidateQueries({ queryKey: ["status"] });
    },
  });
};

export const useStopBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: botApi.stopBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({ queryKey: ["bots"] });
      
      // Snapshot the previous value
      const previousBots = queryClient.getQueryData<BotConfig[]>(["bots"]);
      
      // Optimistically update to the new value
      if (previousBots) {
        queryClient.setQueryData<BotConfig[]>(["bots"], (old) =>
          old?.map((bot) =>
            bot.id === botId ? { ...bot, status: "stopped" as const } : bot
          ) ?? []
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousBots };
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousBots) {
        queryClient.setQueryData(["bots"], context.previousBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["bots"] });
      queryClient.invalidateQueries({ queryKey: ["status"] });
    },
  });
};

export const useBotModel = (id: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["bots", id, "model"],
    queryFn: () => botApi.getBotModel(id),
    enabled: isAuthenticated && !!id,
    staleTime: 30000, // 30 seconds for bot model data
  });
};

export const useBotPerformance = (id: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["bots", id, "performance"],
    queryFn: () => botApi.getBotPerformance(id),
    enabled: isAuthenticated && !!id,
    staleTime: 30000, // 30 seconds for performance data
  });
};

// Trade hooks
export const useTrades = (botId?: string, mode?: "paper" | "real" | "live") => {
  const { isAuthenticated } = useAuth();
  const normalizedMode = mode ? normalizeTradingMode(mode) : mode;
  // Check WebSocket connection for portfolio (trades are part of portfolio updates)
  const { isConnected: wsConnected } = usePortfolioWebSocket(normalizedMode || "paper");
  // Disable polling when WebSocket is connected (real-time updates)
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery<Trade[]>({
    queryKey: ["trades", botId, normalizedMode],
    queryFn: () => tradeApi.getTrades(botId, normalizedMode),
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for trade data
    refetchInterval: shouldPoll ? 5000 : false, // Poll every 5s when authenticated and WebSocket not connected
  });
};

export const useCreateTrade = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: tradeApi.createTrade,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (newTrade) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["trades"] });
      await queryClient.cancelQueries({ queryKey: ["portfolio"] });
      
      // Snapshot the previous values
      const previousTrades = queryClient.getQueryData(["trades"]);
      const previousPortfolio = queryClient.getQueryData(["portfolio"]);
      
      // Return a context object with the snapshotted values
      return { previousTrades, previousPortfolio };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trades"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousTrades) {
        queryClient.setQueryData(["trades"], context.previousTrades);
      }
      if (context?.previousPortfolio) {
        queryClient.setQueryData(["portfolio"], context.previousPortfolio);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["trades"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
};

// Portfolio hooks
export const usePortfolio = (mode: "paper" | "real" | "live" = "paper") => {
  const { isAuthenticated } = useAuth();
  const normalizedMode = normalizeTradingMode(mode);
  
  // Use WebSocket for real-time updates if available
  const { portfolio: wsPortfolio, isConnected: wsConnected } = usePortfolioWebSocket(normalizedMode);
  
  const query = useQuery<Portfolio>({
    queryKey: ["portfolio", normalizedMode],
    queryFn: () => portfolioApi.getPortfolio(normalizedMode),
    enabled: isAuthenticated,
    staleTime: 1 * 60 * 1000, // 1min staleTime for portfolio (optimized)
    refetchInterval: isAuthenticated && !wsConnected ? 10000 : false, // Poll only if WebSocket not connected
  });

  // Merge WebSocket data with query data (WebSocket takes precedence for real-time updates)
  const mergedPortfolio = (wsPortfolio as Portfolio | undefined) || query.data;

  return {
    ...query,
    data: mergedPortfolio,
    isRealTime: wsConnected,
  };
};

// Market hooks
export const useMarkets = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["markets"],
    queryFn: marketApi.getMarkets,
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for market data
    refetchInterval: isAuthenticated ? 10000 : false, // Refetch every 10 seconds when authenticated
  });
};

export const useOHLCV = (pair: string, timeframe = "1h", limit = 100) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["ohlcv", pair, timeframe, limit],
    queryFn: () => marketApi.getOHLCV(pair, timeframe, limit),
    enabled: isAuthenticated && !!pair,
    staleTime: 30 * 1000, // 30s staleTime for market data (optimized)
  });
};

export const useOrderBook = (pair: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["orderbook", pair],
    queryFn: () => marketApi.getOrderBook(pair),
    enabled: isAuthenticated && !!pair,
    staleTime: 30 * 1000, // 30s staleTime for market data (optimized)
    refetchInterval: isAuthenticated ? 5000 : false, // Refetch every 5 seconds when authenticated
  });
};

// Fee hooks
export const useFees = (volumeUSD = 0) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["fees", volumeUSD],
    queryFn: () => feeApi.getFees(volumeUSD),
    enabled: isAuthenticated,
    staleTime: 300000, // 5 minutes - fees don't change often
  });
};

export const useCalculateFees = () => {
  return useMutation({
    mutationFn: feeApi.calculateFees,
  });
};

// Status hooks
export const useStatus = () => {
  // Status can remain public; do not gate but slow polling
  return useQuery<{ status: string; timestamp: number; runningBots?: number }>({
    queryKey: ["status"],
    queryFn: statusApi.getStatus,
    staleTime: 30000, // 30 seconds for status data
    refetchInterval: 15000, // Poll every 15 seconds (public endpoint)
  });
};

// Integrations hooks
export const useIntegrationsStatus = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ['integrations', 'status'],
    queryFn: () => integrationsApi.status(),
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for integrations status
    refetchInterval: isAuthenticated ? 5000 : false, // Poll every 5 seconds when authenticated
  });
};

export const useStartIntegrations = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => integrationsApi.startAll(),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['integrations', 'status'] });
      
      // Snapshot the previous value
      const previousStatus = queryClient.getQueryData(['integrations', 'status']);
      
      // Return a context object with the snapshotted value
      return { previousStatus };
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integrations', 'status'] }),
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousStatus) {
        queryClient.setQueryData(['integrations', 'status'], context.previousStatus);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations', 'status'] });
    },
  });
};

export const useStopIntegrations = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => integrationsApi.stopAll(),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['integrations', 'status'] });
      
      // Snapshot the previous value
      const previousStatus = queryClient.getQueryData(['integrations', 'status']);
      
      // Return a context object with the snapshotted value
      return { previousStatus };
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integrations', 'status'] }),
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousStatus) {
        queryClient.setQueryData(['integrations', 'status'], context.previousStatus);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations', 'status'] });
    },
  });
};

// Risk Scenario hook (POST /api/risk-scenarios/simulate)
export const useRunRiskScenario = () => {
  return useMutation({
    mutationFn: runRiskScenario,
  });
};

// Activity hooks
export const useRecentActivity = (limit = 10) => {
  const { isAuthenticated } = useAuth();
  // Check WebSocket connection - activity updates come via WebSocket
  const { isConnected: wsConnected } = usePortfolioWebSocket("paper");
  // Disable polling when WebSocket is connected
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery({
    queryKey: ["activity", "recent", limit],
    queryFn: () => activityApi.getRecentActivity(limit),
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for activity data
    refetchInterval: shouldPoll ? 30000 : false, // Poll every 30s when authenticated and WebSocket not connected
  });
};

// Performance hooks
export const usePerformanceSummary = (mode?: "paper" | "real" | "live") => {
  const { isAuthenticated } = useAuth();
  const normalizedMode = mode ? normalizeTradingMode(mode) : mode;
  // Check WebSocket connection - performance updates come via portfolio WebSocket
  const { isConnected: wsConnected } = usePortfolioWebSocket(normalizedMode || "paper");
  // Disable polling when WebSocket is connected
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery({
    queryKey: ["performance", "summary", normalizedMode],
    queryFn: () => performanceApi.getSummary(normalizedMode),
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for performance data
    refetchInterval: shouldPoll ? 60000 : false, // Poll every 1 minute when authenticated and WebSocket not connected
  });
};

// Grid Trading hooks
export const useGridBots = (skip = 0, limit = 100) => {
  const { isAuthenticated } = useAuth();
  // Check WebSocket connection - bot status updates come via portfolio WebSocket
  const { isConnected: wsConnected } = usePortfolioWebSocket("paper");
  // Disable polling when WebSocket is connected
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery({
    queryKey: ["grid-bots", skip, limit],
    queryFn: () => gridTradingApi.getGridBots(skip, limit),
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for grid bots data
    refetchInterval: shouldPoll ? 10000 : false, // Poll every 10s when authenticated and WebSocket not connected
  });
};

export const useGridBot = (id: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["grid-bots", id],
    queryFn: () => gridTradingApi.getGridBot(id),
    enabled: isAuthenticated && !!id,
    staleTime: 30000, // 30 seconds for grid bot data
  });
};

export const useCreateGridBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gridTradingApi.createGridBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (newBot) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["grid-bots"] });
      
      // Snapshot the previous value
      const previousGridBots = queryClient.getQueryData(["grid-bots"]);
      
      // Return a context object with the snapshotted value
      return { previousGridBots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousGridBots) {
        queryClient.setQueryData(["grid-bots"], context.previousGridBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
  });
};

export const useStartGridBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gridTradingApi.startGridBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["grid-bots"] });
      
      // Snapshot the previous value
      const previousGridBots = queryClient.getQueryData(["grid-bots"]);
      
      // Optimistically update bot status
      if (previousGridBots && Array.isArray(previousGridBots)) {
        queryClient.setQueryData(["grid-bots"], (old: any) =>
          Array.isArray(old) ? old.map((bot: any) => (bot.id === botId ? { ...bot, status: "running" } : bot)) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousGridBots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousGridBots) {
        queryClient.setQueryData(["grid-bots"], context.previousGridBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
  });
};

export const useStopGridBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gridTradingApi.stopGridBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["grid-bots"] });
      
      // Snapshot the previous value
      const previousGridBots = queryClient.getQueryData(["grid-bots"]);
      
      // Optimistically update bot status
      if (previousGridBots && Array.isArray(previousGridBots)) {
        queryClient.setQueryData(["grid-bots"], (old: any) =>
          Array.isArray(old) ? old.map((bot: any) => (bot.id === botId ? { ...bot, status: "stopped" } : bot)) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousGridBots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousGridBots) {
        queryClient.setQueryData(["grid-bots"], context.previousGridBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
  });
};

export const useDeleteGridBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gridTradingApi.deleteGridBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["grid-bots"] });
      
      // Snapshot the previous value
      const previousGridBots = queryClient.getQueryData(["grid-bots"]);
      
      // Optimistically remove the bot
      if (previousGridBots && Array.isArray(previousGridBots)) {
        queryClient.setQueryData(["grid-bots"], (old: any) =>
          Array.isArray(old) ? old.filter((bot: any) => bot.id !== botId) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousGridBots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousGridBots) {
        queryClient.setQueryData(["grid-bots"], context.previousGridBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
  });
};

// DCA Trading hooks
export const useDCABots = (skip = 0, limit = 100) => {
  const { isAuthenticated } = useAuth();
  // Check WebSocket connection - bot status updates come via portfolio WebSocket
  const { isConnected: wsConnected } = usePortfolioWebSocket("paper");
  // Disable polling when WebSocket is connected
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery({
    queryKey: ["dca-bots", skip, limit],
    queryFn: () => dcaTradingApi.getDCABots(skip, limit),
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for DCA bots data
    refetchInterval: shouldPoll ? 10000 : false, // Poll every 10s when authenticated and WebSocket not connected
  });
};

export const useDCABot = (id: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["dca-bots", id],
    queryFn: () => dcaTradingApi.getDCABot(id),
    enabled: isAuthenticated && !!id,
    staleTime: 30000, // 30 seconds for DCA bot data
  });
};

export const useCreateDCABot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: dcaTradingApi.createDCABot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (newBot) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["dca-bots"] });
      
      // Snapshot the previous value
      const previousDCABots = queryClient.getQueryData(["dca-bots"]);
      
      // Return a context object with the snapshotted value
      return { previousDCABots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousDCABots) {
        queryClient.setQueryData(["dca-bots"], context.previousDCABots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
  });
};

export const useStartDCABot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: dcaTradingApi.startDCABot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["dca-bots"] });
      
      // Snapshot the previous value
      const previousDCABots = queryClient.getQueryData(["dca-bots"]);
      
      // Optimistically update bot status
      if (previousDCABots && Array.isArray(previousDCABots)) {
        queryClient.setQueryData(["dca-bots"], (old: any) =>
          Array.isArray(old) ? old.map((bot: any) => (bot.id === botId ? { ...bot, status: "running" } : bot)) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousDCABots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousDCABots) {
        queryClient.setQueryData(["dca-bots"], context.previousDCABots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
  });
};

export const useStopDCABot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: dcaTradingApi.stopDCABot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["dca-bots"] });
      
      // Snapshot the previous value
      const previousDCABots = queryClient.getQueryData(["dca-bots"]);
      
      // Optimistically update bot status
      if (previousDCABots && Array.isArray(previousDCABots)) {
        queryClient.setQueryData(["dca-bots"], (old: any) =>
          Array.isArray(old) ? old.map((bot: any) => (bot.id === botId ? { ...bot, status: "stopped" } : bot)) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousDCABots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousDCABots) {
        queryClient.setQueryData(["dca-bots"], context.previousDCABots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
  });
};

export const useDeleteDCABot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: dcaTradingApi.deleteDCABot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["dca-bots"] });
      
      // Snapshot the previous value
      const previousDCABots = queryClient.getQueryData(["dca-bots"]);
      
      // Optimistically remove the bot
      if (previousDCABots && Array.isArray(previousDCABots)) {
        queryClient.setQueryData(["dca-bots"], (old: any) =>
          Array.isArray(old) ? old.filter((bot: any) => bot.id !== botId) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousDCABots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousDCABots) {
        queryClient.setQueryData(["dca-bots"], context.previousDCABots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
  });
};

// Infinity Grid hooks
export const useInfinityGrids = (skip = 0, limit = 100) => {
  const { isAuthenticated } = useAuth();
  // Check WebSocket connection - bot status updates come via portfolio WebSocket
  const { isConnected: wsConnected } = usePortfolioWebSocket("paper");
  // Disable polling when WebSocket is connected
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery({
    queryKey: ["infinity-grids", skip, limit],
    queryFn: () => infinityGridApi.getInfinityGrids(skip, limit),
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for infinity grids data
    refetchInterval: shouldPoll ? 10000 : false, // Poll every 10s when authenticated and WebSocket not connected
  });
};

export const useInfinityGrid = (id: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["infinity-grids", id],
    queryFn: () => infinityGridApi.getInfinityGrid(id),
    enabled: isAuthenticated && !!id,
    staleTime: 30000, // 30 seconds for infinity grid data
  });
};

export const useCreateInfinityGrid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: infinityGridApi.createInfinityGrid,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (newGrid) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["infinity-grids"] });
      
      // Snapshot the previous value
      const previousGrids = queryClient.getQueryData(["infinity-grids"]);
      
      // Return a context object with the snapshotted value
      return { previousGrids };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousGrids) {
        queryClient.setQueryData(["infinity-grids"], context.previousGrids);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
  });
};

export const useStartInfinityGrid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: infinityGridApi.startInfinityGrid,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (gridId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["infinity-grids"] });
      
      // Snapshot the previous value
      const previousGrids = queryClient.getQueryData(["infinity-grids"]);
      
      // Optimistically update grid status
      if (previousGrids && Array.isArray(previousGrids)) {
        queryClient.setQueryData(["infinity-grids"], (old: any) =>
          Array.isArray(old) ? old.map((grid: any) => (grid.id === gridId ? { ...grid, status: "running" } : grid)) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousGrids };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, gridId, context) => {
      if (context?.previousGrids) {
        queryClient.setQueryData(["infinity-grids"], context.previousGrids);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
  });
};

export const useStopInfinityGrid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: infinityGridApi.stopInfinityGrid,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (gridId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["infinity-grids"] });
      
      // Snapshot the previous value
      const previousGrids = queryClient.getQueryData(["infinity-grids"]);
      
      // Optimistically update grid status
      if (previousGrids && Array.isArray(previousGrids)) {
        queryClient.setQueryData(["infinity-grids"], (old: any) =>
          Array.isArray(old) ? old.map((grid: any) => (grid.id === gridId ? { ...grid, status: "stopped" } : grid)) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousGrids };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, gridId, context) => {
      if (context?.previousGrids) {
        queryClient.setQueryData(["infinity-grids"], context.previousGrids);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
  });
};

export const useDeleteInfinityGrid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: infinityGridApi.deleteInfinityGrid,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (gridId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["infinity-grids"] });
      
      // Snapshot the previous value
      const previousGrids = queryClient.getQueryData(["infinity-grids"]);
      
      // Optimistically remove the grid
      if (previousGrids && Array.isArray(previousGrids)) {
        queryClient.setQueryData(["infinity-grids"], (old: any) =>
          Array.isArray(old) ? old.filter((grid: any) => grid.id !== gridId) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousGrids };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, gridId, context) => {
      if (context?.previousGrids) {
        queryClient.setQueryData(["infinity-grids"], context.previousGrids);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
  });
};

// Trailing Bot hooks
export const useTrailingBots = (skip = 0, limit = 100) => {
  const { isAuthenticated } = useAuth();
  // Check WebSocket connection - bot status updates come via portfolio WebSocket
  const { isConnected: wsConnected } = usePortfolioWebSocket("paper");
  // Disable polling when WebSocket is connected
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery({
    queryKey: ["trailing-bots", skip, limit],
    queryFn: () => trailingBotApi.getTrailingBots(skip, limit),
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for trailing bots data
    refetchInterval: shouldPoll ? 10000 : false, // Poll every 10s when authenticated and WebSocket not connected
  });
};

export const useTrailingBot = (id: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["trailing-bots", id],
    queryFn: () => trailingBotApi.getTrailingBot(id),
    enabled: isAuthenticated && !!id,
    staleTime: 30000, // 30 seconds for trailing bot data
  });
};

export const useCreateTrailingBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: trailingBotApi.createTrailingBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (newBot) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["trailing-bots"] });
      
      // Snapshot the previous value
      const previousTrailingBots = queryClient.getQueryData(["trailing-bots"]);
      
      // Return a context object with the snapshotted value
      return { previousTrailingBots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousTrailingBots) {
        queryClient.setQueryData(["trailing-bots"], context.previousTrailingBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
  });
};

export const useStartTrailingBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: trailingBotApi.startTrailingBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["trailing-bots"] });
      
      // Snapshot the previous value
      const previousTrailingBots = queryClient.getQueryData(["trailing-bots"]);
      
      // Optimistically update bot status
      if (previousTrailingBots && Array.isArray(previousTrailingBots)) {
        queryClient.setQueryData(["trailing-bots"], (old: any) =>
          Array.isArray(old) ? old.map((bot: any) => (bot.id === botId ? { ...bot, status: "running" } : bot)) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousTrailingBots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousTrailingBots) {
        queryClient.setQueryData(["trailing-bots"], context.previousTrailingBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
  });
};

export const useStopTrailingBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: trailingBotApi.stopTrailingBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["trailing-bots"] });
      
      // Snapshot the previous value
      const previousTrailingBots = queryClient.getQueryData(["trailing-bots"]);
      
      // Optimistically update bot status
      if (previousTrailingBots && Array.isArray(previousTrailingBots)) {
        queryClient.setQueryData(["trailing-bots"], (old: any) =>
          Array.isArray(old) ? old.map((bot: any) => (bot.id === botId ? { ...bot, status: "stopped" } : bot)) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousTrailingBots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousTrailingBots) {
        queryClient.setQueryData(["trailing-bots"], context.previousTrailingBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
  });
};

export const useDeleteTrailingBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: trailingBotApi.deleteTrailingBot,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (botId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["trailing-bots"] });
      
      // Snapshot the previous value
      const previousTrailingBots = queryClient.getQueryData(["trailing-bots"]);
      
      // Optimistically remove the bot
      if (previousTrailingBots && Array.isArray(previousTrailingBots)) {
        queryClient.setQueryData(["trailing-bots"], (old: any) =>
          Array.isArray(old) ? old.filter((bot: any) => bot.id !== botId) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousTrailingBots };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, botId, context) => {
      if (context?.previousTrailingBots) {
        queryClient.setQueryData(["trailing-bots"], context.previousTrailingBots);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
  });
};

// Futures Trading hooks
export const useFuturesPositions = (skip = 0, limit = 100, openOnly = false) => {
  const { isAuthenticated } = useAuth();
  // Check WebSocket connection - position updates come via portfolio WebSocket
  const { isConnected: wsConnected } = usePortfolioWebSocket("paper");
  // Disable polling when WebSocket is connected
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery({
    queryKey: ["futures-positions", skip, limit, openOnly],
    queryFn: () => futuresTradingApi.getFuturesPositions(skip, limit, openOnly),
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for futures positions data
    refetchInterval: shouldPoll ? 5000 : false, // Poll every 5s when authenticated and WebSocket not connected
  });
};

export const useFuturesPosition = (id: string) => {
  const { isAuthenticated } = useAuth();
  // Check WebSocket connection - position updates come via portfolio WebSocket
  const { isConnected: wsConnected } = usePortfolioWebSocket("paper");
  // Disable polling when WebSocket is connected
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery({
    queryKey: ["futures-positions", id],
    queryFn: () => futuresTradingApi.getFuturesPosition(id),
    enabled: isAuthenticated && !!id,
    staleTime: 30000, // 30 seconds for futures position data
    refetchInterval: shouldPoll ? 5000 : false, // Poll every 5s when authenticated and WebSocket not connected
  });
};

export const useCreateFuturesPosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: futuresTradingApi.createFuturesPosition,
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (newPosition) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["futures-positions"] });
      
      // Snapshot the previous value
      const previousPositions = queryClient.getQueryData(["futures-positions"]);
      
      // Return a context object with the snapshotted value
      return { previousPositions };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["futures-positions"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousPositions) {
        queryClient.setQueryData(["futures-positions"], context.previousPositions);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["futures-positions"] });
    },
  });
};

export const useCloseFuturesPosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, closePrice }: { id: string; closePrice?: number }) =>
      futuresTradingApi.closeFuturesPosition(id, closePrice),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async ({ id }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["futures-positions"] });
      await queryClient.cancelQueries({ queryKey: ["futures-positions", id] });
      
      // Snapshot the previous values
      const previousPositions = queryClient.getQueryData(["futures-positions"]);
      const previousPosition = queryClient.getQueryData(["futures-positions", id]);
      
      // Optimistically update position status
      if (previousPositions && Array.isArray(previousPositions)) {
        queryClient.setQueryData(["futures-positions"], (old: any) =>
          Array.isArray(old) ? old.filter((pos: any) => pos.id !== id) : old
        );
      }
      if (previousPosition) {
        queryClient.setQueryData(["futures-positions", id], (old: any) =>
          old ? { ...old, status: "closed" } : old
        );
      }
      
      // Return a context object with the snapshotted values
      return { previousPositions, previousPosition };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["futures-positions"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousPositions) {
        queryClient.setQueryData(["futures-positions"], context.previousPositions);
      }
      if (context?.previousPosition) {
        queryClient.setQueryData(["futures-positions", variables.id], context.previousPosition);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["futures-positions"] });
    },
  });
};

export const useUpdatePositionPnl = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: futuresTradingApi.updatePositionPnl,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["futures-positions", id] });
    },
  });
};

// Wallet hooks
export const useWallets = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["wallets"],
    queryFn: walletApi.getWallets,
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds
  });
};

export const useCreateCustodialWallet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (chainId: number) => walletApi.createCustodialWallet(chainId),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (chainId) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["wallets"] });
      
      // Snapshot the previous value
      const previousWallets = queryClient.getQueryData(["wallets"]);
      
      // Return a context object with the snapshotted value
      return { previousWallets };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, chainId, context) => {
      if (context?.previousWallets) {
        queryClient.setQueryData(["wallets"], context.previousWallets);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
    },
  });
};

export const useRegisterExternalWallet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { wallet_address: string; chain_id: number; label?: string }) =>
      walletApi.registerExternalWallet(data),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (data) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["wallets"] });
      
      // Snapshot the previous value
      const previousWallets = queryClient.getQueryData(["wallets"]);
      
      // Return a context object with the snapshotted value
      return { previousWallets };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, data, context) => {
      if (context?.previousWallets) {
        queryClient.setQueryData(["wallets"], context.previousWallets);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
    },
  });
};

export const useDepositAddress = (chainId: number) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["wallets", "deposit-address", chainId],
    queryFn: () => walletApi.getDepositAddress(chainId),
    enabled: isAuthenticated && !!chainId,
    staleTime: 300000, // 5 minutes (deposit addresses don't change often)
  });
};

export const useWalletBalance = (walletId: number, tokenAddress?: string) => {
  const { isAuthenticated } = useAuth();
  // Check WebSocket connection - wallet balance updates come via portfolio WebSocket
  const { isConnected: wsConnected } = usePortfolioWebSocket("paper");
  // Disable polling when WebSocket is connected
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery({
    queryKey: ["wallets", walletId, "balance", tokenAddress],
    queryFn: () => walletApi.getWalletBalance(walletId, tokenAddress),
    enabled: isAuthenticated && !!walletId,
    staleTime: 30000, // 30 seconds
    refetchInterval: shouldPoll ? 60000 : false, // Refresh every minute when authenticated and WebSocket not connected
  });
};

export const useRefreshWalletBalances = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => walletApi.refreshBalances(),
    onSuccess: () => {
      // Invalidate all wallet balance queries
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
    },
  });
};

export const useWalletTransactions = (walletId: number, limit: number = 50) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["wallets", walletId, "transactions", limit],
    queryFn: () => walletApi.getWalletTransactions(walletId, limit),
    enabled: isAuthenticated && !!walletId,
    staleTime: 60000, // 1 minute
  });
};

// Withdrawal hooks
export const useCreateWithdrawal = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      chain_id: number;
      to_address: string;
      amount: string;
      currency: string;
      mfa_token?: string;
    }) => withdrawalApi.createWithdrawal(data),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (data) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["wallets"] });
      await queryClient.cancelQueries({ queryKey: ["wallet"] });
      
      // Snapshot the previous values
      const previousWallets = queryClient.getQueryData(["wallets"]);
      const previousWallet = queryClient.getQueryData(["wallet", "balance", data.currency]);
      
      // Return a context object with the snapshotted values
      return { previousWallets, previousWallet };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, data, context) => {
      if (context?.previousWallets) {
        queryClient.setQueryData(["wallets"], context.previousWallets);
      }
      if (context?.previousWallet) {
        queryClient.setQueryData(["wallet", "balance", data.currency], context.previousWallet);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
  });
};

export const useWithdrawalStatus = (chainId: number, txHash: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery<WithdrawalStatusResponse>({
    queryKey: ["withdrawals", "status", chainId, txHash],
    queryFn: () => withdrawalApi.getWithdrawalStatus(chainId, txHash),
    enabled: isAuthenticated && !!chainId && !!txHash,
    staleTime: 10000, // 10 seconds for withdrawal status (frequently changing)
    refetchInterval: isAuthenticated ? 5000 : false, // Poll every 5 seconds for status updates when authenticated
  });
};
