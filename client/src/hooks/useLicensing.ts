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
  return useQuery<{ license_types: Record<string, LicenseType> }>({
    queryKey: ["licensing", "types"],
    queryFn: async () => {
      return await apiRequest<{ license_types: Record<string, LicenseType> }>("/api/licensing/types", {
        method: "GET",
      });
    },
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes
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
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (data: ValidateLicenseRequest) => {
      return await apiRequest<LicenseStatus>("/api/licensing/validate", {
        method: "POST",
        body: data,
      });
    },
    enabled: isAuthenticated,
  });
}

export function useActivateLicense() {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  return useMutation({
    mutationFn: async (data: ActivateLicenseRequest) => {
      return await apiRequest<LicenseStatus>("/api/licensing/activate", {
        method: "POST",
        body: data,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["licensing"] });
    },
    enabled: isAuthenticated,
  });
}

export function useGenerateLicense() {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
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
    enabled: isAuthenticated,
  });
}
