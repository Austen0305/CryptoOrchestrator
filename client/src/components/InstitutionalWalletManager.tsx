/**
 * Institutional Wallet Manager Component
 * Manages multi-signature wallets, team access, and institutional custody features
 */

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
  Shield,
  Users,
  Plus,
  Trash2,
  Eye,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { useInstitutionalWallets, useCreateInstitutionalWallet, useAddSigner, useRemoveSigner } from "@/hooks/useInstitutionalWallets";

interface InstitutionalWallet {
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

export function InstitutionalWalletManager() {
  const { toast } = useToast();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [addSignerDialogOpen, setAddSignerDialogOpen] = useState(false);
  const [selectedWalletId, setSelectedWalletId] = useState<number | null>(null);

  // Form state
  const [walletType, setWalletType] = useState<string>("multisig");
  const [chainId, setChainId] = useState<number>(1);
  const [multisigType, setMultisigType] = useState<string>("2_of_3");
  const [requiredSignatures, setRequiredSignatures] = useState<number>(2);
  const [totalSigners, setTotalSigners] = useState<number>(3);
  const [label, setLabel] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [newSignerUserId, setNewSignerUserId] = useState<string>("");
  const [signerRole, setSignerRole] = useState<string>("signer");

  // React Query hooks
  const { data: wallets, isLoading, error } = useInstitutionalWallets();
  const createWallet = useCreateInstitutionalWallet();
  const addSigner = useAddSigner();
  const removeSigner = useRemoveSigner();

  const handleCreateWallet = async () => {
    try {
      // Parse multisig configuration
      let reqSigs = requiredSignatures;
      let totalSigs = totalSigners;
      
      if (multisigType === "2_of_3") {
        reqSigs = 2;
        totalSigs = 3;
      } else if (multisigType === "3_of_5") {
        reqSigs = 3;
        totalSigs = 5;
      }

      await createWallet.mutateAsync({
        wallet_type: walletType,
        chain_id: chainId,
        multisig_type: walletType === "multisig" ? multisigType : undefined,
        required_signatures: reqSigs,
        total_signers: totalSigs,
        label: label || undefined,
        description: description || undefined,
      });

      toast({
        title: "Wallet Created",
        description: "Institutional wallet created successfully",
      });

      setCreateDialogOpen(false);
      // Reset form
      setWalletType("multisig");
      setMultisigType("2_of_3");
      setRequiredSignatures(2);
      setTotalSigners(3);
      setLabel("");
      setDescription("");
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create wallet",
        variant: "destructive",
      });
    }
  };

  const handleAddSigner = async () => {
    if (!selectedWalletId || !newSignerUserId) return;

    try {
      const userId = parseInt(newSignerUserId);
      if (isNaN(userId)) {
        throw new Error("Invalid user ID");
      }

      await addSigner.mutateAsync({
        walletId: selectedWalletId,
        signerUserId: userId,
        role: signerRole,
      });

      toast({
        title: "Signer Added",
        description: "Signer added successfully",
      });

      setAddSignerDialogOpen(false);
      setNewSignerUserId("");
      setSelectedWalletId(null);
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to add signer",
        variant: "destructive",
      });
    }
  };

  const handleRemoveSigner = async (walletId: number, signerUserId: number) => {
    try {
      await removeSigner.mutateAsync({ walletId, signerUserId });

      toast({
        title: "Signer Removed",
        description: "Signer removed successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to remove signer",
        variant: "destructive",
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      active: "default",
      pending: "secondary",
      locked: "outline",
      frozen: "destructive",
      archived: "secondary",
    };

    return (
      <Badge variant={variants[status] || "secondary"}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getWalletTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      multisig: "Multi-Signature",
      timelock: "Time-Locked",
      treasury: "Treasury",
      custodial: "Custodial",
    };
    return labels[type] || type;
  };

  if (isLoading) {
    return <LoadingSkeleton height="400px" />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Institutional Wallets</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-destructive py-8">
            {error instanceof Error ? error.message : "Failed to load wallets"}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Institutional Wallets
              </CardTitle>
              <CardDescription>
                Manage multi-signature wallets, team access, and institutional custody
              </CardDescription>
            </div>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Wallet
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Create Institutional Wallet</DialogTitle>
                  <DialogDescription>
                    Create a new multi-signature, time-locked, or treasury wallet
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Wallet Type</Label>
                    <Select value={walletType} onValueChange={setWalletType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="multisig">Multi-Signature</SelectItem>
                        <SelectItem value="timelock">Time-Locked</SelectItem>
                        <SelectItem value="treasury">Treasury</SelectItem>
                        <SelectItem value="custodial">Custodial</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Chain</Label>
                    <Select
                      value={chainId.toString()}
                      onValueChange={(v) => setChainId(parseInt(v))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">Ethereum</SelectItem>
                        <SelectItem value="8453">Base</SelectItem>
                        <SelectItem value="42161">Arbitrum</SelectItem>
                        <SelectItem value="137">Polygon</SelectItem>
                        <SelectItem value="10">Optimism</SelectItem>
                        <SelectItem value="43114">Avalanche</SelectItem>
                        <SelectItem value="56">BNB Chain</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {walletType === "multisig" && (
                    <>
                      <div className="space-y-2">
                        <Label>Multi-Signature Type</Label>
                        <Select value={multisigType} onValueChange={setMultisigType}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="2_of_3">2 of 3</SelectItem>
                            <SelectItem value="3_of_5">3 of 5</SelectItem>
                            <SelectItem value="custom">Custom</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {multisigType === "custom" && (
                        <>
                          <div className="space-y-2">
                            <Label>Required Signatures (M)</Label>
                            <Input
                              type="number"
                              min="1"
                              value={requiredSignatures}
                              onChange={(e) => setRequiredSignatures(parseInt(e.target.value) || 1)}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Total Signers (N)</Label>
                            <Input
                              type="number"
                              min="1"
                              value={totalSigners}
                              onChange={(e) => setTotalSigners(parseInt(e.target.value) || 1)}
                            />
                          </div>
                        </>
                      )}
                    </>
                  )}

                  <div className="space-y-2">
                    <Label>Label (Optional)</Label>
                    <Input
                      value={label}
                      onChange={(e) => setLabel(e.target.value)}
                      placeholder="My Treasury Wallet"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Description (Optional)</Label>
                    <Textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Wallet description..."
                      rows={3}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateWallet} disabled={createWallet.isPending}>
                    {createWallet.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                    Create Wallet
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {!wallets || wallets.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No institutional wallets found</p>
              <p className="text-sm">Create your first wallet to get started</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Label</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Configuration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Address</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {wallets.map((wallet: InstitutionalWallet) => (
                  <TableRow key={wallet.id}>
                    <TableCell className="font-medium">
                      {wallet.label || `Wallet #${wallet.id}`}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{getWalletTypeLabel(wallet.wallet_type)}</Badge>
                    </TableCell>
                    <TableCell>
                      {wallet.wallet_type === "multisig" && (
                        <span className="text-sm text-muted-foreground">
                          {wallet.required_signatures} of {wallet.total_signers}
                        </span>
                      )}
                      {wallet.wallet_type !== "multisig" && (
                        <span className="text-sm text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>{getStatusBadge(wallet.status)}</TableCell>
                    <TableCell>
                      {wallet.wallet_address ? (
                        <span className="text-sm font-mono">
                          {wallet.wallet_address.slice(0, 10)}...
                        </span>
                      ) : (
                        <span className="text-sm text-muted-foreground">Not deployed</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedWalletId(wallet.id);
                            setAddSignerDialogOpen(true);
                          }}
                        >
                          <Users className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <FileText className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add Signer Dialog */}
      <Dialog open={addSignerDialogOpen} onOpenChange={setAddSignerDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Signer</DialogTitle>
            <DialogDescription>
              Add a user as a signer to this wallet
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>User ID</Label>
              <Input
                type="number"
                value={newSignerUserId}
                onChange={(e) => setNewSignerUserId(e.target.value)}
                placeholder="Enter user ID"
              />
            </div>
            <div className="space-y-2">
              <Label>Role</Label>
              <Select value={signerRole} onValueChange={setSignerRole}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="owner">Owner</SelectItem>
                  <SelectItem value="signer">Signer</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddSignerDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddSigner} disabled={addSigner.isPending || !newSignerUserId}>
              {addSigner.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Add Signer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
