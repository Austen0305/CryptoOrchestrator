import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { botApi, tradeApi, portfolioApi, marketApi, feeApi, statusApi, integrationsApi, runRiskScenario, activityApi, performanceApi, gridTradingApi, dcaTradingApi, infinityGridApi, trailingBotApi, futuresTradingApi } from "@/lib/api";
import type { BotConfig } from "../../../shared/schema";
import { useAuth } from "@/hooks/useAuth";
import { usePortfolioWebSocket } from "@/hooks/usePortfolioWebSocket";

// Bot hooks
export const useBots = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["bots"],
    queryFn: botApi.getBots,
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 10000 : false,
  });
};

export const useBot = (id: string) => {
  return useQuery({
    queryKey: ["bots", id],
    queryFn: () => botApi.getBot(id),
    enabled: !!id,
  });
};

export const useCreateBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: botApi.createBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bots"] });
    },
  });
};

export const useUpdateBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<BotConfig> }) =>
      botApi.updateBot(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bots"] });
    },
  });
};

export const useDeleteBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: botApi.deleteBot,
    onSuccess: () => {
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
  return useQuery({
    queryKey: ["bots", id, "model"],
    queryFn: () => botApi.getBotModel(id),
    enabled: !!id,
  });
};

export const useBotPerformance = (id: string) => {
  return useQuery({
    queryKey: ["bots", id, "performance"],
    queryFn: () => botApi.getBotPerformance(id),
    enabled: !!id,
  });
};

// Trade hooks
export const useTrades = (botId?: string, mode?: "paper" | "real" | "live") => {
  const { isAuthenticated } = useAuth();
  // Normalize "live" to "real" for backend compatibility
  const normalizedMode = mode === "live" ? "real" : mode;
  return useQuery({
    queryKey: ["trades", botId, normalizedMode],
    queryFn: () => tradeApi.getTrades(botId, normalizedMode),
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 5000 : false, // reduce polling and only when authenticated
  });
};

export const useCreateTrade = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: tradeApi.createTrade,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trades"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
};

// Portfolio hooks
export const usePortfolio = (mode: "paper" | "real" | "live" = "paper") => {
  const { isAuthenticated } = useAuth();
  // Normalize "live" to "real" for backward compatibility
  const normalizedMode = mode === "live" ? "real" : mode;
  
  // Use WebSocket for real-time updates if available
  const { portfolio: wsPortfolio, isConnected: wsConnected } = usePortfolioWebSocket(normalizedMode);
  
  const query = useQuery({
    queryKey: ["portfolio", normalizedMode],
    queryFn: () => portfolioApi.getPortfolio(normalizedMode),
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated && !wsConnected ? 10000 : false, // Poll only if WebSocket not connected
  });

  // Merge WebSocket data with query data (WebSocket takes precedence for real-time updates)
  const mergedPortfolio = wsPortfolio || query.data;

  return {
    ...query,
    data: mergedPortfolio,
    isRealTime: wsConnected,
  };
};

// Market hooks
export const useMarkets = () => {
  return useQuery({
    queryKey: ["markets"],
    queryFn: marketApi.getMarkets,
    refetchInterval: 10000, // Refetch every 10 seconds
  });
};

export const useOHLCV = (pair: string, timeframe = "1h", limit = 100) => {
  return useQuery({
    queryKey: ["ohlcv", pair, timeframe, limit],
    queryFn: () => marketApi.getOHLCV(pair, timeframe, limit),
    enabled: !!pair,
  });
};

export const useOrderBook = (pair: string) => {
  return useQuery({
    queryKey: ["orderbook", pair],
    queryFn: () => marketApi.getOrderBook(pair),
    enabled: !!pair,
    refetchInterval: 5000, // Refetch every 5 seconds
  });
};

// Fee hooks
export const useFees = (volumeUSD = 0) => {
  return useQuery({
    queryKey: ["fees", volumeUSD],
    queryFn: () => feeApi.getFees(volumeUSD),
  });
};

export const useCalculateFees = () => {
  return useMutation({
    mutationFn: feeApi.calculateFees,
  });
};

// Status hooks
export const useStatus = () => {
  // status can remain public; do not gate but slow polling
  return useQuery({
    queryKey: ["status"],
    queryFn: statusApi.getStatus,
    refetchInterval: 15000,
  });
};

// Integrations hooks
export const useIntegrationsStatus = () => {
  return useQuery({
    queryKey: ['integrations', 'status'],
    queryFn: () => integrationsApi.status(),
    refetchInterval: 5000,
  });
};

export const useStartIntegrations = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => integrationsApi.startAll(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integrations', 'status'] }),
  });
};

