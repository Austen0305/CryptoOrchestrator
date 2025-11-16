/**
 * React hooks for payment processing
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

// Types
export interface Subscription {
  id: string;
  status: string;
  tier: string;
  customer: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
}

export interface PricingInfo {
  tier: string;
  amount: number;
  amount_display: string;
  currency: string;
  interval: string;
  features: string[];
}

export interface CreateSubscriptionRequest {
  tier: string;
  payment_method_id?: string;
  email: string;
}

export interface PaymentIntent {
  id: string;
  client_secret: string;
  amount: number;
  currency: string;
  status: string;
}

// Hooks
export function usePricing() {
  return useQuery<{ pricing: Record<string, PricingInfo> }>({
    queryKey: ["payments", "pricing"],
    queryFn: async () => {
      return await apiRequest<{ pricing: Record<string, PricingInfo> }>("/api/payments/pricing", {
        method: "GET",
      });
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

export function useSubscription(subscriptionId: string) {
  const { isAuthenticated } = useAuth();
  
  return useQuery<Subscription>({
    queryKey: ["payments", "subscriptions", subscriptionId],
    queryFn: async () => {
      return await apiRequest<Subscription>(`/api/payments/subscriptions/${subscriptionId}`, {
        method: "GET",
      });
    },
    enabled: isAuthenticated && !!subscriptionId,
  });
}

export function useCreateSubscription() {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (data: CreateSubscriptionRequest) => {
      return await apiRequest<Subscription>("/api/payments/subscriptions", {
        method: "POST",
        body: data,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payments"] });
    },
    enabled: isAuthenticated,
  });
}

export function useUpdateSubscription() {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async ({
      subscriptionId,
      newTier,
    }: {
      subscriptionId: string;
      newTier: string;
    }) => {
      return await apiRequest<Subscription>(`/api/payments/subscriptions/${subscriptionId}`, {
        method: "PATCH",
        body: { new_tier: newTier },
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["payments", "subscriptions", variables.subscriptionId] });
      queryClient.invalidateQueries({ queryKey: ["payments"] });
    },
    enabled: isAuthenticated,
  });
}

export function useCancelSubscription() {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async ({
      subscriptionId,
      cancelImmediately = false,
    }: {
      subscriptionId: string;
      cancelImmediately?: boolean;
    }) => {
      return await apiRequest<Subscription>(
        `/api/payments/subscriptions/${subscriptionId}?cancel_immediately=${cancelImmediately}`,
        {
          method: "DELETE",
        }
      );
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["payments", "subscriptions", variables.subscriptionId] });
      queryClient.invalidateQueries({ queryKey: ["payments"] });
    },
    enabled: isAuthenticated,
  });
}

export function useCreatePaymentIntent() {
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (data: { amount: number; currency?: string; metadata?: Record<string, any> }) => {
      return await apiRequest<PaymentIntent>("/api/payments/payment-intents", {
        method: "POST",
        body: data,
      });
    },
    enabled: isAuthenticated,
  });
}
