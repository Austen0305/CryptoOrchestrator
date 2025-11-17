import { useState, useCallback } from "react";
import { apiClient } from "@/lib/apiClient";

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

export function usePayments() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getPlans = useCallback(async (): Promise<Plan[]> => {
    try {
      setLoading(true);
      setError(null);
      const { apiClient } = await import("@/lib/apiClient");
      const { apiClient } = await import("@/lib/apiClient");
      const response = await apiClient.get("/billing/plans");
      return response.data.plans || [];
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || "Failed to load plans";
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const getSubscription = useCallback(async (): Promise<Subscription | null> => {
    try {
      setLoading(true);
      setError(null);
      const { apiClient } = await import("@/lib/apiClient");
      const response = await apiClient.get("/billing/subscription");
      return response.data || null;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || "Failed to load subscription";
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const createCheckout = useCallback(
    async (priceId: string, plan: string): Promise<{ checkout_url: string; session_id: string } | null> => {
      try {
        setLoading(true);
        setError(null);
        const { apiClient } = await import("@/lib/apiClient");
      const response = await apiClient.post("/billing/checkout", {
          price_id: priceId,
          plan,
        });
        return response.data || null;
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || err.message || "Failed to create checkout session";
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const createPortal = useCallback(async (): Promise<{ portal_url: string } | null> => {
    try {
      setLoading(true);
      setError(null);
      const { apiClient } = await import("@/lib/apiClient");
      const response = await apiClient.post("/billing/portal");
      return response.data || null;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || "Failed to create portal session";
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const cancelSubscription = useCallback(async (immediately = false): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.post("/billing/cancel", null, {
        params: { immediately },
      });
      return true;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || "Failed to cancel subscription";
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    getPlans,
    getSubscription,
    createCheckout,
    createPortal,
    cancelSubscription,
  };
}
