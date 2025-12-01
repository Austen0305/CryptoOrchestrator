import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { ArrowDownUp, Download, Upload, Copy, CheckCircle2 } from "lucide-react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { formatCurrencyInput, validateAmount } from "@/lib/validation";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";

interface DepositAddress {
  currency: string;
  address: string;
  network: string;
  qr_code_url: string;
}

export function CryptoTransfer() {
  const { toast } = useToast();
  const [selectedCurrency, setSelectedCurrency] = useState("BTC");
  const [selectedPlatform, setSelectedPlatform] = useState("binance");
  const [transferAmount, setTransferAmount] = useState("");
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [withdrawAddress, setWithdrawAddress] = useState("");
  const [selectedNetwork, setSelectedNetwork] = useState<string>("");

  const { data: depositAddress, isLoading: loadingAddress, error: addressError, refetch: refetchAddress } = useQuery({
    queryKey: ["deposit-address", selectedCurrency, selectedNetwork],
    queryFn: async () => {
      return await apiRequest<DepositAddress>(
        `/api/crypto-transfer/deposit-address/${selectedCurrency}?network=${selectedNetwork || ""}`,
        { method: "GET" }
      );
    },
    enabled: !!selectedCurrency,
    retry: 2,
  });

  const initiateTransfer = useMutation({
    mutationFn: async (data: {
      currency: string;
      amount: number;
      source_platform: string;
      network?: string;
    }) => {
      return await apiRequest("/api/crypto-transfer/initiate", {
        method: "POST",
        body: data
      });
    },
    onSuccess: (data) => {
      toast({
        title: "Transfer Initiated",
        description: `Follow the instructions to complete your ${data.currency} transfer`
      });
    }
  });

  const withdrawCrypto = useMutation({
    mutationFn: async (data: {
      currency: string;
      amount: number;
      destination_address: string;
      network?: string;
    }) => {
      return await apiRequest("/api/crypto-transfer/withdraw", {
        method: "POST",
        body: data
      });
    },
    onSuccess: (data) => {
      toast({
        title: "Withdrawal Initiated",
        description: `Your ${data.currency} withdrawal is being processed`
      });
      setWithdrawAmount("");
      setWithdrawAddress("");
    }
  });

  const handleInitiateTransfer = async () => {
    const amount = parseFloat(transferAmount);
    
    const validation = validateAmount(amount, 0.00000001);
    if (!validation.valid) {
      toast({
        title: "Invalid Amount",
        description: validation.error,
        variant: "destructive"
      });
      return;
    }

    try {
      await initiateTransfer.mutateAsync({
        currency: selectedCurrency,
        amount,
        source_platform: selectedPlatform,
        network: selectedNetwork || undefined
      });
      setTransferAmount("");
    } catch (error) {
      toast({
        title: "Transfer Failed",
        description: error instanceof Error ? error.message : "Failed to initiate transfer",
        variant: "destructive"
      });
    }
  };

  const handleWithdraw = async () => {
    const amount = parseFloat(withdrawAmount);
    
    const validation = validateAmount(amount, 0.00000001);
    if (!validation.valid) {
      toast({
        title: "Invalid Amount",
        description: validation.error,
        variant: "destructive"
      });
      return;
    }

    if (!withdrawAddress || withdrawAddress.length < 10) {
      toast({
        title: "Invalid Address",
        description: "Please enter a valid destination address",
        variant: "destructive"
      });
      return;
    }

    try {
      await withdrawCrypto.mutateAsync({
        currency: selectedCurrency,
        amount,
        destination_address: withdrawAddress,
        network: selectedNetwork || undefined
      });
    } catch (error) {
      toast({
        title: "Withdrawal Failed",
        description: error instanceof Error ? error.message : "Failed to process withdrawal",
        variant: "destructive"
      });
    }
  };

  const copyAddress = () => {
    if (depositAddress?.address) {
      navigator.clipboard.writeText(depositAddress.address);
      toast({
        title: "Address Copied",
        description: "Deposit address copied to clipboard"
      });
    }
  };

  const platforms = [
    { value: "binance", label: "Binance" },
    { value: "coinbase", label: "Coinbase" },
    { value: "kraken", label: "Kraken" },
    { value: "external_wallet", label: "External Wallet" }
  ];

  const currencies = ["BTC", "ETH", "USDT", "SOL", "ADA", "DOT", "ATOM"];
  const networks = {
    BTC: ["default"],
    ETH: ["ERC20", "default"],
    USDT: ["ERC20", "TRC20", "BEP20"],
    SOL: ["default"],
    ADA: ["default"],
    DOT: ["default"],
    ATOM: ["default"]
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Crypto Transfers</CardTitle>
        <CardDescription>Transfer crypto from other platforms or withdraw to external wallets</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="deposit" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="deposit">
              <Upload className="h-4 w-4 mr-2" />
              Deposit from Platform
            </TabsTrigger>
            <TabsTrigger value="withdraw">
              <Download className="h-4 w-4 mr-2" />
              Withdraw to Wallet
            </TabsTrigger>
          </TabsList>

          <TabsContent value="deposit" className="space-y-4">
            <div className="space-y-4">
              <div>
                <Label>Source Platform</Label>
                <Select value={selectedPlatform} onValueChange={setSelectedPlatform}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {platforms.map((platform) => (
                      <SelectItem key={platform.value} value={platform.value}>
                        {platform.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Currency</Label>
                <Select value={selectedCurrency} onValueChange={setSelectedCurrency}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {currencies.map((currency) => (
                      <SelectItem key={currency} value={currency}>
                        {currency}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {networks[selectedCurrency as keyof typeof networks]?.length > 1 && (
                <div>
                  <Label>Network</Label>
                  <Select value={selectedNetwork} onValueChange={setSelectedNetwork}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select network" />
                    </SelectTrigger>
                    <SelectContent>
                      {networks[selectedCurrency as keyof typeof networks].map((network) => (
                        <SelectItem key={network} value={network}>
                          {network}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div>
                <Label>Amount</Label>
                <Input
                  type="text"
                  placeholder="0.00"
                  value={transferAmount}
                  onChange={(e) => {
                    const formatted = formatCurrencyInput(e.target.value);
                    setTransferAmount(formatted);
                  }}
                />
              </div>

              {loadingAddress ? (
                <LoadingSkeleton count={2} className="h-12 w-full mb-2" />
              ) : addressError ? (
                <ErrorRetry
                  title="Failed to load deposit address"
                  message={addressError instanceof Error ? addressError.message : "An unexpected error occurred."}
                  onRetry={() => refetchAddress()}
                  error={addressError as Error}
                />
              ) : depositAddress ? (
                <div className="p-4 border rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Deposit Address</Label>
                    <Button variant="ghost" size="sm" onClick={copyAddress}>
                      <Copy className="h-4 w-4 mr-2" />
                      Copy
                    </Button>
                  </div>
                  <div className="p-3 bg-muted rounded font-mono text-sm break-all">
                    {depositAddress.address}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Network: {depositAddress.network}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    ⚠️ Make sure to use the correct network or funds may be lost
                  </p>
                </div>
              ) : null}

              <Button onClick={handleInitiateTransfer} className="w-full" disabled={!transferAmount}>
                Initiate Transfer
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="withdraw" className="space-y-4">
            <div className="space-y-4">
              <div>
                <Label>Currency</Label>
                <Select value={selectedCurrency} onValueChange={setSelectedCurrency}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {currencies.map((currency) => (
                      <SelectItem key={currency} value={currency}>
                        {currency}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {networks[selectedCurrency as keyof typeof networks]?.length > 1 && (
                <div>
                  <Label>Network</Label>
                  <Select value={selectedNetwork} onValueChange={setSelectedNetwork}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select network" />
                    </SelectTrigger>
                    <SelectContent>
                      {networks[selectedCurrency as keyof typeof networks].map((network) => (
                        <SelectItem key={network} value={network}>
                          {network}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div>
                <Label>Destination Address</Label>
                <Input
                  placeholder="Enter wallet address"
                  value={withdrawAddress}
                  onChange={(e) => setWithdrawAddress(e.target.value)}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  ⚠️ Double-check the address. Transactions cannot be reversed.
                </p>
              </div>

              <div>
                <Label>Amount</Label>
                <Input
                  type="text"
                  placeholder="0.00"
                  value={withdrawAmount}
                  onChange={(e) => {
                    const formatted = formatCurrencyInput(e.target.value);
                    setWithdrawAmount(formatted);
                  }}
                />
              </div>

              <Button
                onClick={handleWithdraw}
                className="w-full"
                disabled={!withdrawAmount || !withdrawAddress}
                variant="destructive"
              >
                <Download className="h-4 w-4 mr-2" />
                Withdraw Crypto
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

