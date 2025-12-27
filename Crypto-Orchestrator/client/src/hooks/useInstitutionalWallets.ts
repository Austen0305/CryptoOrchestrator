/**
 * React Query hooks for institutional wallet management
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

export interface InstitutionalWallet {
  id: number;
  user_id: number;
  wallet_type: string;
  wallet_address?: string;
  chain_id: number;
  multisig_type?: string;
  required_signatures: number;
  total_signers: number;
  status: string;
  label?: string;
  description?: string;
  balance?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CreateInstitutionalWalletRequest {
  wallet_type: string;
  chain_id?: number;
  multisig_type?: string;
  required_signatures?: number;
  total_signers?: number;
  signer_user_ids?: number[];
  label?: string;
  description?: string;
  unlock_time?: string;
  config?: Record<string, any>;
}

export interface PendingTransaction {
  id: number;
  wallet_id: number;
  transaction_type: string;
  to_address?: string;
  amount?: number;
  currency?: string;
  status: string;
  signatures: Record<string, any>;
  required_signatures: number;
  signature_count: number;
  expires_at?: string;
  description?: string;
  created_at: string;
}

/**
 * Hook to fetch institutional wallets
 */
export const useInstitutionalWallets = (
  walletType?: string,
  status?: string
) => {
  const { isAuthenticated } = useAuth();

  return useQuery<InstitutionalWallet[]>({
    queryKey: ["institutional-wallets", walletType, status],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (walletType) params.append("wallet_type", walletType);
      if (status) params.append("status", status);
      const query = params.toString() ? `?${params.toString()}` : "";
      return await apiRequest(`/api/institutional-wallets${query}`, { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Hook to fetch a single institutional wallet
 */
export const useInstitutionalWallet = (walletId: number) => {
  const { isAuthenticated } = useAuth();

  return useQuery<InstitutionalWallet>({
    queryKey: ["institutional-wallets", walletId],
    queryFn: async () => {
      return await apiRequest(`/api/institutional-wallets/${walletId}`, { method: "GET" });
    },
    enabled: isAuthenticated && !!walletId,
    staleTime: 30000,
  });
};

/**
 * Hook to create an institutional wallet
 */
export const useCreateInstitutionalWallet = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: CreateInstitutionalWalletRequest) => {
      return await apiRequest("/api/institutional-wallets", {
        method: "POST",
        body: request,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["institutional-wallets"] });
    },
  });
};

/**
 * Hook to add a signer to a wallet
 */
export const useAddSigner = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      walletId,
      signerUserId,
      role,
    }: {
      walletId: number;
      signerUserId: number;
      role: string;
    }) => {
      return await apiRequest(`/api/institutional-wallets/${walletId}/signers`, {
        method: "POST",
        body: { signer_user_id: signerUserId, role },
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["institutional-wallets"] });
      queryClient.invalidateQueries({
        queryKey: ["institutional-wallets", variables.walletId],
      });
    },
  });
};

/**
 * Hook to remove a signer from a wallet
 */
export const useRemoveSigner = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      walletId,
      signerUserId,
    }: {
      walletId: number;
      signerUserId: number;
    }) => {
      return await apiRequest(
        `/api/institutional-wallets/${walletId}/signers/${signerUserId}`,
        {
          method: "DELETE",
        }
      );
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["institutional-wallets"] });
      queryClient.invalidateQueries({
        queryKey: ["institutional-wallets", variables.walletId],
      });
    },
  });
};

/**
 * Hook to fetch pending transactions for a wallet
 */
export const usePendingTransactions = (walletId: number, status?: string) => {
  const { isAuthenticated } = useAuth();

  return useQuery<PendingTransaction[]>({
    queryKey: ["institutional-wallets", walletId, "transactions", status],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.append("status", status);
      const query = params.toString() ? `?${params.toString()}` : "";
      return await apiRequest(
        `/api/institutional-wallets/${walletId}/transactions${query}`,
        { method: "GET" }
      );
    },
    enabled: isAuthenticated && !!walletId,
    staleTime: 10000, // 10 seconds (transactions change frequently)
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

/**
 * Hook to create a pending transaction
 */
export const useCreatePendingTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      walletId,
      transactionType,
      transactionData,
      description,
      expiresInHours,
    }: {
      walletId: number;
      transactionType: string;
      transactionData: Record<string, any>;
      description?: string;
      expiresInHours?: number;
    }) => {
      return await apiRequest(`/api/institutional-wallets/${walletId}/transactions`, {
        method: "POST",
        body: {
          transaction_type: transactionType,
          transaction_data: transactionData,
          description,
          expires_in_hours: expiresInHours || 24,
        },
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["institutional-wallets", variables.walletId, "transactions"],
      });
    },
  });
};

/**
 * Hook to sign a pending transaction
 */
/**
 * Guardian Management Hooks
 */
