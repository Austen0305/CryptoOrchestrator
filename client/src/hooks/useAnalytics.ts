import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

// Create api object for useAnalytics hooks
const api = {
  get: async (url: string) => {
    return await apiRequest(url, { method: "GET" });
  },
};

// Analytics hooks for comprehensive trading analytics

export const useAnalyticsSummary = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: async () => {
      return await apiRequest("/api/analytics/summary", { method: "GET" });
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 30000 : false, // 30 seconds
  });
};

export const useAnalyticsPerformance = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "performance"],
    queryFn: async () => {
      const response = await api.get("/analytics/performance");
      return response;
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 60000 : false, // 1 minute
  });
};

export const useAnalyticsRisk = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "risk"],
    queryFn: async () => {
      const response = await api.get("/analytics/risk");
      return response;
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 30000 : false,
  });
};

export const useAnalyticsPnLChart = (days: number = 30) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "pnl-chart", days],
    queryFn: async () => {
      const response = await api.get(`/analytics/pnl-chart?days=${days}`);
      return response;
    },
    enabled: isAuthenticated,
  });
};

export const useAnalyticsWinRateChart = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "win-rate-chart"],
    queryFn: async () => {
      const response = await api.get("/analytics/win-rate-chart");
      return response;
    },
    enabled: isAuthenticated,
  });
};

export const useAnalyticsDrawdownChart = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "drawdown-chart"],
    queryFn: async () => {
      const response = await api.get("/analytics/drawdown-chart");
      return response;
    },
    enabled: isAuthenticated,
  });
};

export const useDashboardSummary = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "dashboard", "summary"],
    queryFn: async () => {
      const response = await api.get("/analytics/dashboard/summary");
      return response;
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 10000 : false, // 10 seconds
  });
};

export const useDashboardRealtime = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "dashboard", "realtime"],
    queryFn: async () => {
      const response = await api.get("/analytics/dashboard/realtime");
      return response;
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 5000 : false, // 5 seconds
  });
};

export const useDashboardKPIs = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "dashboard", "kpis"],
    queryFn: async () => {
      const response = await api.get("/analytics/dashboard/kpis");
      return response;
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 30000 : false,
  });
};

export const usePortfolioPerformanceChart = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "dashboard", "charts", "portfolio-performance"],
    queryFn: async () => {
      const response = await api.get("/analytics/dashboard/charts/portfolio-performance");
      return response;
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 60000 : false,
  });
};

export const useAssetAllocationChart = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "dashboard", "charts", "asset-allocation"],
    queryFn: async () => {
      const response = await api.get("/analytics/dashboard/charts/asset-allocation");
      return response;
    },
    enabled: isAuthenticated,
  });
};

export const useBotPerformanceComparison = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "dashboard", "charts", "bot-performance-comparison"],
    queryFn: async () => {
      const response = await api.get("/analytics/dashboard/charts/bot-performance-comparison");
      return response;
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 60000 : false,
  });
};

export const useTradeDistributionChart = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["analytics", "dashboard", "charts", "trade-distribution"],
    queryFn: async () => {
      const response = await api.get("/analytics/dashboard/charts/trade-distribution");
      return response;
    },
    enabled: isAuthenticated,
  });
};

