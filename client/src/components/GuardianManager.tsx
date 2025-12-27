/**
 * Guardian Manager Component
 * Manages social recovery guardians for institutional wallets
 */

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
  Shield,
  Plus,
  Trash2,
  CheckCircle2,
  Clock,
  XCircle,
  User,
  Mail,
  Phone,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  useGuardians,
  useAddGuardian,
  useRemoveGuardian,
  type SocialRecoveryGuardian,
} from "@/hooks/useInstitutionalWallets";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";

interface GuardianManagerProps {
  walletId: number;
}

export function GuardianManager({ walletId }: GuardianManagerProps) {
  const { toast } = useToast();
  const { data: guardians, isLoading } = useGuardians(walletId);
  const addGuardian = useAddGuardian();
  const removeGuardian = useRemoveGuardian();

  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [guardianUserId, setGuardianUserId] = useState("");
  const [guardianEmail, setGuardianEmail] = useState("");
  const [guardianPhone, setGuardianPhone] = useState("");
  const [guardianNotes, setGuardianNotes] = useState("");

  const handleAddGuardian = async () => {
    try {
      await addGuardian.mutateAsync({
        walletId,
        ...(guardianUserId ? { guardian_user_id: parseInt(guardianUserId) } : {}),
        ...(guardianEmail ? { email: guardianEmail } : {}),
        ...(guardianPhone ? { phone: guardianPhone } : {}),
        ...(guardianNotes ? { notes: guardianNotes } : {}),
      });
      toast({
        title: "Guardian added",
        description: "Guardian has been added successfully",
      });
      setIsAddDialogOpen(false);
      setGuardianUserId("");
      setGuardianEmail("");
      setGuardianPhone("");
      setGuardianNotes("");
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add guardian",
        variant: "destructive",
      });
    }
  };

  const handleRemoveGuardian = async (guardianId: number) => {
    try {
      await removeGuardian.mutateAsync({ walletId, guardianId });
      toast({
        title: "Guardian removed",
        description: "Guardian has been removed",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove guardian",
        variant: "destructive",
      });
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return (
          <Badge variant="default" className="bg-green-500">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Active
          </Badge>
        );
      case "pending":
        return (
          <Badge variant="secondary">
            <Clock className="h-3 w-3 mr-1" />
            Pending
          </Badge>
        );
      case "inactive":
        return (
          <Badge variant="outline">
            <XCircle className="h-3 w-3 mr-1" />
            Inactive
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
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Social Recovery Guardians
            </CardTitle>
            <CardDescription>
              Manage guardians who can approve wallet recovery requests
            </CardDescription>
          </div>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Guardian
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Guardian</DialogTitle>
                <DialogDescription>
                  Add a guardian who can approve recovery requests for this wallet
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Guardian User ID (if platform user)</Label>
                  <Input
                    type="number"
                    placeholder="User ID"
                    value={guardianUserId}
                    onChange={(e) => setGuardianUserId(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Email (if not platform user)</Label>
                  <Input
                    type="email"
                    placeholder="guardian@example.com"
                    value={guardianEmail}
                    onChange={(e) => setGuardianEmail(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Phone (optional, for SMS verification)</Label>
                  <Input
                    type="tel"
                    placeholder="+1234567890"
                    value={guardianPhone}
                    onChange={(e) => setGuardianPhone(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Notes (optional)</Label>
                  <Textarea
                    placeholder="Additional notes about this guardian"
                    value={guardianNotes}
                    onChange={(e) => setGuardianNotes(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleAddGuardian}
                  disabled={addGuardian.isPending || (!guardianUserId && !guardianEmail)}
                >
                  Add Guardian
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {guardians && guardians.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Guardian</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Verified</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {guardians.map((guardian) => (
                <TableRow key={guardian.id}>
                  <TableCell>
                    {guardian.guardian_user_id ? (
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4" />
                        User #{guardian.guardian_user_id}
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4" />
                        {guardian.email}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      {guardian.email && (
                        <div className="text-sm flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          {guardian.email}
                        </div>
                      )}
                      {guardian.phone && (
                        <div className="text-sm flex items-center gap-1">
                          <Phone className="h-3 w-3" />
                          {guardian.phone}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(guardian.status)}</TableCell>
                  <TableCell>
                    {guardian.verified_at ? (
                      <span className="text-sm text-muted-foreground">
                        {new Date(guardian.verified_at).toLocaleDateString()}
                      </span>
                    ) : (
                      <span className="text-sm text-muted-foreground">Not verified</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveGuardian(guardian.id)}
                      disabled={removeGuardian.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No guardians added</p>
            <p className="text-sm">Add guardians to enable social recovery</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
