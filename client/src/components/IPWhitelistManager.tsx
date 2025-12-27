/**
 * IP Whitelist Manager Component
 * Allows users to manage their IP whitelist for enhanced security
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Shield, Plus, Trash2, AlertCircle, CheckCircle2 } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import logger from "@/lib/logger";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface IPWhitelistEntry {
  address: string;
  label?: string;
  added_at?: string;
}

// API functions
const ipWhitelistApi = {
  getWhitelist: () => apiRequest<IPWhitelistEntry[]>("/api/security/whitelists/ip", { method: "GET" }),
  addIP: (ipAddress: string, label?: string) =>
    apiRequest("/api/security/whitelists/ip", {
      method: "POST",
      body: { ip_address: ipAddress, label },
    }),
  removeIP: (ipAddress: string) =>
    apiRequest("/api/security/whitelists/ip", {
      method: "DELETE",
      body: { ip_address: ipAddress },
    }),
};

export function IPWhitelistManager() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [newIP, setNewIP] = useState("");
  const [newLabel, setNewLabel] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Fetch IP whitelist
  const { data: whitelist = [], isLoading } = useQuery({
    queryKey: ["ip-whitelist"],
    queryFn: () => ipWhitelistApi.getWhitelist(),
  });

  // Add IP mutation
  const addIPMutation = useMutation({
    mutationFn: ({ ip, label }: { ip: string; label?: string }) => ipWhitelistApi.addIP(ip, label),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ip-whitelist"] });
      toast({
        title: "IP Added",
        description: "IP address has been added to your whitelist.",
      });
      setNewIP("");
      setNewLabel("");
      setIsDialogOpen(false);
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to Add IP",
        description: error.message || "Failed to add IP address to whitelist.",
        variant: "destructive",
      });
    },
  });

  // Remove IP mutation
  const removeIPMutation = useMutation({
    mutationFn: (ipAddress: string) => ipWhitelistApi.removeIP(ipAddress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ip-whitelist"] });
      toast({
        title: "IP Removed",
        description: "IP address has been removed from your whitelist.",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to Remove IP",
        description: error.message || "Failed to remove IP address from whitelist.",
        variant: "destructive",
      });
    },
  });

  const handleAddIP = () => {
    if (!newIP.trim()) {
      toast({
        title: "Invalid IP",
        description: "Please enter a valid IP address.",
        variant: "destructive",
      });
      return;
    }

    // Basic IP validation
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    if (!ipRegex.test(newIP)) {
      toast({
        title: "Invalid IP Format",
        description: "Please enter a valid IPv4 address (e.g., 192.168.1.1).",
        variant: "destructive",
      });
      return;
    }

    addIPMutation.mutate({ ip: newIP.trim(), label: newLabel.trim() || undefined });
  };

  const handleRemoveIP = (ipAddress: string) => {
    if (confirm(`Are you sure you want to remove ${ipAddress} from your whitelist?`)) {
      removeIPMutation.mutate(ipAddress);
    }
  };

  // Get current IP (for convenience)
  const getCurrentIP = async () => {
    try {
      // In production, you'd call an endpoint that returns the client's IP
      // For now, we'll use a service or leave it empty
      // This is a placeholder - actual implementation would need backend endpoint
      toast({
        title: "Current IP",
        description: "Please enter your current IP address manually, or contact support for assistance.",
      });
    } catch (error) {
      logger.error("Failed to get current IP", { error });
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              IP Whitelist
            </CardTitle>
            <CardDescription>
              Manage IP addresses allowed to access sensitive operations (withdrawals, real money trades).
              When enabled, only whitelisted IPs can perform these operations.
            </CardDescription>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add IP
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add IP Address to Whitelist</DialogTitle>
                <DialogDescription>
                  Add an IP address to your whitelist. Only whitelisted IPs can perform sensitive operations.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="ip-address">IP Address</Label>
                  <Input
                    id="ip-address"
                    placeholder="192.168.1.1"
                    value={newIP}
                    onChange={(e) => setNewIP(e.target.value)}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={getCurrentIP}
                    className="text-xs"
                  >
                    Get My Current IP
                  </Button>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ip-label">Label (Optional)</Label>
                  <Input
                    id="ip-label"
                    placeholder="Home, Office, etc."
                    value={newLabel}
                    onChange={(e) => setNewLabel(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleAddIP} disabled={addIPMutation.isPending}>
                  {addIPMutation.isPending ? "Adding..." : "Add IP"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">Loading whitelist...</div>
        ) : whitelist.length === 0 ? (
          <div className="text-center py-8 space-y-4">
            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground" />
            <div>
              <p className="font-medium">No IP addresses whitelisted</p>
              <p className="text-sm text-muted-foreground mt-2">
                IP whitelisting is not enabled. Add IP addresses to enable this security feature.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {whitelist && Array.isArray(whitelist) && whitelist.length > 0 ? whitelist.map((entry, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <div>
                    <p className="font-mono font-medium">{entry.address}</p>
                    {entry.label && (
                      <p className="text-sm text-muted-foreground">{entry.label}</p>
                    )}
                    {entry.added_at && (
                      <p className="text-xs text-muted-foreground">
                        Added {new Date(entry.added_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveIP(entry.address)}
                  disabled={removeIPMutation.isPending}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            )) : (
              <div className="text-center text-muted-foreground py-8">
                No IP addresses whitelisted
              </div>
            )}
          </div>
        )}

        {whitelist.length > 0 && (
          <div className="mt-6 p-4 bg-muted/50 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium">Security Notice</p>
                <p className="text-muted-foreground mt-1">
                  When IP whitelisting is enabled, only whitelisted IPs can perform withdrawals and real money trades.
                  Make sure to add all IPs you'll use to access the platform.
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
