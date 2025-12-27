/**
 * Backup Manager Component
 * Manages database backups and restoration
 */

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Database,
  Download,
  Trash2,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  useBackups,
  useCreateBackup,
  useVerifyBackup,
  useCleanupBackups,
  useRestoreBackup,
  type BackupListItem,
} from "@/hooks/useBackups";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";

export function BackupManager() {
  const { toast } = useToast();
  const { data: backups, isLoading, refetch } = useBackups();
  const createBackup = useCreateBackup();
  const verifyBackup = useVerifyBackup();
  const cleanupBackups = useCleanupBackups();
  const restoreBackup = useRestoreBackup();

  const [restoreBackupPath, setRestoreBackupPath] = useState<string | null>(null);
  const [isRestoreDialogOpen, setIsRestoreDialogOpen] = useState(false);

  const handleCreateBackup = async () => {
    try {
      await createBackup.mutateAsync({ backupType: "full", compress: true });
      toast({
        title: "Backup created",
        description: "Database backup created successfully",
      });
      refetch();
    } catch (error) {
      toast({
        title: "Backup failed",
        description: "Failed to create backup",
        variant: "destructive",
      });
    }
  };

  const handleVerify = async (backupPath: string) => {
    try {
      const result = await verifyBackup.mutateAsync({
        backupPath,
      });
      toast({
        title: result.is_valid ? "Backup verified" : "Backup invalid",
        description: result.is_valid
          ? "Backup integrity verified"
          : "Backup verification failed",
        variant: result.is_valid ? "default" : "destructive",
      });
    } catch (error) {
      toast({
        title: "Verification failed",
        description: "Failed to verify backup",
        variant: "destructive",
      });
    }
  };

  const handleCleanup = async () => {
    try {
      const stats = await cleanupBackups.mutateAsync();
      toast({
        title: "Cleanup complete",
        description: `Deleted ${stats.deleted_daily} daily, ${stats.deleted_weekly} weekly, ${stats.deleted_monthly} monthly backups`,
      });
      refetch();
    } catch (error) {
      toast({
        title: "Cleanup failed",
        description: "Failed to cleanup old backups",
        variant: "destructive",
      });
    }
  };

  const handleRestore = async () => {
    if (!restoreBackupPath) return;

    try {
      await restoreBackup.mutateAsync({
        backupPath: restoreBackupPath,
        verify: true,
      });
      toast({
        title: "Restore initiated",
        description: "Database restoration in progress. Please wait...",
      });
      setIsRestoreDialogOpen(false);
      setRestoreBackupPath(null);
    } catch (error) {
      toast({
        title: "Restore failed",
        description: "Failed to restore from backup",
        variant: "destructive",
      });
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Database Backups
              </CardTitle>
              <CardDescription>
                Create, verify, and restore database backups
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleCleanup}
                disabled={cleanupBackups.isPending}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Cleanup Old
              </Button>
              <Button
                onClick={handleCreateBackup}
                disabled={createBackup.isPending}
              >
                {createBackup.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Database className="h-4 w-4 mr-2" />
                    Create Backup
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {backups && backups.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Compressed</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {backups.map((backup, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono text-sm">
                      {backup.file_path.split("/").pop()}
                    </TableCell>
                    <TableCell>{formatFileSize(backup.file_size)}</TableCell>
                    <TableCell>
                      {new Date(backup.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      {backup.compressed ? (
                        <Badge variant="secondary">Compressed</Badge>
                      ) : (
                        <Badge variant="outline">Raw</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleVerify(backup.file_path)}
                          disabled={verifyBackup.isPending}
                        >
                          <CheckCircle2 className="h-4 w-4 mr-1" />
                          Verify
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setRestoreBackupPath(backup.file_path);
                            setIsRestoreDialogOpen(true);
                          }}
                        >
                          <RefreshCw className="h-4 w-4 mr-1" />
                          Restore
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No backups found</p>
              <p className="text-sm">Create your first backup to get started</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Restore Confirmation Dialog */}
      <AlertDialog open={isRestoreDialogOpen} onOpenChange={setIsRestoreDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Restore Database?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will restore the database from: <code className="text-xs">{restoreBackupPath}</code>
              <br />
              <strong className="text-destructive">
                WARNING: This will overwrite all current data!
              </strong>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRestore}
              className="bg-destructive text-destructive-foreground"
            >
              Restore
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
