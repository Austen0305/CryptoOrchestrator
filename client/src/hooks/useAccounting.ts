/**
 * React Query hooks for accounting system connections
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";

export interface AccountingConnection {
  id: number;
  system: string;
  status: string;
  sync_frequency: string;
  last_sync_at: string | null;
  next_sync_at: string | null;
  enabled: boolean;
  connected_at: string;
}

export interface AccountingConnectionResponse {
  authorization_url: string;
  system: string;
}

export const accountingApi = {
  getAuthorizationUrl: (system: string) =>
    apiRequest<AccountingConnectionResponse>(
      `/api/tax/accounting/connect/${system}`,
      { method: "GET" }
    ),

  completeOAuth: (data: {
    system: string;
    authorization_code: string;
    state?: string;
  }) =>
    apiRequest<{ id: number; system: string; status: string; connected_at: string }>(
      "/api/tax/accounting/complete",
      {
        method: "POST",
        body: data,
      }
    ),

  getConnections: () =>
    apiRequest<AccountingConnection[]>("/api/tax/accounting/connections", {
      method: "GET",
    }),

  exportToAccounting: (system: string, taxYear: number, startDate?: string, endDate?: string) => {
    const params = new URLSearchParams({
      tax_year: taxYear.toString(),
    });
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);

    return apiRequest<{ success: boolean; system: string; tax_year: number; message: string }>(
      `/api/tax/accounting/export/${system}?${params.toString()}`,
      { method: "POST" }
    );
  },

  updateSyncConfig: (system: string, data: { sync_frequency: string; account_mappings?: Record<string, string> }) =>
    apiRequest<{ id: number; sync_frequency: string; next_sync_at: string | null }>(
      `/api/tax/accounting/${system}/sync-config`,
      {
        method: "POST",
        body: data,
      }
    ),

  disconnect: (system: string) =>
    apiRequest<{ success: boolean; system: string }>(
      `/api/tax/accounting/${system}/disconnect`,
      { method: "DELETE" }
    ),
};

/**
 * Hook to get OAuth authorization URL
 */
export function useAccountingAuthUrl(system: string, enabled: boolean = false) {
  return useQuery({
    queryKey: ["accounting", "auth-url", system],
    queryFn: () => accountingApi.getAuthorizationUrl(system),
    enabled: enabled && !!system,
  });
}

/**
 * Hook to complete OAuth flow
 */
export function useCompleteAccountingOAuth() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountingApi.completeOAuth,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounting", "connections"] });
    },
  });
}

/**
 * Hook to get all accounting connections
 */
export function useAccountingConnections() {
  return useQuery({
    queryKey: ["accounting", "connections"],
    queryFn: accountingApi.getConnections,
  });
}

/**
 * Hook to export to accounting system
 */
export function useExportToAccounting() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      system,
      taxYear,
      startDate,
      endDate,
    }: {
      system: string;
      taxYear: number;
      startDate?: string;
      endDate?: string;
    }) => accountingApi.exportToAccounting(system, taxYear, startDate, endDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounting"] });
    },
  });
}

/**
 * Hook to update sync configuration
 */
export function useUpdateSyncConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      system,
      ...data
    }: {
      system: string;
      sync_frequency: string;
      account_mappings?: Record<string, string>;
    }) => accountingApi.updateSyncConfig(system, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounting", "connections"] });
    },
  });
}

/**
 * Hook to disconnect accounting system
 */
export function useDisconnectAccounting() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: accountingApi.disconnect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounting", "connections"] });
    },
  });
}
