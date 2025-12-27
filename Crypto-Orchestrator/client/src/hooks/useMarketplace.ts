import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

export interface Trader {
  id: number;
  user_id: number;
  username?: string;
  profile_description?: string;
  trading_strategy?: string;
  risk_level?: string;
  total_return: number;
  sharpe_ratio: number;
  win_rate: number;
  total_trades: number;
  follower_count: number;
  average_rating: number;
  total_ratings: number;
  subscription_fee?: number;
  performance_fee_percentage: number;
  curator_status: string;
  last_metrics_update?: string;
}

export interface MarketplaceTradersResponse {
  traders: Trader[];
  total: number;
  skip: number;
  limit: number;
}

export interface TraderProfile extends Trader {
  winning_trades: number;
  total_profit: number;
  max_drawdown: number;
  profit_factor: number;
}

export interface ApplySignalProviderRequest {
  profile_description?: string;
}

export interface RateTraderRequest {
  rating: number; // 1-5
  comment?: string;
}

export interface MarketplaceFilters {
  sort_by?: "total_return" | "sharpe_ratio" | "win_rate" | "follower_count" | "rating";
  min_rating?: number;
  min_win_rate?: number;
  min_sharpe?: number;
  skip?: number;
  limit?: number;
}

export const useMarketplaceTraders = (filters: MarketplaceFilters = {}) => {
  const { sort_by = "total_return", min_rating, min_win_rate, min_sharpe, skip = 0, limit = 20 } = filters;
  
  return useQuery<MarketplaceTradersResponse>({
    queryKey: ["marketplace", "traders", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append("skip", skip.toString());
      params.append("limit", limit.toString());
      params.append("sort_by", sort_by);
      if (min_rating !== undefined) params.append("min_rating", min_rating.toString());
      if (min_win_rate !== undefined) params.append("min_win_rate", min_win_rate.toString());
      if (min_sharpe !== undefined) params.append("min_sharpe", min_sharpe.toString());
      
      return await apiRequest(`/api/marketplace/traders?${params.toString()}`, { method: "GET" });
    },
    staleTime: 300000, // 5 minutes for marketplace data
  });
};

export const useTraderProfile = (traderId: number) => {
  return useQuery<TraderProfile>({
    queryKey: ["marketplace", "trader", traderId],
    queryFn: async () => {
      return await apiRequest(`/api/marketplace/traders/${traderId}`, { method: "GET" });
    },
    enabled: !!traderId,
    staleTime: 120000, // 2 minutes for trader profile
  });
};

export const useApplyAsSignalProvider = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: ApplySignalProviderRequest) => {
      return await apiRequest("/api/marketplace/apply", {
        method: "POST",
        body: request,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["marketplace"] });
    },
  });
};

export const useRateTrader = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ traderId, ...request }: { traderId: number } & RateTraderRequest) => {
      return await apiRequest(`/api/marketplace/traders/${traderId}/rate`, {
        method: "POST",
        body: request,
      });
    },
    onSuccess: (_, variables) => {
      // Invalidate trader profile and marketplace list
      queryClient.invalidateQueries({ queryKey: ["marketplace", "trader", variables.traderId] });
      queryClient.invalidateQueries({ queryKey: ["marketplace", "traders"] });
    },
  });
};

export const useFollowTrader = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ traderId, follow }: { traderId: number; follow: boolean }) => {
      const method = follow ? "POST" : "DELETE";
      return await apiRequest(`/api/marketplace/traders/${traderId}/follow`, {
        method,
      });
    },
    onSuccess: (_, variables) => {
      // Invalidate trader profile and marketplace list
      queryClient.invalidateQueries({ queryKey: ["marketplace", "trader", variables.traderId] });
      queryClient.invalidateQueries({ queryKey: ["marketplace", "traders"] });
    },
  });
};

export const useCalculatePayout = (signalProviderId: number, periodDays: number = 30) => {
  const { isAuthenticated } = useAuth();
  
  return useQuery({
    queryKey: ["marketplace", "payout", signalProviderId, periodDays],
    queryFn: async () => {
      return await apiRequest(
        `/api/marketplace/payouts/calculate?signal_provider_id=${signalProviderId}&period_days=${periodDays}`,
        { method: "GET" }
      );
    },
    enabled: isAuthenticated && !!signalProviderId,
    staleTime: 60000, // 1 minute for payout calculation
  });
};

