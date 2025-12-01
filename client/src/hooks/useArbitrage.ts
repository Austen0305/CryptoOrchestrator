import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

// Arbitrage hooks

export const useArbitrageStatus = () => {
  return useQuery({
    queryKey: ["arbitrage", "status"],
    queryFn: async () => {
      return await apiRequest("/api/arbitrage/status", { method: "GET" });
    },
    refetchInterval: 10000, // 10 seconds
  });
};

export const useArbitrageOpportunities = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["arbitrage", "opportunities"],
    queryFn: async () => {
      return await apiRequest("/api/arbitrage/opportunities", { method: "GET" });
    },
    refetchInterval: isAuthenticated ? 5000 : false, // 5 seconds
  });
};

export const useArbitrageStats = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["arbitrage", "stats"],
    queryFn: async () => {
      return await apiRequest("/api/arbitrage/stats", { method: "GET" });
    },
    refetchInterval: isAuthenticated ? 30000 : false, // 30 seconds
  });
};

export const useArbitrageHistory = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["arbitrage", "history"],
    queryFn: async () => {
      return await apiRequest("/api/arbitrage/history", { method: "GET" });
    },
  });
};

export const useStartArbitrage = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async () => {
      return await apiRequest("/api/arbitrage/start", { method: "POST", body: {} });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "status"] });
    },
  });
};

export const useStopArbitrage = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async () => {
      return await apiRequest("/api/arbitrage/stop", { method: "POST", body: {} });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "status"] });
    },
  });
};

export const useExecuteArbitrage = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (opportunityId: string) => {
      return await apiRequest(`/api/arbitrage/execute/${opportunityId}`, { method: "POST", body: {} });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "history"] });
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "stats"] });
    },
  });
};

