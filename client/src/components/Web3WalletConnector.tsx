/**
 * Web3 Wallet Connector Component
 * Enhanced wallet connector with chain switching and wallet management
 */
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Wallet, LogOut, Copy, Check, AlertCircle, CheckCircle2 } from "lucide-react";
import { useWeb3Wallet } from "@/hooks/useWeb3Wallet";
import { useToast } from "@/hooks/use-toast";
import { useRegisterExternalWallet } from "@/hooks/useApi";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAccount, useSwitchChain } from "wagmi";

const CHAIN_NAMES: Record<number, string> = {
  1: "Ethereum",
  8453: "Base",
  42161: "Arbitrum One",
  137: "Polygon",
  10: "Optimism",
  43114: "Avalanche",
  56: "BNB Chain",
};

interface Web3WalletConnectorProps {
  onWalletRegistered?: (walletAddress: string, chainId: number) => void;
  autoRegister?: boolean;
}

export function Web3WalletConnector({ onWalletRegistered, autoRegister = false }: Web3WalletConnectorProps) {
  const { address, isConnected, isConnecting, connectors, connectWallet, disconnectWallet } = useWeb3Wallet();
  const { chain } = useAccount();
  const { switchChain } = useSwitchChain();
  const chainId = chain?.id;
  const { toast } = useToast();
  const registerWallet = useRegisterExternalWallet();
  const [copied, setCopied] = useState(false);
  const [selectedChain, setSelectedChain] = useState<number>(chainId || 1);
  const [isRegistering, setIsRegistering] = useState(false);

  useEffect(() => {
    if (chainId) {
      setSelectedChain(chainId);
    }
  }, [chainId]);

  const handleCopyAddress = async () => {
    if (!address) return;

    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      toast({
        title: "Address Copied",
        description: "Wallet address copied to clipboard",
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: "Copy Failed",
        description: "Failed to copy address",
        variant: "destructive",
      });
    }
  };

  const handleRegisterWallet = async () => {
    if (!address || !isConnected) {
      toast({
        title: "Wallet Not Connected",
        description: "Please connect your wallet first",
        variant: "destructive",
      });
      return;
    }

    setIsRegistering(true);
    try {
      await registerWallet.mutateAsync({
        wallet_address: address,
        chain_id: selectedChain,
        label: `Web3 Wallet (${CHAIN_NAMES[selectedChain] || `Chain ${selectedChain}`})`,
      });

      toast({
        title: "Wallet Registered",
        description: "Your wallet has been registered for non-custodial trading",
      });

      if (onWalletRegistered) {
        onWalletRegistered(address, selectedChain);
      }
    } catch (error: any) {
      toast({
        title: "Registration Failed",
        description: error.message || "Failed to register wallet",
        variant: "destructive",
      });
    } finally {
      setIsRegistering(false);
    }
  };

  const handleChainSwitch = async (newChainId: number) => {
    setSelectedChain(newChainId);
    if (isConnected && switchChain) {
      try {
        switchChain({ chainId: newChainId });
        toast({
          title: "Chain Switched",
          description: `Switched to ${CHAIN_NAMES[newChainId] || `Chain ${newChainId}`}`,
        });
      } catch (error: any) {
        toast({
          title: "Switch Failed",
          description: error.message || "Failed to switch chain",
          variant: "destructive",
        });
      }
    }
  };

  const formatAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  if (isConnected && address) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-primary" />
            Web3 Wallet Connected
          </CardTitle>
          <CardDescription>Your wallet is connected and ready for non-custodial trading</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Wallet Address */}
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono">
                {formatAddress(address)}
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopyAddress}
                className="h-8 w-8 p-0"
              >
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* Chain Selection */}
          <div>
            <Label>Blockchain Network</Label>
            <Select value={String(selectedChain)} onValueChange={(v) => handleChainSwitch(Number(v))}>
              <SelectTrigger className="mt-2">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(CHAIN_NAMES).map(([id, name]) => (
                  <SelectItem key={id} value={id}>
                    {name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {chainId && chainId !== selectedChain && (
              <Alert className="mt-2">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Wallet is on {CHAIN_NAMES[chainId] || `Chain ${chainId}`}. Switch to match selected chain.
                </AlertDescription>
              </Alert>
            )}
          </div>

          {/* Register Wallet */}
          <Button
            onClick={handleRegisterWallet}
            disabled={isRegistering || registerWallet.isPending}
            className="w-full"
          >
            {isRegistering || registerWallet.isPending ? (
              "Registering..."
            ) : (
              <>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Register Wallet for Trading
              </>
            )}
          </Button>

          {/* Disconnect */}
          <Button
            variant="outline"
            onClick={disconnectWallet}
            className="w-full"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Disconnect Wallet
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wallet className="h-5 w-5" />
          Connect Web3 Wallet
        </CardTitle>
        <CardDescription>
          Connect your MetaMask, WalletConnect, or other Web3 wallet for non-custodial trading
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Available Wallets */}
        <div className="space-y-2">
          {connectors.map((connector: any) => (
            <Button
              key={connector.id}
              variant="outline"
              className="w-full justify-start"
              onClick={() => connectWallet(connector.id)}
              disabled={isConnecting || !connector.ready}
            >
              <Wallet className="h-4 w-4 mr-2" />
              {connector.name}
              {!connector.ready && (
                <Badge variant="secondary" className="ml-auto">
                  Not Available
                </Badge>
              )}
            </Button>
          ))}
        </div>

        {connectors.length === 0 && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <p className="font-semibold mb-1">No Web3 wallets detected</p>
              <p className="text-sm">
                Please install a Web3 wallet browser extension like MetaMask or Coinbase Wallet to use non-custodial trading.
              </p>
            </AlertDescription>
          </Alert>
        )}

        {/* Info */}
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-sm">
            Non-custodial trading means you maintain full control of your funds. Transactions are executed directly from your wallet.
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}