export const useCreatePayout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ signalProviderId, periodDays = 30 }: { signalProviderId: number; periodDays?: number }) => {
      return await apiRequest(`/api/marketplace/payouts/create?signal_provider_id=${signalProviderId}&period_days=${periodDays}`, {
        method: "POST",
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["marketplace", "payout", variables.signalProviderId] });
    },
  });
};

// Analytics hooks

export interface MarketplaceOverview {
  copy_trading: {
    total_providers: number;
    approved_providers: number;
    pending_providers: number;
    total_ratings: number;
    average_rating: number;
    total_followers: number;
    total_payouts: number;
    total_payout_amount: number;
    platform_revenue: number;
  };
  indicators: {
    total_indicators: number;
    approved_indicators: number;
    pending_indicators: number;
    free_indicators: number;
    paid_indicators: number;
    total_purchases: number;
    total_revenue: number;
    platform_revenue: number;
    developer_revenue: number;
    total_ratings: number;
    average_rating: number;
    by_category: Record<string, number>;
  };
  timestamp: string;
}

export interface TopProvider {
  id: number;
  username?: string;
  total_return: number;
  sharpe_ratio: number;
  win_rate: number;
  follower_count: number;
  average_rating: number;
}

export interface TopIndicator {
  id: number;
  name: string;
  category: string;
  price: number;
  is_free: boolean;
  purchase_count: number;
  average_rating: number;
}

export interface RevenueTrend {
  date: string;
  platform_revenue: number;
  provider_payout?: number;
  total_revenue?: number;
  developer_revenue?: number;
  purchase_count?: number;
}

export interface DeveloperAnalytics {
  developer_id: number;
  total_indicators: number;
  total_purchases: number;
  total_revenue: number;
  developer_earnings: number;
  average_rating: number;
  indicators: Array<{
    id: number;
    name: string;
    purchases: number;
    revenue: number;
    developer_earnings: number;
    average_rating: number;
  }>;
}

export interface IndicatorAnalytics {
  indicator_id: number;
  name: string;
  purchases: number;
  total_revenue: number;
  developer_earnings: number;
  platform_fee: number;
  average_rating: number;
  total_ratings: number;
}

export interface ProviderAnalytics {
  provider_id: number;
  total_return: number;
  sharpe_ratio: number;
  win_rate: number;
  total_trades: number;
  follower_count: number;
  average_rating: number;
  total_ratings: number;
  total_payouts: number;
  total_earnings: number;
  recent_payouts: Array<{
    id: number;
    period_start: string;
    period_end: string;
    provider_payout: number;
    status: string;
  }>;
  recent_ratings: Array<{
    id: number;
    rating: number;
    comment?: string;
    created_at: string;
  }>;
}

