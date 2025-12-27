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
    staleTime: 30000, // 30 seconds for watchlist data
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
    staleTime: 30000, // 30 seconds for favorites data
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
    staleTime: 30000, // 30 seconds for market analysis
    refetchInterval: isAuthenticated ? 60000 : false, // 1 minute when authenticated
  });
};

export const useMarketDetails = (pair: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["markets", "details", pair],
    queryFn: async () => {
      return await apiRequest(`/api/markets/${pair}/details`, { method: "GET" });
    },
    enabled: isAuthenticated && !!pair,
    staleTime: 30000, // 30 seconds for market data
  });
};

export const useMarketTickers = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["markets", "tickers"],
    queryFn: async () => {
      return await apiRequest("/api/markets/tickers", { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for market data
    refetchInterval: isAuthenticated ? 10000 : false, // 10 seconds when authenticated
  });
};

export const useMarketSummary = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["markets", "summary"],
    queryFn: async () => {
      return await apiRequest("/api/markets/summary", { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for market data
    refetchInterval: isAuthenticated ? 30000 : false, // 30 seconds when authenticated
  });
};

export const useSearchTradingPairs = (query: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["markets", "search", query],
    queryFn: async () => {
      return await apiRequest(`/api/markets/trading-pairs/search?q=${encodeURIComponent(query)}`, { method: "GET" });
    },
    enabled: isAuthenticated && !!query && query.length >= 2,
    staleTime: 30000, // 30 seconds for search results
  });
};

export const useAddToWatchlist = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (pair: string) => {
      // In production, this would call the API endpoint
      // For now, we'll simulate it
      return { pair, added: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["markets", "watchlist"] });
    },
  });
};

export const useRemoveFromWatchlist = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (pair: string) => {
      // In production, this would call the API endpoint
      return { pair, removed: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["markets", "watchlist"] });
    },
  });
};

