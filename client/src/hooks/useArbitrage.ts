import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

// Arbitrage hooks

export const useArbitrageStatus = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["arbitrage", "status"],
    queryFn: async () => {
      return await apiRequest("/api/arbitrage/status", { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000, // 2 minutes for status data
    refetchInterval: isAuthenticated ? 10000 : false, // 10 seconds when authenticated
  });
};

export const useArbitrageOpportunities = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["arbitrage", "opportunities"],
    queryFn: async () => {
      return await apiRequest("/api/arbitrage/opportunities", { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for opportunities data
    refetchInterval: isAuthenticated ? 5000 : false, // 5 seconds when authenticated
  });
};

export const useArbitrageStats = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["arbitrage", "stats"],
    queryFn: async () => {
      return await apiRequest("/api/arbitrage/stats", { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for stats data
    refetchInterval: isAuthenticated ? 30000 : false, // 30 seconds when authenticated
  });
};

export const useArbitrageHistory = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["arbitrage", "history"],
    queryFn: async () => {
      return await apiRequest("/api/arbitrage/history", { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds for history data
  });
};

export const useStartArbitrage = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      return await apiRequest("/api/arbitrage/start", { method: "POST", body: {} });
    },
    // Optimistic update: immediately update UI before server confirms
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["arbitrage", "status"] });
      
      // Snapshot the previous value
      const previousStatus = queryClient.getQueryData(["arbitrage", "status"]);
      
      // Optimistically update status
      queryClient.setQueryData(["arbitrage", "status"], (old: any) =>
        old ? { ...old, running: true } : old
      );
      
      // Return a context object with the snapshotted value
      return { previousStatus };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "status"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousStatus) {
        queryClient.setQueryData(["arbitrage", "status"], context.previousStatus);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "status"] });
    },
  });
};

export const useStopArbitrage = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      return await apiRequest("/api/arbitrage/stop", { method: "POST", body: {} });
    },
    // Optimistic update: immediately update UI before server confirms
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["arbitrage", "status"] });
      
      // Snapshot the previous value
      const previousStatus = queryClient.getQueryData(["arbitrage", "status"]);
      
      // Optimistically update status
      queryClient.setQueryData(["arbitrage", "status"], (old: any) =>
        old ? { ...old, running: false } : old
      );
      
      // Return a context object with the snapshotted value
      return { previousStatus };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "status"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousStatus) {
        queryClient.setQueryData(["arbitrage", "status"], context.previousStatus);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "status"] });
    },
  });
};

export const useExecuteArbitrage = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (opportunityId: string) => {
      return await apiRequest(`/api/arbitrage/execute/${opportunityId}`, { method: "POST", body: {} });
    },
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (opportunityId) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["arbitrage", "opportunities"] });
      await queryClient.cancelQueries({ queryKey: ["arbitrage", "history"] });
      await queryClient.cancelQueries({ queryKey: ["arbitrage", "stats"] });
      
      // Snapshot the previous values
      const previousOpportunities = queryClient.getQueryData(["arbitrage", "opportunities"]);
      const previousHistory = queryClient.getQueryData(["arbitrage", "history"]);
      const previousStats = queryClient.getQueryData(["arbitrage", "stats"]);
      
      // Optimistically remove the opportunity
      if (previousOpportunities && Array.isArray(previousOpportunities)) {
        queryClient.setQueryData(["arbitrage", "opportunities"], (old: any) =>
          Array.isArray(old) ? old.filter((opp: any) => opp.id !== opportunityId) : old
        );
      }
      
      // Return a context object with the snapshotted values
      return { previousOpportunities, previousHistory, previousStats };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "history"] });
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "stats"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, opportunityId, context) => {
      if (context?.previousOpportunities) {
        queryClient.setQueryData(["arbitrage", "opportunities"], context.previousOpportunities);
      }
      if (context?.previousHistory) {
        queryClient.setQueryData(["arbitrage", "history"], context.previousHistory);
      }
      if (context?.previousStats) {
        queryClient.setQueryData(["arbitrage", "stats"], context.previousStats);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "history"] });
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "stats"] });
    },
  });
};

