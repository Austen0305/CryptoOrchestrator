/**
 * Wallet Management Page
 * Manage custodial and external wallets, view balances, and get deposit addresses
 */
import { useState } from "react";
import { useWallets, useCreateCustodialWallet, useRegisterExternalWallet, useDepositAddress } from "@/hooks/useApi";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Wallet, Plus, Copy, Check, QrCode, ExternalLink } from "lucide-react";
import { Web3WalletConnector } from "@/components/Web3WalletConnector";
import { useToast } from "@/hooks/use-toast";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { useEffect, useRef } from "react";
import { WithdrawalForm } from "@/components/WithdrawalForm";
import { WalletCard } from "@/components/WalletCard";
import { EnhancedErrorBoundary } from "@/components/EnhancedErrorBoundary";
import { TransactionHistoryTable } from "@/components/TransactionHistoryTable";
import logger from "@/lib/logger";

// Chain configuration
const SUPPORTED_CHAINS = [
  { id: 1, name: "Ethereum", symbol: "ETH" },
  { id: 8453, name: "Base", symbol: "ETH" },
  { id: 42161, name: "Arbitrum One", symbol: "ETH" },
  { id: 137, name: "Polygon", symbol: "MATIC" },
  { id: 10, name: "Optimism", symbol: "ETH" },
  { id: 43114, name: "Avalanche", symbol: "AVAX" },
  { id: 56, name: "BNB Chain", symbol: "BNB" },
];

