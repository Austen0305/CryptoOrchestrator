/**
 * Accounting Connection Manager Component
 * Manages OAuth connections to QuickBooks and Xero
 */

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Link,
  Unlink,
  RefreshCw,
  Settings,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  ExternalLink,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  useAccountingConnections,
  useAccountingAuthUrl,
  useCompleteAccountingOAuth,
  useDisconnectAccounting,
  useUpdateSyncConfig,
  useExportToAccounting,
  type AccountingConnection,
} from "@/hooks/useAccounting";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";

export function AccountingConnectionManager() {
  const { toast } = useToast();
  const { data: connections, isLoading } = useAccountingConnections();
  const [selectedSystem, setSelectedSystem] = useState<string | null>(null);
  const [isOAuthDialogOpen, setIsOAuthDialogOpen] = useState(false);

  const { data: authUrl } = useAccountingAuthUrl(selectedSystem || "", !!selectedSystem);
  const completeOAuth = useCompleteAccountingOAuth();
  const disconnect = useDisconnectAccounting();
  const updateSync = useUpdateSyncConfig();
  const exportToAccounting = useExportToAccounting();

  const handleConnect = (system: string) => {
    setSelectedSystem(system);
    setIsOAuthDialogOpen(true);
  };

  const handleOAuthComplete = async (authorizationCode: string, state?: string) => {
    if (!selectedSystem) return;

    try {
      await completeOAuth.mutateAsync({
        system: selectedSystem,
        authorization_code: authorizationCode,
        state,
      });
      toast({
        title: "Connected!",
        description: `${selectedSystem} has been connected successfully`,
      });
      setIsOAuthDialogOpen(false);
    } catch (error) {
      toast({
        title: "Connection failed",
        description: "Failed to complete OAuth flow",
        variant: "destructive",
      });
    }
  };

  const handleDisconnect = async (system: string) => {
    try {
      await disconnect.mutateAsync(system);
      toast({
        title: "Disconnected",
        description: `${system} has been disconnected`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to disconnect",
        variant: "destructive",
      });
    }
  };

  const handleExport = async (system: string, taxYear: number) => {
    try {
      await exportToAccounting.mutateAsync({
        system,
        taxYear,
      });
      toast({
        title: "Export initiated",
        description: `Exporting to ${system}...`,
      });
    } catch (error) {
      toast({
        title: "Export failed",
        description: "Failed to export to accounting system",
        variant: "destructive",
      });
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "connected":
        return (
          <Badge variant="default" className="bg-green-500">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Connected
          </Badge>
        );
      case "pending":
        return (
          <Badge variant="secondary">
            <Clock className="h-3 w-3 mr-1" />
            Pending
          </Badge>
        );
      case "error":
        return (
          <Badge variant="destructive">
            <XCircle className="h-3 w-3 mr-1" />
            Error
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Accounting System Connections</CardTitle>
          <CardDescription>
            Connect your QuickBooks or Xero account to automatically sync tax data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* QuickBooks */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>QuickBooks Online</CardTitle>
                    <CardDescription>Sync transactions to QuickBooks</CardDescription>
                  </div>
                  {connections?.find((c) => c.system === "quickbooks") ? (
                    <div className="flex gap-2">
                      {getStatusBadge(
                        connections.find((c) => c.system === "quickbooks")!.status
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDisconnect("quickbooks")}
                      >
                        <Unlink className="h-4 w-4 mr-2" />
                        Disconnect
                      </Button>
                    </div>
                  ) : (
                    <Button onClick={() => handleConnect("quickbooks")}>
                      <Link className="h-4 w-4 mr-2" />
                      Connect
                    </Button>
                  )}
                </div>
              </CardHeader>
            </Card>

            {/* Xero */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Xero</CardTitle>
                    <CardDescription>Sync transactions to Xero</CardDescription>
                  </div>
                  {connections?.find((c) => c.system === "xero") ? (
                    <div className="flex gap-2">
                      {getStatusBadge(connections.find((c) => c.system === "xero")!.status)}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDisconnect("xero")}
                      >
                        <Unlink className="h-4 w-4 mr-2" />
                        Disconnect
                      </Button>
                    </div>
                  ) : (
                    <Button onClick={() => handleConnect("xero")}>
                      <Link className="h-4 w-4 mr-2" />
                      Connect
                    </Button>
                  )}
                </div>
              </CardHeader>
            </Card>

            {/* Connections Table */}
            {connections && connections.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-4">Active Connections</h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>System</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Sync Frequency</TableHead>
                      <TableHead>Last Sync</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {connections.map((connection) => (
                      <TableRow key={connection.id}>
                        <TableCell className="font-medium capitalize">
                          {connection.system}
                        </TableCell>
                        <TableCell>{getStatusBadge(connection.status)}</TableCell>
                        <TableCell className="capitalize">{connection.sync_frequency}</TableCell>
                        <TableCell>
                          {connection.last_sync_at
                            ? new Date(connection.last_sync_at).toLocaleDateString()
                            : "Never"}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                handleExport(connection.system, new Date().getFullYear())
                              }
                            >
                              Export
                            </Button>
                            <Button variant="outline" size="sm">
                              <Settings className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* OAuth Dialog */}
      <Dialog open={isOAuthDialogOpen} onOpenChange={setIsOAuthDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Connect {selectedSystem}</DialogTitle>
            <DialogDescription>
              You will be redirected to authorize the connection
            </DialogDescription>
          </DialogHeader>
          {authUrl && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Click the button below to authorize the connection:
              </p>
              <Button
                onClick={() => window.open(authUrl.authorization_url, "_blank")}
                className="w-full"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Authorize {selectedSystem}
              </Button>
              <p className="text-xs text-muted-foreground">
                After authorization, you'll be redirected back with an authorization code. Paste it
                below:
              </p>
              <input
                type="text"
                placeholder="Paste authorization code here"
                className="w-full p-2 border rounded"
                onBlur={(e) => {
                  if (e.target.value) {
                    handleOAuthComplete(e.target.value);
                  }
                }}
              />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