export const useStopIntegrations = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => integrationsApi.stopAll(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integrations', 'status'] }),
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
  return useQuery({
    queryKey: ["activity", "recent", limit],
    queryFn: () => activityApi.getRecentActivity(limit),
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 30000 : false, // 30 seconds
  });
};

// Performance hooks
export const usePerformanceSummary = (mode?: "paper" | "real" | "live") => {
  const { isAuthenticated } = useAuth();
  const normalizedMode = mode === "live" ? "real" : mode;
  return useQuery({
    queryKey: ["performance", "summary", normalizedMode],
    queryFn: () => performanceApi.getSummary(normalizedMode),
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 60000 : false, // 1 minute
  });
};

// Grid Trading hooks
export const useGridBots = (skip = 0, limit = 100) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["grid-bots", skip, limit],
    queryFn: () => gridTradingApi.getGridBots(skip, limit),
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 10000 : false,
  });
};

export const useGridBot = (id: string) => {
  return useQuery({
    queryKey: ["grid-bots", id],
    queryFn: () => gridTradingApi.getGridBot(id),
    enabled: !!id,
  });
};

export const useCreateGridBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gridTradingApi.createGridBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
  });
};

export const useStartGridBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gridTradingApi.startGridBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
  });
};

export const useStopGridBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gridTradingApi.stopGridBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
  });
};

export const useDeleteGridBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: gridTradingApi.deleteGridBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grid-bots"] });
    },
  });
};

// DCA Trading hooks
export const useDCABots = (skip = 0, limit = 100) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["dca-bots", skip, limit],
    queryFn: () => dcaTradingApi.getDCABots(skip, limit),
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 10000 : false,
  });
};

export const useDCABot = (id: string) => {
  return useQuery({
    queryKey: ["dca-bots", id],
    queryFn: () => dcaTradingApi.getDCABot(id),
    enabled: !!id,
  });
};

export const useCreateDCABot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: dcaTradingApi.createDCABot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
  });
};

export const useStartDCABot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: dcaTradingApi.startDCABot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
  });
};

export const useStopDCABot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: dcaTradingApi.stopDCABot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
  });
};

export const useDeleteDCABot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: dcaTradingApi.deleteDCABot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dca-bots"] });
    },
  });
};

// Infinity Grid hooks
export const useInfinityGrids = (skip = 0, limit = 100) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["infinity-grids", skip, limit],
    queryFn: () => infinityGridApi.getInfinityGrids(skip, limit),
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 10000 : false,
  });
};

export const useInfinityGrid = (id: string) => {
  return useQuery({
    queryKey: ["infinity-grids", id],
    queryFn: () => infinityGridApi.getInfinityGrid(id),
    enabled: !!id,
  });
};

export const useCreateInfinityGrid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: infinityGridApi.createInfinityGrid,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
  });
};

export const useStartInfinityGrid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: infinityGridApi.startInfinityGrid,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
  });
};

export const useStopInfinityGrid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: infinityGridApi.stopInfinityGrid,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
  });
};

export const useDeleteInfinityGrid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: infinityGridApi.deleteInfinityGrid,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["infinity-grids"] });
    },
  });
};

// Trailing Bot hooks
export const useTrailingBots = (skip = 0, limit = 100) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["trailing-bots", skip, limit],
    queryFn: () => trailingBotApi.getTrailingBots(skip, limit),
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 10000 : false,
  });
};

export const useTrailingBot = (id: string) => {
  return useQuery({
    queryKey: ["trailing-bots", id],
    queryFn: () => trailingBotApi.getTrailingBot(id),
    enabled: !!id,
  });
};

export const useCreateTrailingBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: trailingBotApi.createTrailingBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
  });
};

export const useStartTrailingBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: trailingBotApi.startTrailingBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
  });
};

export const useStopTrailingBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: trailingBotApi.stopTrailingBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
  });
};

export const useDeleteTrailingBot = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: trailingBotApi.deleteTrailingBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trailing-bots"] });
    },
  });
};

// Futures Trading hooks
export const useFuturesPositions = (skip = 0, limit = 100, openOnly = false) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["futures-positions", skip, limit, openOnly],
    queryFn: () => futuresTradingApi.getFuturesPositions(skip, limit, openOnly),
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 5000 : false, // More frequent for futures
  });
};

export const useFuturesPosition = (id: string) => {
  return useQuery({
    queryKey: ["futures-positions", id],
    queryFn: () => futuresTradingApi.getFuturesPosition(id),
    enabled: !!id,
    refetchInterval: 5000, // Frequent updates for P&L
  });
};

export const useCreateFuturesPosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: futuresTradingApi.createFuturesPosition,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["futures-positions"] });
    },
  });
};

export const useCloseFuturesPosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, closePrice }: { id: string; closePrice?: number }) =>
      futuresTradingApi.closeFuturesPosition(id, closePrice),
    onSuccess: () => {
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
