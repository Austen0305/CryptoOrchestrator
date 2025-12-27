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
  config: Record<string, unknown>;
  logic?: Record<string, unknown>;
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
  config: Record<string, unknown>;
  logic?: Record<string, unknown>;
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
  config: Record<string, unknown>;
  logic?: Record<string, unknown>;
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
    staleTime: 5 * 60 * 1000, // 5 minutes - templates don't change often
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
    staleTime: 5 * 60 * 1000, // 5 minutes - templates don't change often
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
    staleTime: 30000, // 30 seconds for strategy data
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
    staleTime: 30000, // 30 seconds for strategy data
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
    staleTime: 30000, // 30 seconds for version data
  });
}

// Strategy mutations
export function useCreateStrategy() {
  const queryClient = useQueryClient();
  
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
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (newStrategy) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["strategies"] });
      
      // Snapshot the previous value
      const previousStrategies = queryClient.getQueryData<Strategy[]>(["strategies", "list", false]);
      
      // Optimistically update to the new value
      if (previousStrategies) {
        const optimisticStrategy: Strategy = {
          id: `temp-${Date.now()}`,
          user_id: 0,
          name: newStrategy.name,
          description: newStrategy.description,
          strategy_type: newStrategy.strategy_type,
          category: newStrategy.category,
          version: "1.0.0",
          config: newStrategy.config,
          logic: newStrategy.logic,
          is_template: false,
          is_public: false,
          is_published: false,
          usage_count: 0,
          rating: 0,
          rating_count: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        queryClient.setQueryData<Strategy[]>(["strategies", "list", false], (old) => [
          ...(old || []),
          optimisticStrategy,
        ]);
      }
      
      // Return a context object with the snapshotted value
      return { previousStrategies };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousStrategies) {
        queryClient.setQueryData(["strategies", "list", false], context.previousStrategies);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
  });
}

export function useUpdateStrategy() {
  const queryClient = useQueryClient();
  
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
    // Optimistic update: immediately update UI before server confirms
    onMutate: async ({ strategyId, data }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["strategies", strategyId] });
      await queryClient.cancelQueries({ queryKey: ["strategies"] });
      
      // Snapshot the previous values
      const previousStrategy = queryClient.getQueryData<Strategy>(["strategies", strategyId]);
      const previousStrategies = queryClient.getQueryData<Strategy[]>(["strategies", "list", false]);
      
      // Optimistically update to the new value
      if (previousStrategy) {
        queryClient.setQueryData<Strategy>(["strategies", strategyId], (old) =>
          old ? { ...old, ...data, updated_at: new Date().toISOString() } : old
        );
      }
      if (previousStrategies) {
        queryClient.setQueryData<Strategy[]>(["strategies", "list", false], (old) =>
          old?.map((s) => (s.id === strategyId ? { ...s, ...data, updated_at: new Date().toISOString() } : s)) ?? []
        );
      }
      
      // Return a context object with the snapshotted values
      return { previousStrategy, previousStrategies };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["strategies", variables.strategyId] });
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      if (context?.previousStrategy) {
        queryClient.setQueryData(["strategies", variables.strategyId], context.previousStrategy);
      }
      if (context?.previousStrategies) {
        queryClient.setQueryData(["strategies", "list", false], context.previousStrategies);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: (_, variables) => {
      if (variables && typeof variables === 'object' && 'strategyId' in variables) {
        const strategyId = variables.strategyId as string;
        queryClient.invalidateQueries({ queryKey: ["strategies", strategyId] });
      }
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
  });
}

export function useDeleteStrategy() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (strategyId: string) => {
      return await apiRequest(`/api/strategies/${strategyId}`, {
        method: "DELETE",
      });
    },
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (strategyId) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["strategies"] });
      
      // Snapshot the previous value
      const previousStrategies = queryClient.getQueryData<Strategy[]>(["strategies", "list", false]);
      
      // Optimistically update to the new value (remove the strategy)
      if (previousStrategies) {
        queryClient.setQueryData<Strategy[]>(["strategies", "list", false], (old) =>
          old?.filter((s) => s.id !== strategyId) ?? []
        );
      }
      
      // Return a context object with the snapshotted value
      return { previousStrategies };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, strategyId, context) => {
      if (context?.previousStrategies) {
        queryClient.setQueryData(["strategies", "list", false], context.previousStrategies);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
  });
}

export function useBacktestStrategy() {
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
  });
}

export function usePublishStrategy() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (strategyId: string) => {
      return await apiRequest<Strategy>(`/api/strategies/${strategyId}/publish`, {
        method: "POST",
      });
    },
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (strategyId) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["strategies", strategyId] });
      await queryClient.cancelQueries({ queryKey: ["strategies"] });
      
      // Snapshot the previous values
      const previousStrategy = queryClient.getQueryData<Strategy>(["strategies", strategyId]);
      const previousStrategies = queryClient.getQueryData<Strategy[]>(["strategies", "list", false]);
      
      // Optimistically update to the new value
      if (previousStrategy) {
        queryClient.setQueryData<Strategy>(["strategies", strategyId], (old) =>
          old ? { ...old, is_published: true, published_at: new Date().toISOString() } : old
        );
      }
      if (previousStrategies) {
        queryClient.setQueryData<Strategy[]>(["strategies", "list", false], (old) =>
          old?.map((s) =>
            s.id === strategyId
              ? { ...s, is_published: true, published_at: new Date().toISOString() }
              : s
          ) ?? []
        );
      }
      
      // Return a context object with the snapshotted values
      return { previousStrategy, previousStrategies };
    },
    onSuccess: (_, strategyId) => {
      queryClient.invalidateQueries({ queryKey: ["strategies", strategyId] });
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, strategyId, context) => {
      if (context?.previousStrategy) {
        queryClient.setQueryData(["strategies", strategyId], context.previousStrategy);
      }
      if (context?.previousStrategies) {
        queryClient.setQueryData(["strategies", "list", false], context.previousStrategies);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: (_, strategyId) => {
      queryClient.invalidateQueries({ queryKey: ["strategies", strategyId] });
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
  });
}