// Admin analytics hooks
export const useMarketplaceOverview = () => {
  const { isAuthenticated } = useAuth();
  
  return useQuery<MarketplaceOverview>({
    queryKey: ["admin", "marketplace", "overview"],
    queryFn: async () => {
      return await apiRequest("/admin/marketplace/overview", { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 300000, // 5 minutes
  });
};

export const useTopProviders = (limit: number = 10, sortBy: string = "total_return") => {
  const { isAuthenticated } = useAuth();
  
  return useQuery<{ providers: TopProvider[]; limit: number; sort_by: string }>({
    queryKey: ["admin", "marketplace", "top-providers", limit, sortBy],
    queryFn: async () => {
      return await apiRequest(`/admin/marketplace/top-providers?limit=${limit}&sort_by=${sortBy}`, { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 300000, // 5 minutes
  });
};

export const useTopIndicators = (limit: number = 10, sortBy: string = "purchase_count") => {
  const { isAuthenticated } = useAuth();
  
  return useQuery<{ indicators: TopIndicator[]; limit: number; sort_by: string }>({
    queryKey: ["admin", "marketplace", "top-indicators", limit, sortBy],
    queryFn: async () => {
      return await apiRequest(`/admin/marketplace/top-indicators?limit=${limit}&sort_by=${sortBy}`, { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 300000, // 5 minutes
  });
};

// Analytics Threshold Types
export interface AnalyticsThreshold {
  id: number;
  threshold_type: string;
  metric: string;
  operator: string;
  threshold_value: number;
  context?: Record<string, any>;
  enabled: boolean;
  notification_channels?: Record<string, boolean>;
  cooldown_minutes: number;
  last_triggered_at?: string;
  name?: string;
  description?: string;
  created_at: string;
}

export interface CreateThresholdRequest {
  threshold_type: string;
  metric: string;
  operator: string;
  threshold_value: number;
  context?: Record<string, any>;
  enabled?: boolean;
  notification_channels?: Record<string, boolean>;
  cooldown_minutes?: number;
  name?: string;
  description?: string;
}

export interface UpdateThresholdRequest {
  enabled?: boolean;
  threshold_value?: number;
  operator?: string;
  notification_channels?: Record<string, boolean>;
  cooldown_minutes?: number;
  name?: string;
  description?: string;
}

// Analytics Threshold Hooks
export const useAnalyticsThresholds = (thresholdType?: string) => {
  const { isAuthenticated } = useAuth();
  
  return useQuery<AnalyticsThreshold[]>({
    queryKey: ["marketplace", "analytics", "thresholds", thresholdType],
    queryFn: async () => {
      const url = thresholdType
        ? `/api/marketplace/analytics/thresholds?threshold_type=${thresholdType}`
        : "/api/marketplace/analytics/thresholds";
      return await apiRequest(url, { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 60000, // 1 minute
  });
};

export const useAnalyticsThreshold = (thresholdId: number) => {
  const { isAuthenticated } = useAuth();
  
  return useQuery<AnalyticsThreshold>({
    queryKey: ["marketplace", "analytics", "thresholds", thresholdId],
    queryFn: async () => {
      return await apiRequest(`/api/marketplace/analytics/thresholds/${thresholdId}`, { method: "GET" });
    },
    enabled: isAuthenticated && !!thresholdId,
    staleTime: 60000,
  });
};

export const useCreateAnalyticsThreshold = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: CreateThresholdRequest) => {
      return await apiRequest("/api/marketplace/analytics/thresholds", {
        method: "POST",
        body: request,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["marketplace", "analytics", "thresholds"] });
    },
  });
};

export const useUpdateAnalyticsThreshold = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ thresholdId, ...request }: { thresholdId: number } & UpdateThresholdRequest) => {
      return await apiRequest(`/api/marketplace/analytics/thresholds/${thresholdId}`, {
        method: "PUT",
        body: request,
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["marketplace", "analytics", "thresholds"] });
      queryClient.invalidateQueries({ queryKey: ["marketplace", "analytics", "thresholds", variables.thresholdId] });
    },
  });
};

export const useDeleteAnalyticsThreshold = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (thresholdId: number) => {
      return await apiRequest(`/api/marketplace/analytics/thresholds/${thresholdId}`, {
        method: "DELETE",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["marketplace", "analytics", "thresholds"] });
    },
  });
};

export const useTestAnalyticsThreshold = () => {
  return useMutation({
    mutationFn: async (thresholdId: number) => {
      return await apiRequest(`/api/marketplace/analytics/thresholds/${thresholdId}/test`, {
        method: "POST",
      });
    },
  });
};

export const useRevenueTrends = (days: number = 30) => {
  const { isAuthenticated } = useAuth();
  
  return useQuery<{
    copy_trading: RevenueTrend[];
    indicators: RevenueTrend[];
    period_days: number;
  }>({
    queryKey: ["admin", "marketplace", "revenue-trends", days],
    queryFn: async () => {
      return await apiRequest(`/admin/marketplace/revenue-trends?days=${days}`, { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 600000, // 10 minutes
  });
};

// Developer analytics hooks
export const useDeveloperAnalytics = () => {
  const { isAuthenticated } = useAuth();
  
  return useQuery<DeveloperAnalytics>({
    queryKey: ["indicators", "analytics", "developer"],
    queryFn: async () => {
      return await apiRequest("/api/indicators/analytics/developer", { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 300000, // 5 minutes
  });
};

export const useIndicatorAnalytics = (indicatorId: number) => {
  const { isAuthenticated } = useAuth();
  
  return useQuery<IndicatorAnalytics>({
    queryKey: ["indicators", "analytics", indicatorId],
    queryFn: async () => {
      return await apiRequest(`/api/indicators/analytics/indicator/${indicatorId}`, { method: "GET" });
    },
    enabled: isAuthenticated && !!indicatorId,
    staleTime: 300000, // 5 minutes
  });
};

// Provider analytics hooks
export const useProviderAnalytics = (providerId: number) => {
  const { isAuthenticated } = useAuth();
  
  return useQuery<ProviderAnalytics>({
    queryKey: ["marketplace", "analytics", "provider", providerId],
    queryFn: async () => {
      return await apiRequest(`/api/marketplace/analytics/provider/${providerId}`, { method: "GET" });
    },
    enabled: isAuthenticated && !!providerId,
    staleTime: 300000, // 5 minutes
  });
};
