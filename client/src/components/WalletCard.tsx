/**
 * Wallet Card Component
 * Displays wallet information with balance, quick actions, and status
 */
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, Check, Wallet, ExternalLink, RefreshCw, QrCode, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useWalletBalance, useRefreshWalletBalances } from "@/hooks/useApi";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { DepositModal } from "@/components/DepositModal";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import logger from "@/lib/logger";

const CHAIN_NAMES: Record<number, string> = {
  1: "Ethereum",
  8453: "Base",
  42161: "Arbitrum One",
  137: "Polygon",
  10: "Optimism",
  43114: "Avalanche",
  56: "BNB Chain",
};

interface WalletCardProps {
  wallet: {
    wallet_id: number;
    address: string;
    chain_id: number;
    wallet_type: "custodial" | "external";
    label?: string;
    is_verified: boolean;
    is_active: boolean;
    balance?: any;
    last_balance_update?: string;
  };
  onCopy?: (text: string, walletId: number) => void;
  copiedAddress?: string | null;
}

function WalletCardContent({ wallet, onCopy, copiedAddress }: WalletCardProps) {
  const { toast } = useToast();
  const [showDeposit, setShowDeposit] = useState(false);
  const [showWithdraw, setShowWithdraw] = useState(false);
  
  const { data: balanceData, isLoading: balanceLoading, refetch: refetchBalance } = useWalletBalance(
    wallet.wallet_id,
    undefined, // token_address - None for ETH
  ) || { data: null, isLoading: false, refetch: async () => {} };
  
  const refreshBalances = useRefreshWalletBalances();

  const handleCopy = () => {
    if (onCopy) {
      onCopy(wallet.address, wallet.wallet_id);
    } else {
      navigator.clipboard.writeText(wallet.address);
      toast({
        title: "Copied",
        description: "Address copied to clipboard",
      });
    }
  };

  const handleRefresh = async () => {
    try {
      await refreshBalances.mutateAsync();
      await refetchBalance();
      toast({
        title: "Balance Refreshed",
        description: "Wallet balance updated",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to refresh balance",
        variant: "destructive",
      });
    }
  };

  // Parse balance from wallet.balance (could be JSON string or object)
  const walletBalance = wallet.balance 
    ? (typeof wallet.balance === "string" ? JSON.parse(wallet.balance) : wallet.balance)
    : {};
  const walletBalanceETH = walletBalance && typeof walletBalance === 'object' && 'ETH' in walletBalance
    ? (walletBalance.ETH as string | number) ?? "0.0"
    : "0.0";
  const balance = balanceData?.balance || walletBalanceETH || "0.0";
  const chainName = CHAIN_NAMES[wallet.chain_id] || `Chain ${wallet.chain_id}`;
  const isCopied = copiedAddress === String(wallet.wallet_id);

  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <Wallet className="h-5 w-5 text-primary" />
              {wallet.label || `${chainName} Wallet`}
            </CardTitle>
            <CardDescription className="mt-1">
              {wallet.wallet_type === "custodial" ? "Platform-managed" : "Your wallet"}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            {wallet.wallet_type === "custodial" && (
              <Badge variant="secondary" className="bg-blue-500/10 text-blue-500 border-blue-500/20">
                Custodial
              </Badge>
            )}
            {wallet.wallet_type === "external" && (
              <Badge variant="outline">
                External
              </Badge>
            )}
            {wallet.is_verified && (
              <Badge variant="default" className="bg-green-500">
                Verified
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Balance */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Balance</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={balanceLoading || refreshBalances.isPending}
            >
              <RefreshCw className={`h-4 w-4 ${balanceLoading || refreshBalances.isPending ? "animate-spin" : ""}`} />
            </Button>
          </div>
          {balanceLoading ? (
            <LoadingSkeleton className="h-8 w-32" />
          ) : (
            <div className="text-2xl font-bold">
              {parseFloat(String(balance)).toFixed(6)} ETH
            </div>
          )}
          {wallet.last_balance_update && (
            <p className="text-xs text-muted-foreground mt-1">
              Updated {new Date(wallet.last_balance_update).toLocaleString()}
            </p>
          )}
        </div>

        {/* Address */}
        <div>
          <div className="flex items-center justify-between gap-2">
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground mb-1">Address</p>
              <p className="text-sm font-mono truncate">{wallet.address}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="shrink-0"
            >
              {isCopied ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2 pt-2 border-t">
          {wallet.wallet_type === "custodial" && (
            <>
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => setShowDeposit(true)}
              >
                <ArrowDownRight className="h-4 w-4 mr-2" />
                Deposit
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => setShowWithdraw(true)}
              >
                <ArrowUpRight className="h-4 w-4 mr-2" />
                Withdraw
              </Button>
            </>
          )}
          {wallet.wallet_type === "external" && (
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => window.open(`https://etherscan.io/address/${wallet.address}`, "_blank")}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View on Explorer
            </Button>
          )}
        </div>
      </CardContent>

      {/* Deposit Modal */}
      {showDeposit && wallet.wallet_type === "custodial" && (
        <DepositModal
          walletId={wallet.wallet_id}
          address={wallet.address}
          chainId={wallet.chain_id}
          chainName={chainName}
          open={showDeposit}
          onOpenChange={setShowDeposit}
        />
      )}
    </Card>
  );
}

export function WalletCard({ wallet, onCopy, copiedAddress }: WalletCardProps) {
  return (
    <ErrorBoundary
      fallback={
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Error loading wallet card</p>
          </CardContent>
        </Card>
      }
      onError={(error, errorInfo) => {
        logger.error("WalletCard error", { error, errorInfo });
      }}
    >
      <WalletCardContent wallet={wallet} onCopy={onCopy} copiedAddress={copiedAddress} />
    </ErrorBoundary>
  );
}
