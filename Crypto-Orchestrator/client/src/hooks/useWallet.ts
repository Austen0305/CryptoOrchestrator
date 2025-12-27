import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";
import { usePortfolioWebSocket } from "@/hooks/usePortfolioWebSocket";

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
  const { isAuthenticated } = useAuth();
  // Check WebSocket connection - wallet balance updates come via portfolio WebSocket
  const { isConnected: wsConnected } = usePortfolioWebSocket("paper");
  // Disable polling when WebSocket is connected
  const shouldPoll = isAuthenticated && !wsConnected;
  return useQuery({
    queryKey: ["wallet", "balance", currency],
    queryFn: async () => {
      return await apiRequest<WalletBalance>(`/api/wallet/balance?currency=${currency}`, { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds
    refetchInterval: shouldPoll ? 60000 : false, // Poll every 1 minute when authenticated and WebSocket not connected
  });
};

export const useWalletTransactions = (
  currency?: string,
  transactionType?: string,
  limit: number = 50
) => {
  const { isAuthenticated } = useAuth();
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
    enabled: isAuthenticated,
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
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (request) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["wallet"] });
      await queryClient.cancelQueries({ queryKey: ["portfolio"] });
      
      // Snapshot the previous values
      const previousWallet = queryClient.getQueryData(["wallet", "balance", request.currency || "USD"]);
      const previousPortfolio = queryClient.getQueryData(["portfolio"]);
      
      // Return a context object with the snapshotted values
      return { previousWallet, previousPortfolio };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, request, context) => {
      if (context?.previousWallet) {
        queryClient.setQueryData(["wallet", "balance", request.currency || "USD"], context.previousWallet);
      }
      if (context?.previousPortfolio) {
        queryClient.setQueryData(["portfolio"], context.previousPortfolio);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
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
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (request) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["wallet"] });
      await queryClient.cancelQueries({ queryKey: ["portfolio"] });
      
      // Snapshot the previous values
      const previousWallet = queryClient.getQueryData(["wallet", "balance", request.currency || "USD"]);
      const previousPortfolio = queryClient.getQueryData(["portfolio"]);
      
      // Return a context object with the snapshotted values
      return { previousWallet, previousPortfolio };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, request, context) => {
      if (context?.previousWallet) {
        queryClient.setQueryData(["wallet", "balance", request.currency || "USD"], context.previousWallet);
      }
      if (context?.previousPortfolio) {
        queryClient.setQueryData(["portfolio"], context.previousPortfolio);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
};

