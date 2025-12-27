/**
 * Withdrawal Form Component
 * Secure withdrawal interface with 2FA and validation
 */
import { useState } from "react";
import { useCreateWithdrawal, useWithdrawalStatus } from "@/hooks/useApi";
import { walletApi, type WithdrawalStatusResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";

const SUPPORTED_CHAINS = [
  { id: 1, name: "Ethereum", symbol: "ETH" },
  { id: 8453, name: "Base", symbol: "ETH" },
  { id: 42161, name: "Arbitrum One", symbol: "ETH" },
  { id: 137, name: "Polygon", symbol: "MATIC" },
  { id: 10, name: "Optimism", symbol: "ETH" },
  { id: 43114, name: "Avalanche", symbol: "AVAX" },
  { id: 56, name: "BNB Chain", symbol: "BNB" },
];

interface WithdrawalFormProps {
  walletId?: number;
  walletAddress?: string;
  chainId?: number;
  balance?: string;
}

export function WithdrawalForm({ walletId, walletAddress, chainId: initialChainId, balance }: WithdrawalFormProps) {
  const createWithdrawal = useCreateWithdrawal();
  const { toast } = useToast();

  const [chainId, setChainId] = useState<number>(initialChainId || 1);
  const [toAddress, setToAddress] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("ETH");
  const [mfaToken, setMfaToken] = useState("");
  const [txHash, setTxHash] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { data: status } = useWithdrawalStatus(chainId, txHash || "");

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!toAddress.trim()) {
      newErrors.toAddress = "Destination address is required";
    } else if (!/^0x[a-fA-F0-9]{40}$/.test(toAddress.trim())) {
      newErrors.toAddress = "Invalid Ethereum address format";
    }

    if (!amount.trim()) {
      newErrors.amount = "Amount is required";
    } else {
      const numAmount = parseFloat(amount);
      if (isNaN(numAmount) || numAmount <= 0) {
        newErrors.amount = "Amount must be greater than 0";
      } else if (balance && numAmount > parseFloat(balance)) {
        newErrors.amount = "Insufficient balance";
      } else if (numAmount < 0.001) {
        newErrors.amount = "Minimum withdrawal amount is 0.001";
      }
    }

    if (!mfaToken.trim()) {
      newErrors.mfaToken = "2FA token is required for withdrawals";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      if (!walletId) {
        throw new Error("Wallet ID is required");
      }
      
      const result = await walletApi.processWithdrawal(walletId, {
        to_address: toAddress.trim(),
        amount: amount.trim(),
        token_address: currency === "ETH" ? undefined : currency,
        mfa_token: mfaToken.trim(),
      });

      if (result?.transaction_hash) {
        setTxHash(result.transaction_hash);
        toast({
          title: "Withdrawal Initiated",
          description: `Transaction sent: ${result.transaction_hash.slice(0, 10)}...`,
        });
        // Reset form
        setToAddress("");
        setAmount("");
        setMfaToken("");
      } else {
        throw new Error("No transaction hash returned");
      }
    } catch (error: any) {
      toast({
        title: "Withdrawal Failed",
        description: error.message || "Failed to process withdrawal",
        variant: "destructive",
      });
    }
  };

  const chain = SUPPORTED_CHAINS.find((c) => c.id === chainId);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Withdraw Funds</CardTitle>
        <CardDescription>Withdraw funds from your custodial wallet to an external address</CardDescription>
      </CardHeader>
      <CardContent>
        {txHash ? (
          <div className="space-y-4">
            <Alert>
              <CheckCircle2 className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-semibold">Withdrawal Transaction Sent</p>
                  <p className="text-sm">Transaction Hash: {txHash}</p>
                  <div className="flex items-center gap-2 mt-2">
                    {status?.status === "confirmed" ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span className="text-sm text-green-500">Confirmed</span>
                      </>
                    ) : status?.status === "pending" ? (
                      <>
                        <Clock className="h-4 w-4 text-yellow-500" />
                        <span className="text-sm text-yellow-500">Pending</span>
                      </>
                    ) : status?.status === "failed" ? (
                      <>
                        <XCircle className="h-4 w-4 text-red-500" />
                        <span className="text-sm text-red-500">Failed</span>
                      </>
                    ) : (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">Checking status...</span>
                      </>
                    )}
                  </div>
                </div>
              </AlertDescription>
            </Alert>
            <Button
              variant="outline"
              onClick={() => {
                setTxHash(null);
                setToAddress("");
                setAmount("");
                setMfaToken("");
              }}
            >
              New Withdrawal
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="withdrawal-chain">Blockchain</Label>
              <Select value={String(chainId)} onValueChange={(v) => setChainId(Number(v))}>
                <SelectTrigger id="withdrawal-chain">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SUPPORTED_CHAINS.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name} ({c.symbol})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="to-address">Destination Address</Label>
              <Input
                id="to-address"
                placeholder="0x..."
                value={toAddress}
                onChange={(e) => setToAddress(e.target.value)}
                className={errors.toAddress ? "border-destructive" : ""}
              />
              {errors.toAddress && <p className="text-sm text-destructive mt-1">{errors.toAddress}</p>}
            </div>

            <div>
              <Label htmlFor="amount">Amount</Label>
              <div className="flex gap-2">
                <Input
                  id="amount"
                  type="number"
                  step="0.000001"
                  placeholder="0.0"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className={errors.amount ? "border-destructive" : ""}
                />
                <Select value={currency} onValueChange={setCurrency}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ETH">ETH</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {errors.amount && <p className="text-sm text-destructive mt-1">{errors.amount}</p>}
              {balance && (
                <p className="text-xs text-muted-foreground mt-1">
                  Available: {balance} {chain?.symbol || "ETH"}
                </p>
              )}
            </div>

            <div>
              <Label htmlFor="mfa-token">2FA Token</Label>
              <Input
                id="mfa-token"
                type="text"
                placeholder="Enter 2FA code"
                value={mfaToken}
                onChange={(e) => setMfaToken(e.target.value)}
                className={errors.mfaToken ? "border-destructive" : ""}
              />
              {errors.mfaToken && <p className="text-sm text-destructive mt-1">{errors.mfaToken}</p>}
              <p className="text-xs text-muted-foreground mt-1">Required for security</p>
            </div>

            <Button type="submit" disabled={createWithdrawal.isPending} className="w-full">
              {createWithdrawal.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                "Withdraw"
              )}
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
