/**
 * React Query hooks for tax reporting
 */

import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

export interface TaxSummary {
  symbol?: string;
  start_date?: string;
  end_date?: string;
  total_events: number;
  short_term: {
    gains: number;
    losses: number;
    net: number;
  };
  long_term: {
    gains: number;
    losses: number;
    net: number;
  };
  total_proceeds: number;
  total_cost_basis: number;
  net_gain_loss: number;
  wash_sales: {
    count: number;
    total_adjustment: number;
  };
}

export interface Form8949 {
  tax_year: number;
  user_id: number;
  part_i: {
    title: string;
    rows: Array<{
      description: string;
      date_acquired: string;
      date_sold: string;
      proceeds: number;
      cost_basis: number;
      code: string;
      adjustment_amount: number;
      gain_loss: number;
      is_long_term: boolean;
    }>;
    totals: {
      total_proceeds: number;
      total_cost_basis: number;
      total_adjustments: number;
      total_gain_loss: number;
      row_count: number;
    };
  };
  part_ii: {
    title: string;
    rows: Array<{
      description: string;
      date_acquired: string;
      date_sold: string;
      proceeds: number;
      cost_basis: number;
      code: string;
      adjustment_amount: number;
      gain_loss: number;
      is_long_term: boolean;
    }>;
    totals: {
      total_proceeds: number;
      total_cost_basis: number;
      total_adjustments: number;
      total_gain_loss: number;
      row_count: number;
    };
  };
  summary: TaxSummary;
  generated_at: string;
}

export interface TaxLossHarvesting {
  symbol: string;
  opportunities: Array<{
    purchase_date: string;
    purchase_price: number;
    quantity: number;
    current_price: number;
    current_value: number;
    cost_basis: number;
    unrealized_loss: number;
    loss_percent: number;
    holding_period_days: number;
  }>;
}

/**
 * Hook to fetch tax summary
 */
export const useTaxSummary = (
  symbol?: string,
  startDate?: Date,
  endDate?: Date
) => {
  const { isAuthenticated } = useAuth();

  return useQuery<TaxSummary>({
    queryKey: ["tax-summary", symbol, startDate, endDate],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (symbol) params.append("symbol", symbol);
      if (startDate) params.append("start_date", startDate.toISOString());
      if (endDate) params.append("end_date", endDate.toISOString());
      const query = params.toString() ? `?${params.toString()}` : "";
      return await apiRequest(`/api/tax/summary${query}`, { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 60000, // 1 minute
  });
};

/**
 * Hook to fetch Form 8949
 */
export const useForm8949 = (taxYear: number, method: string = "fifo") => {
  const { isAuthenticated } = useAuth();

  return useQuery<Form8949>({
    queryKey: ["form-8949", taxYear, method],
    queryFn: async () => {
      return await apiRequest(
        `/api/tax/form-8949?tax_year=${taxYear}&method=${method}`,
        { method: "GET" }
      );
    },
    enabled: isAuthenticated && !!taxYear,
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook to fetch tax-loss harvesting opportunities
 */
export const useTaxLossHarvesting = (
  symbol: string,
  currentPrice: number,
  thresholdPercent: number = 0.1
) => {
  const { isAuthenticated } = useAuth();

  return useQuery<TaxLossHarvesting>({
    queryKey: ["tax-loss-harvesting", symbol, currentPrice, thresholdPercent],
    queryFn: async () => {
      return await apiRequest(
        `/api/tax/loss-harvesting/${symbol}?current_price=${currentPrice}&threshold_percent=${thresholdPercent}`,
        { method: "GET" }
      );
    },
    enabled: isAuthenticated && !!symbol && currentPrice > 0,
    staleTime: 300000, // 5 minutes
  });
};
