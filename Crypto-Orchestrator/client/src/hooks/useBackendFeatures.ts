/**
 * React Hooks for Backend Features
 * Provides hooks for accessing new backend features
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  webhookApi,
  featureFlagsApi,
  errorRecoveryApi,
  analyticsApi,
  monitoringApi,
  securityAuditApi,
  loggingApi,
} from "@/lib/api";
import type {
  WebhookSubscription,
  FeatureFlag,
  CircuitBreakerState,
  AnalyticsSummary,
  Alert,
  SecurityAuditResult,
  LogEntry,
} from "@/lib/api";

/**
 * Hook to get all feature flags
 */
export function useFeatureFlags() {
  return useQuery({
    queryKey: ["feature-flags"],
    queryFn: () => featureFlagsApi.list(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to check if a specific feature is enabled
 */
export function useFeatureFlag(flagName: string) {
  return useQuery({
    queryKey: ["feature-flags", flagName],
    queryFn: () => featureFlagsApi.get(flagName),
    staleTime: 5 * 60 * 1000,
    enabled: !!flagName,
  });
}

/**
 * Hook to get webhook subscriptions
 */
export function useWebhooks(activeOnly: boolean = true) {
  return useQuery({
    queryKey: ["webhooks", activeOnly],
    queryFn: () => webhookApi.list(activeOnly),
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook to create webhook subscription
 */
export function useCreateWebhook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      url: string;
      events: string[];
      secret?: string;
      max_retries?: number;
      timeout?: number;
    }) => webhookApi.subscribe(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });
}

/**
 * Hook to get circuit breaker status
 */
export function useCircuitBreakers() {
  return useQuery({
    queryKey: ["circuit-breakers"],
    queryFn: () => errorRecoveryApi.getCircuitBreakers(),
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
}

/**
 * Hook to get API analytics
 */
export function useAnalytics() {
  return useQuery({
    queryKey: ["analytics"],
    queryFn: () => analyticsApi.getSummary(),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

/**
 * Hook to get monitoring alerts
 */
export function useAlerts(params?: {
  level?: string;
  resolved?: boolean;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["alerts", params],
    queryFn: () => monitoringApi.getAlerts(params),
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
}

/**
 * Hook to resolve an alert
 */
export function useResolveAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alertId: string) => monitoringApi.resolveAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });
}

/**
 * Hook to run security audit
 */
export function useSecurityAudit() {
  return useQuery({
    queryKey: ["security-audit"],
    queryFn: () => securityAuditApi.runFullAudit(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: false, // Only run on demand
  });
}

/**
 * Hook to get logs
 */
export function useLogs(params?: {
  level?: string;
  source?: string;
  start_time?: string;
  end_time?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["logs", params],
    queryFn: () => loggingApi.getLogs(params),
    staleTime: 5 * 1000, // 5 seconds
  });
}

/**
 * Hook to search logs
 */
export function useSearchLogs(query: string, limit: number = 100) {
  return useQuery({
    queryKey: ["logs", "search", query, limit],
    queryFn: () => loggingApi.search(query, limit),
    enabled: !!query && query.length > 0,
    staleTime: 5 * 1000,
  });
}

