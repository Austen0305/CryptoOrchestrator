/**
 * React hooks for license management
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

// Types
export interface LicenseStatus {
  valid: boolean;
  license_type: string;
  expires_at?: string;
  activated_at?: string;
  max_bots: number;
  features: string[];
  message?: string;
}

export interface LicenseInfo {
  license_key: string;
  license_type: string;
  user_id: string;
  expires_at?: string;
  created_at: string;
  max_bots: number;
  features: string[];
}

export interface LicenseType {
  duration_days?: number;
  max_bots: number;
  features: string[];
}

export interface GenerateLicenseRequest {
  user_id: string;
  license_type: string;
  expires_at?: string;
}

export interface ValidateLicenseRequest {
  license_key: string;
  machine_id?: string;
}

export interface ActivateLicenseRequest {
  license_key: string;
  machine_id?: string;
}

// Hooks
export function useLicenseTypes() {
  const { isAuthenticated } = useAuth();
  return useQuery<{ license_types: Record<string, LicenseType> }>({
    queryKey: ["licensing", "types"],
    queryFn: async () => {
      return await apiRequest<{ license_types: Record<string, LicenseType> }>("/api/licensing/types", {
        method: "GET",
      });
    },
    enabled: isAuthenticated,
    staleTime: 10 * 60 * 1000, // 10 minutes - license types don't change often
  });
}

export function useMachineId() {
  const { isAuthenticated } = useAuth();
  
  return useQuery<{ machine_id: string }>({
    queryKey: ["licensing", "machine-id"],
    queryFn: async () => {
      return await apiRequest<{ machine_id: string }>("/api/licensing/machine-id", {
        method: "GET",
      });
    },
    enabled: isAuthenticated,
    staleTime: Infinity, // Machine ID doesn't change
  });
}

export function useValidateLicense() {
  return useMutation({
    mutationFn: async (data: ValidateLicenseRequest) => {
      return await apiRequest<LicenseStatus>("/api/licensing/validate", {
        method: "POST",
        body: data,
      });
    },
  });
}

export function useActivateLicense() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: ActivateLicenseRequest) => {
      return await apiRequest<LicenseStatus>("/api/licensing/activate", {
        method: "POST",
        body: data,
      });
    },
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (data) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["licensing"] });
      
      // Snapshot the previous value
      const previousLicense = queryClient.getQueryData(["licensing", "status"]);
      
      // Return a context object with the snapshotted value
      return { previousLicense };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["licensing"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, data, context) => {
      if (context?.previousLicense) {
        queryClient.setQueryData(["licensing", "status"], context.previousLicense);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["licensing"] });
    },
  });
}

export function useGenerateLicense() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: GenerateLicenseRequest) => {
      return await apiRequest<LicenseInfo>("/api/licensing/generate", {
        method: "POST",
        body: data,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["licensing"] });
    },
  });
}
