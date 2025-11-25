import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

// Arbitrage hooks

export const useArbitrageStatus = () => {
  return useQuery({
    queryKey: ["arbitrage", "status"],
    queryFn: async () => {
      const response = await apiRequest("GET", "/api/arbitrage/status");
      return response.json();
    },
    refetchInterval: 10000, // 10 seconds
  });
};

export const useArbitrageOpportunities = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["arbitrage", "opportunities"],
    queryFn: async () => {
      const response = await api.get("/arbitrage/opportunities");
      return response;
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 5000 : false, // 5 seconds
  });
};

export const useArbitrageStats = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["arbitrage", "stats"],
    queryFn: async () => {
      const response = await api.get("/arbitrage/stats");
      return response;
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 30000 : false, // 30 seconds
  });
};

export const useArbitrageHistory = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["arbitrage", "history"],
    queryFn: async () => {
      const response = await api.get("/arbitrage/history");
      return response;
    },
    enabled: isAuthenticated,
  });
};

export const useStartArbitrage = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async () => {
      const response = await apiRequest("POST", "/api/arbitrage/start", {});
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "status"] });
    },
    enabled: isAuthenticated,
  });
};

export const useStopArbitrage = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async () => {
      const response = await api.post("/arbitrage/stop", {});
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "status"] });
    },
    enabled: isAuthenticated,
  });
};

export const useExecuteArbitrage = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (opportunityId: string) => {
      const response = await api.post(`/arbitrage/execute/${opportunityId}`, {});
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "history"] });
      queryClient.invalidateQueries({ queryKey: ["arbitrage", "stats"] });
    },
    enabled: isAuthenticated,
  });
};

