import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

// Extended market hooks

export const useWatchlist = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["markets", "watchlist"],
    queryFn: async () => {
      const response = await apiRequest("GET", "/api/markets/watchlist");
      return response.json();
    },
    enabled: isAuthenticated,
  });
};

export const useFavorites = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["markets", "favorites"],
    queryFn: async () => {
      const response = await api.get("/markets/favorites");
      return response;
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
      const response = await api.get(`/markets/advanced/${pair}/analysis?indicators=${indicatorsQuery}`);
      return response;
    },
    enabled: isAuthenticated && !!pair,
    refetchInterval: isAuthenticated ? 60000 : false, // 1 minute
  });
};

export const useMarketDetails = (pair: string) => {
  return useQuery({
    queryKey: ["markets", "details", pair],
    queryFn: async () => {
      const response = await api.get(`/markets/${pair}/details`);
      return response;
    },
    enabled: !!pair,
  });
};

export const useMarketTickers = () => {
  return useQuery({
    queryKey: ["markets", "tickers"],
    queryFn: async () => {
      const response = await api.get("/markets/tickers");
      return response;
    },
    refetchInterval: 10000, // 10 seconds
  });
};

export const useMarketSummary = () => {
  return useQuery({
    queryKey: ["markets", "summary"],
    queryFn: async () => {
      const response = await api.get("/markets/summary");
      return response;
    },
    refetchInterval: 30000, // 30 seconds
  });
};

export const useSearchTradingPairs = (query: string) => {
  return useQuery({
    queryKey: ["markets", "search", query],
    queryFn: async () => {
      const response = await api.get(`/markets/trading-pairs/search?q=${encodeURIComponent(query)}`);
      return response;
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

