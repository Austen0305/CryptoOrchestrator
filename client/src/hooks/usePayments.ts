import { useCallback } from "react";
import { api } from "@/lib/apiClient";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import logger from "@/lib/logger";
import { useAuth } from "@/hooks/useAuth";

interface Plan {
  plan: string;
  name: string;
  price_monthly: number;
  price_yearly: number;
  stripe_price_id_monthly?: string;
  stripe_price_id_yearly?: string;
  features: string[];
  limits: {
    max_bots: number;
    max_strategies: number;
    max_backtests_per_month: number;
  };
}

interface Subscription {
  plan: string;
  status: string;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
  limits: Record<string, number>;
}

export interface PricingPlan {
  tier: string;
  amount: number; // Amount in cents
  amount_display: string; // Formatted display amount (e.g., "$49.00")
  currency: string;
  interval: string; // "month" or "year"
  features: string[];
}

export interface PricingInfo {
  pricing: {
    [tier: string]: PricingPlan;
  };
}

/**
 * Hook for fetching pricing information using React Query
 * Used by PricingPlans component
 */
export function usePricing() {
  const { isAuthenticated } = useAuth();
  return useQuery<PricingInfo>({
    queryKey: ['pricing'],
    queryFn: async () => {
      const { api } = await import("@/lib/apiClient");
      // apiClient.get<T>() returns T directly, not { data: T }
      const response = await api.get<{ pricing: Record<string, PricingPlan> }>("/billing/pricing");
      return response || { pricing: {} };
    },
    enabled: isAuthenticated,
    staleTime: 10 * 60 * 1000, // 10 minutes - pricing doesn't change often
    retry: 2,
  });
}

/**
 * Hook for payment operations (mutations)
 * Provides helper functions for Billing page
 * Note: Billing page uses React Query directly for queries
 */
export function usePayments() {
  const queryClient = useQueryClient();

  // Create checkout session mutation
  const createCheckoutMutation = useMutation({
    mutationFn: async ({ priceId, plan }: { priceId: string; plan: string }) => {
      const { api } = await import("@/lib/apiClient");
      // apiClient.post<T>() returns T directly, not { data: T }
      const response = await api.post<{ checkout_url: string; session_id: string }>("/billing/checkout", {
        price_id: priceId,
        plan,
      });
      return response;
    },
    onError: (error: Error) => {
      logger.error('Failed to create checkout session', { error });
      throw error;
    },
  });

  // Create portal session mutation
  const createPortalMutation = useMutation({
    mutationFn: async () => {
      const { api } = await import("@/lib/apiClient");
      // apiClient.post<T>() returns T directly, not { data: T }
      // api.post requires (endpoint, data, config?) - pass empty object for POST without body
      const response = await api.post<{ portal_url: string }>("/billing/portal", {});
      return response;
    },
    onError: (error: Error) => {
      logger.error('Failed to create portal session', { error });
      throw error;
    },
  });

  // Cancel subscription mutation
  const cancelSubscriptionMutation = useMutation({
    mutationFn: async (immediately: boolean = false) => {
      const { api } = await import("@/lib/apiClient");
      await api.post("/billing/cancel", { immediately });
      return true;
    },
    onSuccess: () => {
      // Invalidate subscription queries
      queryClient.invalidateQueries({ queryKey: ['billing-subscription'] });
    },
    onError: (error: Error) => {
      logger.error('Failed to cancel subscription', { error });
      throw error;
    },
  });

  // Helper functions for backward compatibility with Billing page
  const getPlans = useCallback(async (): Promise<Plan[]> => {
    const { api } = await import("@/lib/apiClient");
    // apiClient.get<T>() returns T directly, not { data: T }
    const response = await api.get<{ plans?: Plan[] }>("/billing/plans");
    return (response && 'plans' in response && Array.isArray(response.plans))
      ? response.plans
      : [];
  }, []);

  const getSubscription = useCallback(async (): Promise<Subscription | null> => {
    const { api } = await import("@/lib/apiClient");
    try {
      // apiClient.get<T>() returns T directly, not { data: T }
      const response = await api.get<Subscription>("/billing/subscription");
      return response || null;
    } catch (err) {
      // Return null instead of throwing for subscription (user might not have one)
      logger.error('Failed to get subscription', { error: err });
      return null;
    }
  }, []);

  const createCheckout = useCallback(
    async (priceId: string, plan: string): Promise<{ checkout_url: string; session_id: string } | null> => {
      const result = await createCheckoutMutation.mutateAsync({ priceId, plan });
      return result || null;
    },
    [createCheckoutMutation]
  );

  const createPortal = useCallback(async (): Promise<{ portal_url: string } | null> => {
    const result = await createPortalMutation.mutateAsync();
    return result || null;
  }, [createPortalMutation]);

  const cancelSubscription = useCallback(async (immediately = false): Promise<boolean> => {
    return await cancelSubscriptionMutation.mutateAsync(immediately);
  }, [cancelSubscriptionMutation]);

  return {
    loading: createCheckoutMutation.isPending || createPortalMutation.isPending || cancelSubscriptionMutation.isPending,
    error: createCheckoutMutation.error || createPortalMutation.error || cancelSubscriptionMutation.error,
    getPlans,
    getSubscription,
    createCheckout,
    createPortal,
    cancelSubscription,
  };
}
