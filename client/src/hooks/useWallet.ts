import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";

export interface WalletBalance {
  wallet_id: number | null;
  currency: string;
  balance: number;
  available_balance: number;
  locked_balance: number;
  total_deposited: number;
  total_withdrawn: number;
  total_traded: number;
}

export interface WalletTransaction {
  id: number;
  type: string;
  status: string;
  amount: number;
  currency: string;
  fee: number;
  net_amount: number;
  description: string | null;
  created_at: string | null;
  processed_at: string | null;
}

export interface DepositRequest {
  amount: number;
  currency?: string;
  payment_method_id?: string;
  payment_method_type?: string;  // 'card', 'ach', 'bank_transfer'
  description?: string;
}

export interface WithdrawRequest {
  amount: number;
  currency?: string;
  destination?: string;
  description?: string;
}

export const useWallet = (currency: string = "USD") => {
  return useQuery({
    queryKey: ["wallet", "balance", currency],
    queryFn: async () => {
      return await apiRequest<WalletBalance>(`/api/wallet/balance?currency=${currency}`, { method: "GET" });
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // 1 minute
  });
};

export const useWalletTransactions = (
  currency?: string,
  transactionType?: string,
  limit: number = 50
) => {
  const params = new URLSearchParams();
  if (currency) params.append("currency", currency);
  if (transactionType) params.append("transaction_type", transactionType);
  params.append("limit", limit.toString());
  
  return useQuery({
    queryKey: ["wallet", "transactions", currency, transactionType, limit],
    queryFn: async () => {
      return await apiRequest<{ transactions: WalletTransaction[] }>(`/api/wallet/transactions?${params}`, {
        method: "GET"
      });
    },
    staleTime: 60000, // 1 minute
  });
};

export const useDeposit = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: DepositRequest) => {
      return await apiRequest("/api/wallet/deposit", {
        method: "POST",
        body: request,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
};

export const useWithdraw = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: WithdrawRequest) => {
      return await apiRequest("/api/wallet/withdraw", {
        method: "POST",
        body: request,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
};

