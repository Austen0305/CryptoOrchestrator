import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

// Extended market hooks

export const useWatchlist = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["markets", "watchlist"],
    queryFn: async () => {
      return await apiRequest("/api/markets/watchlist", { method: "GET" });
    },
    enabled: isAuthenticated,
  });
};

export const useFavorites = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["markets", "favorites"],
    queryFn: async () => {
      return await apiRequest("/api/markets/favorites", { method: "GET" });
    },
    enabled: isAuthenticated,
  });
};

export const useAdvancedMarketAnalysis = (pair: string, indicators: string[] = ["rsi", "macd", "bollinger"]) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["markets", "advanced", pair, indicators],
    queryFn: async () => {
      const indicatorsQuery = indicators.join(",");
      return await apiRequest(`/api/markets/advanced/${pair}/analysis?indicators=${indicatorsQuery}`, { method: "GET" });
    },
    enabled: isAuthenticated && !!pair,
    refetchInterval: isAuthenticated ? 60000 : false, // 1 minute
  });
};

export const useMarketDetails = (pair: string) => {
  return useQuery({
    queryKey: ["markets", "details", pair],
    queryFn: async () => {
      return await apiRequest(`/api/markets/${pair}/details`, { method: "GET" });
    },
    enabled: !!pair,
  });
};

export const useMarketTickers = () => {
  return useQuery({
    queryKey: ["markets", "tickers"],
    queryFn: async () => {
      return await apiRequest("/api/markets/tickers", { method: "GET" });
    },
    refetchInterval: 10000, // 10 seconds
  });
};

export const useMarketSummary = () => {
  return useQuery({
    queryKey: ["markets", "summary"],
    queryFn: async () => {
      return await apiRequest("/api/markets/summary", { method: "GET" });
    },
    refetchInterval: 30000, // 30 seconds
  });
};

export const useSearchTradingPairs = (query: string) => {
  return useQuery({
    queryKey: ["markets", "search", query],
    queryFn: async () => {
      return await apiRequest(`/api/markets/trading-pairs/search?q=${encodeURIComponent(query)}`, { method: "GET" });
    },
    enabled: !!query && query.length >= 2,
  });
};

export const useAddToWatchlist = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (pair: string) => {
      // In production, this would call the API endpoint
      // For now, we'll simulate it
      return { pair, added: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["markets", "watchlist"] });
    },
    enabled: isAuthenticated,
  });
};

export const useRemoveFromWatchlist = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (pair: string) => {
      // In production, this would call the API endpoint
      return { pair, removed: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["markets", "watchlist"] });
    },
    enabled: isAuthenticated,
  });
};

