import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

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
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["copy-trading", "followed"],
    queryFn: async () => {
      return await apiRequest("/api/copy-trading/followed", { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for followed traders data
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
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (request) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["copy-trading", "followed"] });
      
      // Snapshot the previous value
      const previousFollowed = queryClient.getQueryData(["copy-trading", "followed"]);
      
      // Return a context object with the snapshotted value
      return { previousFollowed };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["copy-trading"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, request, context) => {
      if (context?.previousFollowed) {
        queryClient.setQueryData(["copy-trading", "followed"], context.previousFollowed);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
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
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (traderId) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["copy-trading", "followed"] });
      
      // Snapshot the previous value
      const previousFollowed = queryClient.getQueryData(["copy-trading", "followed"]);
      
      // Optimistically remove the trader from the list
      if (previousFollowed && Array.isArray(previousFollowed)) {
        queryClient.setQueryData(["copy-trading", "followed"], (old: any) =>
          Array.isArray(old) ? old.filter((t: any) => t.trader_id !== traderId) : old
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousFollowed };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["copy-trading"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, traderId, context) => {
      if (context?.previousFollowed) {
        queryClient.setQueryData(["copy-trading", "followed"], context.previousFollowed);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
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
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (request) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["trades"] });
      await queryClient.cancelQueries({ queryKey: ["copy-trading"] });
      
      // Snapshot the previous values
      const previousTrades = queryClient.getQueryData(["trades"]);
      const previousCopyTrading = queryClient.getQueryData(["copy-trading"]);
      
      // Return a context object with the snapshotted values
      return { previousTrades, previousCopyTrading };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["copy-trading"] });
      queryClient.invalidateQueries({ queryKey: ["trades"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, request, context) => {
      if (context?.previousTrades) {
        queryClient.setQueryData(["trades"], context.previousTrades);
      }
      if (context?.previousCopyTrading) {
        queryClient.setQueryData(["copy-trading"], context.previousCopyTrading);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["copy-trading"] });
      queryClient.invalidateQueries({ queryKey: ["trades"] });
    },
  });
};

export const useCopyTradingStats = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["copy-trading", "stats"],
    queryFn: async () => {
      return await apiRequest("/api/copy-trading/stats", { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for stats data
  });
};

