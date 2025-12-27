/**
 * React Query hooks for backup management
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";

export interface BackupMetadata {
  backup_id: string;
  backup_type: string;
  file_path: string;
  file_size: number;
  checksum: string;
  created_at: string;
  compressed: boolean;
}

export interface BackupListItem {
  file_path: string;
  file_size: number;
  created_at: string;
  compressed: boolean;
}

export const backupsApi = {
  createBackup: (backupType: string = "full", compress: boolean = true) =>
    apiRequest<BackupMetadata>("/api/backups/create", {
      method: "POST",
      body: { backup_type: backupType, compress },
    }),

  listBackups: (backupType?: string) => {
    const params = backupType ? `?backup_type=${backupType}` : "";
    return apiRequest<BackupListItem[]>(`/api/backups/list${params}`, {
      method: "GET",
    });
  },

  verifyBackup: (backupPath: string, expectedChecksum?: string) =>
    apiRequest<{ backup_path: string; is_valid: boolean }>("/api/backups/verify", {
      method: "POST",
      body: { backup_path: backupPath, expected_checksum: expectedChecksum },
    }),

  cleanupBackups: () =>
    apiRequest<{ deleted_daily: number; deleted_weekly: number; deleted_monthly: number }>(
      "/api/backups/cleanup",
      { method: "POST" }
    ),

  restoreBackup: (backupPath: string, verify: boolean = true) =>
    apiRequest<{ success: boolean; backup_path: string; message: string }>(
      "/api/backups/restore",
      {
        method: "POST",
        body: { backup_path: backupPath, verify },
      }
    ),
};

/**
 * Hook to create a backup
 */
export function useCreateBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ backupType, compress }: { backupType?: string; compress?: boolean } = {}) =>
      backupsApi.createBackup(backupType, compress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backups"] });
    },
  });
}

/**
 * Hook to list backups
 */
export function useBackups(backupType?: string) {
  return useQuery({
    queryKey: ["backups", "list", backupType],
    queryFn: () => backupsApi.listBackups(backupType),
  });
}

/**
 * Hook to verify a backup
 */
export function useVerifyBackup() {
  return useMutation({
    mutationFn: ({
      backupPath,
      expectedChecksum,
    }: {
      backupPath: string;
      expectedChecksum?: string;
    }) => backupsApi.verifyBackup(backupPath, expectedChecksum),
  });
}

/**
 * Hook to cleanup old backups
 */
export function useCleanupBackups() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: backupsApi.cleanupBackups,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backups"] });
    },
  });
}

/**
 * Hook to restore from backup
 */
export function useRestoreBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ backupPath, verify }: { backupPath: string; verify?: boolean }) =>
      backupsApi.restoreBackup(backupPath, verify),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backups"] });
    },
  });
}