export interface SocialRecoveryGuardian {
  id: number;
  wallet_id: number;
  guardian_user_id: number | null;
  email: string | null;
  phone: string | null;
  status: string;
  verified_at: string | null;
  added_by: number;
  notes: string | null;
  created_at: string;
}

export interface RecoveryRequest {
  id: number;
  wallet_id: number;
  requester_id: number;
  reason: string;
  status: string;
  required_approvals: number;
  current_approvals: number;
  time_lock_days: number;
  unlock_time: string | null;
  expires_at: string | null;
  created_at: string;
}

export const guardianApi = {
  addGuardian: (walletId: number, data: {
    guardian_user_id?: number;
    email?: string;
    phone?: string;
    notes?: string;
  }) =>
    apiRequest<SocialRecoveryGuardian>(`/api/institutional-wallets/${walletId}/guardians`, {
      method: "POST",
      body: data,
    }),

  removeGuardian: (walletId: number, guardianId: number) =>
    apiRequest<{ success: boolean; guardian_id: number }>(
      `/api/institutional-wallets/${walletId}/guardians/${guardianId}`,
      { method: "DELETE" }
    ),

  getGuardians: (walletId: number, status?: string) => {
    const params = status ? `?status=${status}` : "";
    return apiRequest<SocialRecoveryGuardian[]>(
      `/api/institutional-wallets/${walletId}/guardians${params}`,
      { method: "GET" }
    );
  },

  createRecoveryRequest: (data: {
    wallet_id: number;
    reason: string;
    required_approvals?: number;
    time_lock_days?: number;
  }) =>
    apiRequest<RecoveryRequest>("/api/institutional-wallets/recovery/requests", {
      method: "POST",
      body: data,
    }),

  approveRecovery: (recoveryRequestId: number, data: { signature?: string }) =>
    apiRequest<{ success: boolean; current_approvals: number; required_approvals: number; status: string }>(
      `/api/institutional-wallets/recovery/requests/${recoveryRequestId}/approve`,
      { method: "POST", body: data }
    ),

  getRecoveryRequests: (walletId: number, status?: string) => {
    const params = status ? `?status=${status}` : "";
    return apiRequest<RecoveryRequest[]>(
      `/api/institutional-wallets/wallets/${walletId}/recovery-requests${params}`,
      { method: "GET" }
    );
  },
};

export function useGuardians(walletId: number, status?: string) {
  return useQuery({
    queryKey: ["institutional-wallets", walletId, "guardians", status],
    queryFn: () => guardianApi.getGuardians(walletId, status),
    enabled: !!walletId,
  });
}

export function useAddGuardian() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ walletId, ...data }: { walletId: number; guardian_user_id?: number; email?: string; phone?: string; notes?: string }) =>
      guardianApi.addGuardian(walletId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["institutional-wallets", variables.walletId, "guardians"],
      });
    },
  });
}

export function useRemoveGuardian() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ walletId, guardianId }: { walletId: number; guardianId: number }) =>
      guardianApi.removeGuardian(walletId, guardianId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["institutional-wallets", variables.walletId, "guardians"],
      });
    },
  });
}

export function useRecoveryRequests(walletId: number, status?: string) {
  return useQuery({
    queryKey: ["institutional-wallets", walletId, "recovery-requests", status],
    queryFn: () => guardianApi.getRecoveryRequests(walletId, status),
    enabled: !!walletId,
  });
}

export function useCreateRecoveryRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: guardianApi.createRecoveryRequest,
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["institutional-wallets", data.wallet_id, "recovery-requests"],
      });
    },
  });
}

export function useApproveRecovery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ recoveryRequestId, ...data }: { recoveryRequestId: number; signature?: string }) =>
      guardianApi.approveRecovery(recoveryRequestId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["institutional-wallets", "recovery-requests"] });
    },
  });
}

export const useSignTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      transactionId,
      signatureData,
    }: {
      transactionId: number;
      signatureData: Record<string, any>;
    }) => {
      return await apiRequest(`/api/institutional-wallets/transactions/${transactionId}/sign`, {
        method: "POST",
        body: { signature_data: signatureData },
      });
    },
    onSuccess: (_, variables) => {
      // Invalidate all wallet transaction queries
      queryClient.invalidateQueries({ queryKey: ["institutional-wallets"] });
    },
  });
};

/**
 * Hook to fetch audit logs
 */
export const useAuditLogs = (
  walletId: number,
  startDate?: string,
  endDate?: string,
  userId?: number
) => {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ["institutional-wallets", walletId, "audit-logs", startDate, endDate, userId],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);
      if (userId) params.append("user_id", userId.toString());
      const query = params.toString() ? `?${params.toString()}` : "";
      return await apiRequest(
        `/api/institutional-wallets/${walletId}/audit-logs${query}`,
        { method: "GET" }
      );
    },
    enabled: isAuthenticated && !!walletId,
    staleTime: 60000, // 1 minute
  });
};