function WalletsContent() {
  const { data: wallets, isLoading, error } = useWallets();
  const createCustodialWallet = useCreateCustodialWallet();
  const registerExternalWallet = useRegisterExternalWallet();
  const { toast } = useToast();

  const [showCreateCustodial, setShowCreateCustodial] = useState(false);
  const [showRegisterExternal, setShowRegisterExternal] = useState(false);
  const [selectedChain, setSelectedChain] = useState<number>(1);
  const [externalAddress, setExternalAddress] = useState("");
  const [externalLabel, setExternalLabel] = useState("");
  const [copiedAddress, setCopiedAddress] = useState<string | null>(null);

  const handleCreateCustodial = async () => {
    try {
      await createCustodialWallet.mutateAsync(selectedChain);
      toast({
        title: "Wallet Created",
        description: `Custodial wallet created for ${SUPPORTED_CHAINS.find((c) => c.id === selectedChain)?.name}`,
      });
      setShowCreateCustodial(false);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to create custodial wallet",
        variant: "destructive",
      });
    }
  };

  const handleRegisterExternal = async () => {
    if (!externalAddress.trim()) {
      toast({
        title: "Error",
        description: "Please enter a wallet address",
        variant: "destructive",
      });
      return;
    }

    try {
      await registerExternalWallet.mutateAsync({
        wallet_address: externalAddress.trim(),
        chain_id: selectedChain,
        label: externalLabel.trim() || undefined,
      });
      toast({
        title: "Wallet Registered",
        description: "External wallet registered successfully",
      });
      setShowRegisterExternal(false);
      setExternalAddress("");
      setExternalLabel("");
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to register external wallet",
        variant: "destructive",
      });
    }
  };

  const copyToClipboard = (text: string, walletId: number) => {
    navigator.clipboard.writeText(text);
    setCopiedAddress(`${walletId}`);
    setTimeout(() => setCopiedAddress(null), 2000);
    toast({
      title: "Copied",
      description: "Address copied to clipboard",
    });
  };

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight" data-testid="wallets-page">Wallets</h1>
          <p className="text-muted-foreground mt-2">Manage your blockchain wallets</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">Error loading wallets. Please try again.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const custodialWallets = (wallets && Array.isArray(wallets) ? wallets.filter((w: any) => w.wallet_type === "custodial") : []) || [];
  const externalWallets = (wallets && Array.isArray(wallets) ? wallets.filter((w: any) => w.wallet_type === "external") : []) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight" data-testid="wallets-page">Wallets</h1>
          <p className="text-muted-foreground mt-2">Manage your blockchain wallets for deposits and trading</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={showCreateCustodial} onOpenChange={setShowCreateCustodial}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Custodial Wallet
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Custodial Wallet</DialogTitle>
                <DialogDescription>Create a new custodial wallet for deposits and trading on a specific chain.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="chain-select">Blockchain</Label>
                  <Select value={String(selectedChain)} onValueChange={(v) => setSelectedChain(Number(v))}>
                    <SelectTrigger id="chain-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SUPPORTED_CHAINS.map((chain) => (
                        <SelectItem key={chain.id} value={String(chain.id)}>
                          {chain.name} ({chain.symbol})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleCreateCustodial} disabled={createCustodialWallet.isPending} className="w-full">
                  {createCustodialWallet.isPending ? "Creating..." : "Create Wallet"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={showRegisterExternal} onOpenChange={setShowRegisterExternal}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <ExternalLink className="h-4 w-4 mr-2" />
                Connect Web3 Wallet
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle>Connect Web3 Wallet</DialogTitle>
                <DialogDescription>
                  Connect your MetaMask, WalletConnect, or other Web3 wallet for non-custodial trading
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <Web3WalletConnector
                  onWalletRegistered={(address, chainId) => {
                    setShowRegisterExternal(false);
                    toast({
                      title: "Wallet Connected",
                      description: "Your Web3 wallet has been registered",
                    });
                  }}
                />
                
                {/* Manual Entry Option */}
                <div className="pt-4 border-t">
                  <p className="text-sm text-muted-foreground mb-4">Or enter wallet address manually:</p>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="external-chain-select">Blockchain</Label>
                      <Select value={String(selectedChain)} onValueChange={(v) => setSelectedChain(Number(v))}>
                        <SelectTrigger id="external-chain-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {SUPPORTED_CHAINS.map((chain) => (
                            <SelectItem key={chain.id} value={String(chain.id)}>
                              {chain.name} ({chain.symbol})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="external-address">Wallet Address</Label>
                      <Input
                        id="external-address"
                        placeholder="0x..."
                        value={externalAddress}
                        onChange={(e) => setExternalAddress(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="external-label">Label (Optional)</Label>
                      <Input
                        id="external-label"
                        placeholder="My MetaMask Wallet"
                        value={externalLabel}
                        onChange={(e) => setExternalLabel(e.target.value)}
                      />
                    </div>
                    <Button onClick={handleRegisterExternal} disabled={registerExternalWallet.isPending} className="w-full">
                      {registerExternalWallet.isPending ? "Registering..." : "Register Wallet"}
                    </Button>
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Custodial Wallets */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Custodial Wallets</h2>
        {custodialWallets.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <p className="text-muted-foreground text-center py-8">No custodial wallets yet. Create one to start depositing funds.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {custodialWallets.map((wallet: any) => (
              <WalletCard key={wallet.wallet_id} wallet={wallet} onCopy={copyToClipboard} copiedAddress={copiedAddress} />
            ))}
          </div>
        )}
      </div>

      {/* External Wallets */}
      <div>
        <h2 className="text-xl font-semibold mb-4">External Wallets</h2>
        {externalWallets.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <p className="text-muted-foreground text-center py-8">No external wallets registered. Register one for non-custodial trading.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {externalWallets.map((wallet: any) => (
              <WalletCard key={wallet.wallet_id} wallet={wallet} onCopy={copyToClipboard} copiedAddress={copiedAddress} />
            ))}
          </div>
        )}
      </div>

      {/* Transaction History */}
      {custodialWallets.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Transaction History</h2>
          <Tabs defaultValue={custodialWallets[0]?.wallet_id?.toString() || "0"}>
            <TabsList>
              {custodialWallets.map((wallet: any) => (
                <TabsTrigger key={wallet.wallet_id} value={wallet.wallet_id.toString()}>
                  {wallet.label || `Wallet ${wallet.wallet_id}`}
                </TabsTrigger>
              ))}
            </TabsList>
            {custodialWallets.map((wallet: any) => (
              <TabsContent key={wallet.wallet_id} value={wallet.wallet_id.toString()}>
                <TransactionHistoryTable walletId={wallet.wallet_id} />
              </TabsContent>
            ))}
          </Tabs>
        </div>
      )}

      {/* Withdrawals */}
      {custodialWallets.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Withdraw Funds</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {custodialWallets.map((wallet: any) => {
              const chain = SUPPORTED_CHAINS.find((c) => c.id === wallet.chain_id);
              const balance = wallet.balance
                ? typeof wallet.balance === "string"
                  ? JSON.parse(wallet.balance).ETH || "0.0"
                  : wallet.balance.ETH || "0.0"
                : "0.0";
              return (
                <WithdrawalForm
                  key={wallet.wallet_id}
                  walletId={wallet.wallet_id}
                  walletAddress={wallet.address}
                  chainId={wallet.chain_id}
                  balance={balance}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function DepositQRCode({ address }: { address: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (canvasRef.current && address) {
      // Use dynamic import for qrcode to avoid SSR issues
      import("qrcode").then((QRCode) => {
        if (!canvasRef.current) return;
        QRCode.default.toCanvas(canvasRef.current, address, {
          width: 256,
          margin: 2,
        });
      });
    }
  }, [address]);

  return <canvas ref={canvasRef} className="rounded" />;
}

// WalletCard component moved to @/components/WalletCard.tsx
// Keeping this for backward compatibility if needed, but using imported component
function LegacyWalletCard({ wallet, onCopy, copiedAddress }: { wallet: any; onCopy: (text: string, id: number) => void; copiedAddress: string | null }) {
  const chain = SUPPORTED_CHAINS.find((c) => c.id === wallet.chain_id);
  const [showQR, setShowQR] = useState(false);
  const { data: depositAddress } = useDepositAddress(wallet.chain_id);

  const address = wallet.address || (depositAddress && typeof depositAddress === 'object' && 'address' in depositAddress ? String((depositAddress as { address?: string }).address || '') : '') || "";
  const isCopied = copiedAddress === String(wallet.wallet_id);

  // Parse balance from JSON
  const balance = wallet.balance ? (typeof wallet.balance === "string" ? JSON.parse(wallet.balance) : wallet.balance) : null;
  const ethBalance = balance?.ETH || "0.0";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            {wallet.label || `${chain?.name || `Chain ${wallet.chain_id}`} Wallet`}
          </CardTitle>
          <span className={`text-xs px-2 py-1 rounded ${wallet.wallet_type === "custodial" ? "bg-primary/10 text-primary" : "bg-secondary text-secondary-foreground"}`}>
            {wallet.wallet_type === "custodial" ? "Custodial" : "External"}
          </span>
        </div>
        <CardDescription>{chain?.name || `Chain ${wallet.chain_id}`}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label className="text-xs text-muted-foreground">Address</Label>
          <div className="flex items-center gap-2 mt-1">
            <code className="text-sm flex-1 truncate bg-muted px-2 py-1 rounded">{address}</code>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => onCopy(address, wallet.wallet_id)}
              title="Copy address"
            >
              {isCopied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </Button>
            {wallet.wallet_type === "custodial" && (
              <Dialog open={showQR} onOpenChange={setShowQR}>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8" title="Show QR code">
                    <QrCode className="h-4 w-4" />
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Deposit Address QR Code</DialogTitle>
                    <DialogDescription>Scan this QR code to send funds to your custodial wallet</DialogDescription>
                  </DialogHeader>
                  <div className="flex flex-col items-center space-y-4">
                    <DepositQRCode address={address} />
                    <code className="text-sm bg-muted px-4 py-2 rounded break-all">{address}</code>
                  </div>
                </DialogContent>
              </Dialog>
            )}
          </div>
        </div>

        {wallet.wallet_type === "custodial" && (
          <div>
            <Label className="text-xs text-muted-foreground">Balance</Label>
            <p className="text-lg font-semibold mt-1">
              {ethBalance} {chain?.symbol || "ETH"}
            </p>
            {wallet.last_balance_update && (
              <p className="text-xs text-muted-foreground mt-1">
                Updated: {new Date(wallet.last_balance_update).toLocaleString()}
              </p>
            )}
          </div>
        )}

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {wallet.is_verified && <span className="text-green-500">✓ Verified</span>}
          {wallet.is_active ? (
            <span className="text-green-500">● Active</span>
          ) : (
            <span className="text-muted-foreground">○ Inactive</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function Wallets() {
  return (
    <EnhancedErrorBoundary
      onError={(error, errorInfo) => {
        logger.error("Wallets page error", { error, errorInfo });
      }}
    >
      <WalletsContent />
    </EnhancedErrorBoundary>
  );
}
