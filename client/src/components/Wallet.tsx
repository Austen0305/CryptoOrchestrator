import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Wallet as WalletIcon, ArrowDown, ArrowUp, DollarSign, TrendingUp, Clock } from "lucide-react";
import { useWallet, useWalletTransactions, useDeposit, useWithdraw, type WalletBalance, type WalletTransaction } from "@/hooks/useWallet";
import { useWalletWebSocket } from "@/hooks/useWalletWebSocket";
import { formatCurrency } from "@/lib/formatters";
import { useToast } from "@/hooks/use-toast";
import { depositSchema, withdrawSchema, validateAmount, formatCurrencyInput } from "@/lib/validation";
import { ZodError } from "zod";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";

export function Wallet() {
  const { data: balance, isLoading, error: balanceError, refetch: refetchBalance } = useWallet("USD");
  const { balance: wsBalance, isConnected: wsConnected } = useWalletWebSocket("USD");
  const { data: transactions, isLoading: transactionsLoading, error: transactionsError, refetch: refetchTransactions } = useWalletTransactions();
  const deposit = useDeposit();
  const withdraw = useWithdraw();
  const { toast } = useToast();
  
  // Use WebSocket balance if available, otherwise fall back to API balance
  const displayBalance = (wsBalance || balance) as WalletBalance | undefined;
  
  const [showDepositDialog, setShowDepositDialog] = useState(false);
  const [showWithdrawDialog, setShowWithdrawDialog] = useState(false);
  const [depositAmount, setDepositAmount] = useState("");
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  
  const handleDeposit = async () => {
    const amount = parseFloat(depositAmount);
    
    // Validate amount (min 0.01, max 1000000)
    if (amount < 0.01 || amount > 1000000) {
      toast({
        title: "Invalid Amount",
        description: "Amount must be between 0.01 and 1,000,000",
        variant: "destructive"
      });
      return;
    }
    const amountValidation = validateAmount(amount, 0.01);
    if (!amountValidation.valid) {
      toast({
        title: "Invalid Amount",
        description: amountValidation.error,
        variant: "destructive"
      });
      return;
    }
    
    // Validate with schema
    try {
      depositSchema.parse({
        amount,
        currency,
        payment_method_id: undefined,
        description: undefined
      });
    } catch (error) {
      const zodError = error instanceof ZodError ? error : null;
      toast({
        title: "Validation Error",
        description: zodError?.issues?.[0]?.message || "Invalid deposit data",
        variant: "destructive"
      });
      return;
    }
    
    try {
      await deposit.mutateAsync({
        amount,
        currency
      });
      toast({
        title: "Deposit Initiated",
        description: "Your deposit is being processed"
      });
      setShowDepositDialog(false);
      setDepositAmount("");
    } catch (error) {
      toast({
        title: "Deposit Failed",
        description: error instanceof Error ? error.message : "Failed to process deposit",
        variant: "destructive"
      });
    }
  };
  
  const handleWithdraw = async () => {
    const amount = parseFloat(withdrawAmount);
    
    // Validate amount (min 0.01, max 1000000)
    if (amount < 0.01 || amount > 1000000) {
      toast({
        title: "Invalid Amount",
        description: "Amount must be between 0.01 and 1,000,000",
        variant: "destructive"
      });
      return;
    }
    const amountValidation = validateAmount(amount, 0.01);
    if (!amountValidation.valid) {
      toast({
        title: "Invalid Amount",
        description: amountValidation.error,
        variant: "destructive"
      });
      return;
    }
    
    // Check available balance
    if (displayBalance && amount > displayBalance.available_balance) {
      toast({
        title: "Insufficient Balance",
        description: `Available balance: ${formatCurrency(displayBalance.available_balance)} ${currency}`,
        variant: "destructive"
      });
      return;
    }
    
    // Validate with schema
    try {
      withdrawSchema.parse({
        amount,
        currency,
        destination: undefined,
        description: undefined
      });
    } catch (error) {
      const zodError = error instanceof ZodError ? error : null;
      toast({
        title: "Validation Error",
        description: zodError?.issues?.[0]?.message || "Invalid withdrawal data",
        variant: "destructive"
      });
      return;
    }
    
    try {
      await withdraw.mutateAsync({
        amount,
        currency
      });
      toast({
        title: "Withdrawal Initiated",
        description: "Your withdrawal is being processed"
      });
      setShowWithdrawDialog(false);
      setWithdrawAmount("");
    } catch (error) {
      toast({
        title: "Withdrawal Failed",
        description: error instanceof Error ? error.message : "Failed to process withdrawal",
        variant: "destructive"
      });
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Wallet Balance Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <WalletIcon className="h-5 w-5" />
                Wallet Balance
              </CardTitle>
              <CardDescription>
                Manage your funds for trading
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Dialog open={showDepositDialog} onOpenChange={setShowDepositDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="gap-2">
                    <ArrowDown className="h-4 w-4" />
                    Deposit
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Deposit Funds</DialogTitle>
                    <DialogDescription>
                      Add funds to your wallet for trading
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Currency</label>
                      <Select value={currency} onValueChange={setCurrency}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="USD">USD</SelectItem>
                          <SelectItem value="BTC">BTC</SelectItem>
                          <SelectItem value="ETH">ETH</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Amount</label>
                      <Input
                        type="text"
                        placeholder="0.00"
                        value={depositAmount}
                        onChange={(e) => {
                          const formatted = formatCurrencyInput(e.target.value);
                          setDepositAmount(formatted);
                        }}
                        min="0"
                        step="0.01"
                      />
                      {depositAmount && parseFloat(depositAmount) > 0 && (
                        <p className="text-xs text-muted-foreground mt-1">
                          ≈ {formatCurrency(parseFloat(depositAmount))} {currency}
                        </p>
                      )}
                    </div>
                    <Button 
                      onClick={handleDeposit} 
                      className="w-full"
                      disabled={deposit.isPending}
                    >
                      {deposit.isPending ? "Processing..." : "Deposit"}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
              
              <Dialog open={showWithdrawDialog} onOpenChange={setShowWithdrawDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="gap-2">
                    <ArrowUp className="h-4 w-4" />
                    Withdraw
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Withdraw Funds</DialogTitle>
                    <DialogDescription>
                      Withdraw funds from your wallet
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Currency</label>
                      <Select value={currency} onValueChange={setCurrency}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="USD">USD</SelectItem>
                          <SelectItem value="BTC">BTC</SelectItem>
                          <SelectItem value="ETH">ETH</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Amount</label>
                      <Input
                        type="text"
                        placeholder="0.00"
                        value={withdrawAmount}
                        onChange={(e) => {
                          const formatted = formatCurrencyInput(e.target.value);
                          setWithdrawAmount(formatted);
                        }}
                        min="0"
                        step="0.01"
                      />
                      {displayBalance && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Available: {formatCurrency(displayBalance.available_balance)} {currency}
                        </p>
                      )}
                      {withdrawAmount && parseFloat(withdrawAmount) > 0 && (
                        <p className="text-xs text-muted-foreground mt-1">
                          ≈ {formatCurrency(parseFloat(withdrawAmount))} {currency}
                        </p>
                      )}
                    </div>
                    <Button 
                      onClick={handleWithdraw} 
                      className="w-full"
                      disabled={withdraw.isPending}
                    >
                      {withdraw.isPending ? "Processing..." : "Withdraw"}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading && !displayBalance ? (
            <LoadingSkeleton count={3} className="h-20 w-full mb-4" />
          ) : balanceError ? (
            <ErrorRetry
              title="Failed to load wallet balance"
              message={balanceError instanceof Error ? balanceError.message : "An unexpected error occurred."}
              onRetry={() => refetchBalance()}
              error={balanceError as Error}
            />
          ) : displayBalance ? (
            <>
              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-sm">
                  <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-gray-400'}`} />
                  <span className="text-muted-foreground">
                    {wsConnected ? 'Real-time updates active' : 'Using API data'}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg border">
                <div className="text-sm text-muted-foreground mb-1">Total Balance</div>
                <div className="text-2xl font-bold">{formatCurrency(displayBalance.balance)} {displayBalance.currency}</div>
              </div>
              <div className="p-4 rounded-lg border">
                <div className="text-sm text-muted-foreground mb-1">Available</div>
                <div className="text-2xl font-bold text-green-500">
                  {formatCurrency(displayBalance.available_balance)} {displayBalance.currency}
                </div>
              </div>
              <div className="p-4 rounded-lg border">
                <div className="text-sm text-muted-foreground mb-1">Locked</div>
                <div className="text-2xl font-bold text-yellow-500">
                  {formatCurrency(displayBalance.locked_balance)} {displayBalance.currency}
                </div>
              </div>
            </div>
            </>
          ) : (
            <EmptyState
              icon={WalletIcon}
              title="No wallet balance found"
              description="Your wallet balance could not be loaded or is empty."
            />
          )}
        </CardContent>
      </Card>
      
      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
          <CardDescription>
            View your deposit and withdrawal history
          </CardDescription>
        </CardHeader>
        <CardContent>
          {transactionsLoading ? (
            <LoadingSkeleton count={5} className="h-12 w-full mb-2" />
          ) : transactionsError ? (
            <ErrorRetry
              title="Failed to load transactions"
              message={transactionsError instanceof Error ? transactionsError.message : "An unexpected error occurred."}
              onRetry={() => refetchTransactions()}
              error={transactionsError as Error}
            />
          ) : transactions?.transactions && transactions.transactions.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.transactions.map((tx) => (
                  <TableRow key={tx.id}>
                    <TableCell>
                      <Badge variant={
                        tx.type === "deposit" ? "default" : 
                        tx.type === "withdrawal" ? "secondary" : 
                        "outline"
                      }>
                        {tx.type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {tx.type === "deposit" ? "+" : "-"}
                      {formatCurrency(tx.amount)} {tx.currency}
                    </TableCell>
                    <TableCell>
                      <Badge variant={
                        tx.status === "completed" ? "default" :
                        tx.status === "pending" ? "secondary" :
                        "destructive"
                      }>
                        {tx.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {tx.created_at ? new Date(tx.created_at).toLocaleString() : "N/A"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <EmptyState
              icon={Clock}
              title="No transactions found"
              description="Your transaction history will appear here once you make deposits or withdrawals."
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

