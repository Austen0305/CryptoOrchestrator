/**
 * React hooks for strategy management
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

// Types
export interface StrategyTemplate {
  name: string;
  description: string;
  strategy_type: string;
  category: string;
  config: Record<string, any>;
  logic?: Record<string, any>;
}

export interface Strategy {
  id: string;
  user_id: number;
  name: string;
  description?: string;
  strategy_type: string;
  category: string;
  version: string;
  parent_strategy_id?: string;
  config: Record<string, any>;
  logic?: Record<string, any>;
  is_template: boolean;
  is_public: boolean;
  is_published: boolean;
  backtest_sharpe_ratio?: number;
  backtest_win_rate?: number;
  backtest_total_return?: number;
  backtest_max_drawdown?: number;
  usage_count: number;
  rating: number;
  rating_count: number;
  created_at: string;
  updated_at: string;
  published_at?: string;
}

export interface StrategyVersion {
  id: string;
  strategy_id: string;
  version: string;
  name: string;
  config: Record<string, any>;
  logic?: Record<string, any>;
  change_description?: string;
  created_at: string;
}

export interface BacktestRequest {
  strategy_id: string;
  start_date: string;
  end_date: string;
  initial_balance?: number;
  trading_pair?: string;
}

export interface BacktestResponse {
  strategy_id: string;
  sharpe_ratio: number;
  win_rate: number;
  total_return: number;
  max_drawdown: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
}

// Template hooks
export function useStrategyTemplates(category?: string) {
  const { isAuthenticated } = useAuth();
  
  return useQuery<StrategyTemplate[]>({
    queryKey: ["strategies", "templates", category],
    queryFn: async () => {
      const url = category 
        ? `/api/strategies/templates?category=${category}`
        : "/api/strategies/templates";
      return await apiRequest<StrategyTemplate[]>(url, { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

export function useStrategyTemplate(templateId: string) {
  const { isAuthenticated } = useAuth();
  
  return useQuery<StrategyTemplate>({
    queryKey: ["strategies", "templates", templateId],
    queryFn: async () => {
      return await apiRequest<StrategyTemplate>(`/api/strategies/templates/${templateId}`, {
        method: "GET",
      });
    },
    enabled: isAuthenticated && !!templateId,
  });
}

// Strategy hooks
export function useStrategies(includePublic = false) {
  const { isAuthenticated } = useAuth();
  
  return useQuery<Strategy[]>({
    queryKey: ["strategies", "list", includePublic],
    queryFn: async () => {
      const url = includePublic
        ? "/api/strategies?include_public=true"
        : "/api/strategies";
      return await apiRequest<Strategy[]>(url, { method: "GET" });
    },
    enabled: isAuthenticated,
  });
}

export function useStrategy(strategyId: string) {
  const { isAuthenticated } = useAuth();
  
  return useQuery<Strategy>({
    queryKey: ["strategies", strategyId],
    queryFn: async () => {
      return await apiRequest<Strategy>(`/api/strategies/${strategyId}`, {
        method: "GET",
      });
    },
    enabled: isAuthenticated && !!strategyId,
  });
}

export function useStrategyVersions(strategyId: string) {
  const { isAuthenticated } = useAuth();
  
  return useQuery<StrategyVersion[]>({
    queryKey: ["strategies", strategyId, "versions"],
    queryFn: async () => {
      return await apiRequest<StrategyVersion[]>(`/api/strategies/${strategyId}/versions`, {
        method: "GET",
      });
    },
    enabled: isAuthenticated && !!strategyId,
  });
}

// Strategy mutations
export function useCreateStrategy() {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (data: {
      name: string;
      description?: string;
      strategy_type: string;
      category: string;
      config: Record<string, any>;
      logic?: Record<string, any>;
      template_id?: string;
    }) => {
      return await apiRequest<Strategy>("/api/strategies", {
        method: "POST",
        body: data,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
    enabled: isAuthenticated,
  });
}

export function useUpdateStrategy() {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async ({
      strategyId,
      data,
    }: {
      strategyId: string;
      data: {
        name?: string;
        description?: string;
        config?: Record<string, any>;
        logic?: Record<string, any>;
      };
    }) => {
      return await apiRequest<Strategy>(`/api/strategies/${strategyId}`, {
        method: "PATCH",
        body: data,
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["strategies", variables.strategyId] });
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
    enabled: isAuthenticated,
  });
}

export function useDeleteStrategy() {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (strategyId: string) => {
      return await apiRequest(`/api/strategies/${strategyId}`, {
        method: "DELETE",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
    enabled: isAuthenticated,
  });
}

export function useBacktestStrategy() {
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (data: BacktestRequest) => {
      return await apiRequest<BacktestResponse>(
        `/api/strategies/${data.strategy_id}/backtest`,
        {
          method: "POST",
          body: data,
        }
      );
    },
    enabled: isAuthenticated,
  });
}

export function usePublishStrategy() {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (strategyId: string) => {
      return await apiRequest<Strategy>(`/api/strategies/${strategyId}/publish`, {
        method: "POST",
      });
    },
    onSuccess: (_, strategyId) => {
      queryClient.invalidateQueries({ queryKey: ["strategies", strategyId] });
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
    enabled: isAuthenticated,
  });
}
