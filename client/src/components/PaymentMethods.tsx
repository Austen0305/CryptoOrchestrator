import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { CreditCard, Building2, Plus, Trash2, CheckCircle2 } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";

interface PaymentMethod {
  id: string;
  type: string;
  card?: {
    brand: string;
    last4: string;
    exp_month: number;
    exp_year: number;
  };
  us_bank_account?: {
    bank_name: string;
    last4: string;
    account_type: string;
  };
}

export function PaymentMethods() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [paymentMethodType, setPaymentMethodType] = useState<"card" | "ach">("card");

  const { data: paymentMethods, isLoading, error, refetch } = useQuery({
    queryKey: ["payment-methods"],
    queryFn: async () => {
      return await apiRequest<PaymentMethod[]>("/api/payment-methods", {
        method: "GET"
      });
    },
    retry: 2,
  });

  const createSetupIntent = useMutation({
    mutationFn: async (type: "card" | "ach") => {
      return await apiRequest("/api/payment-methods/setup-intent", {
        method: "POST",
        body: { payment_method_type: type }
      });
    },
    onSuccess: (data) => {
      // In production, would use Stripe Elements to collect payment method
      // For now, show instructions
      toast({
        title: "Setup Intent Created",
        description: `Client secret: ${data.client_secret?.substring(0, 20)}...`
      });
    }
  });

  const deletePaymentMethod = useMutation({
    mutationFn: async (paymentMethodId: string) => {
      return await apiRequest(`/api/payment-methods/${paymentMethodId}`, {
        method: "DELETE"
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payment-methods"] });
      toast({
        title: "Payment Method Deleted",
        description: "Payment method has been removed"
      });
    }
  });

  const handleAddPaymentMethod = async () => {
    try {
      await createSetupIntent.mutateAsync(paymentMethodType);
      setShowAddDialog(false);
    } catch (error) {
      toast({
        title: "Failed to Add Payment Method",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive"
      });
    }
  };

  const formatCardNumber = (last4: string) => `**** **** **** ${last4}`;
  const formatExpiry = (month: number, year: number) => `${month.toString().padStart(2, '0')}/${year}`;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Payment Methods</CardTitle>
            <CardDescription>Manage your cards and bank accounts</CardDescription>
          </div>
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Payment Method
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Payment Method</DialogTitle>
                <DialogDescription>
                  Add a credit card or bank account for deposits
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Payment Method Type</Label>
                  <Select
                    value={paymentMethodType}
                    onValueChange={(value) => setPaymentMethodType(value as "card" | "ach")}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="card">Credit/Debit Card</SelectItem>
                      <SelectItem value="ach">Bank Account (ACH)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="text-sm text-muted-foreground">
                  {paymentMethodType === "card" ? (
                    <p>You'll be redirected to securely enter your card details.</p>
                  ) : (
                    <p>You'll be redirected to securely link your bank account.</p>
                  )}
                </div>
                <Button onClick={handleAddPaymentMethod} className="w-full">
                  Continue
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <LoadingSkeleton count={3} className="h-20 w-full mb-2" />
        ) : error ? (
          <ErrorRetry
            title="Failed to load payment methods"
            message={error instanceof Error ? error.message : "An unexpected error occurred."}
            onRetry={() => refetch()}
            error={error as Error}
          />
        ) : paymentMethods && paymentMethods.length > 0 ? (
          <div className="space-y-4">
            {paymentMethods.map((method) => (
              <div
                key={method.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center gap-4">
                  {method.type === "card" ? (
                    <CreditCard className="h-8 w-8 text-muted-foreground" />
                  ) : (
                    <Building2 className="h-8 w-8 text-muted-foreground" />
                  )}
                  <div>
                    {method.type === "card" && method.card ? (
                      <>
                        <div className="font-medium">
                          {method.card.brand.toUpperCase()} {formatCardNumber(method.card.last4)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Expires {formatExpiry(method.card.exp_month, method.card.exp_year)}
                        </div>
                      </>
                    ) : method.us_bank_account ? (
                      <>
                        <div className="font-medium">
                          {method.us_bank_account.bank_name || "Bank Account"}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          ****{method.us_bank_account.last4} ({method.us_bank_account.account_type})
                        </div>
                      </>
                    ) : (
                      <div className="font-medium">{method.type.toUpperCase()}</div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deletePaymentMethod.mutate(method.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={CreditCard}
            title="No payment methods added yet"
            description="Add a payment method to enable deposits and withdrawals."
            action={
              <Button onClick={() => setShowAddDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Payment Method
              </Button>
            }
          />
        )}
      </CardContent>
    </Card>
  );
}

