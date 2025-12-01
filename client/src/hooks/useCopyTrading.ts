import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";

export interface FollowTraderRequest {
  trader_id: number;
  allocation_percentage?: number;
  max_position_size?: number;
}

export interface CopyTradeRequest {
  trader_id: number;
  original_trade_id: string;
  allocation_percentage?: number;
}

export const useFollowedTraders = () => {
  return useQuery({
    queryKey: ["copy-trading", "followed"],
    queryFn: async () => {
      return await apiRequest("/api/copy-trading/followed", { method: "GET" });
    },
  });
};

export const useFollowTrader = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: FollowTraderRequest) => {
      return await apiRequest("/api/copy-trading/follow", {
        method: "POST",
        body: request,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["copy-trading"] });
    },
  });
};

export const useUnfollowTrader = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (traderId: number) => {
      return await apiRequest(`/api/copy-trading/follow/${traderId}`, { method: "DELETE" });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["copy-trading"] });
    },
  });
};

export const useCopyTrade = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: CopyTradeRequest) => {
      return await apiRequest("/api/copy-trading/copy", {
        method: "POST",
        body: request,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["copy-trading"] });
      queryClient.invalidateQueries({ queryKey: ["trades"] });
    },
  });
};

export const useCopyTradingStats = () => {
  return useQuery({
    queryKey: ["copy-trading", "stats"],
    queryFn: async () => {
      return await apiRequest("/api/copy-trading/stats", { method: "GET" });
    },
  });
};

