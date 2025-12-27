/**
 * Wallet Connection Component
 * UI for connecting Web3 wallets (MetaMask, WalletConnect, etc.)
 */
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Wallet, LogOut, Copy, Check } from "lucide-react";
import { useWeb3Wallet } from "@/hooks/useWeb3Wallet";
import { toast } from "@/components/ui/use-toast";

export function WalletConnect() {
  const { address, isConnected, isConnecting, connectors, connectWallet, disconnectWallet } = useWeb3Wallet();
  const [copied, setCopied] = useState(false);

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

  const formatAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  if (isConnected && address) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            Wallet Connected
          </CardTitle>
          <CardDescription>Your Web3 wallet is connected</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
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
          Connect Wallet
        </CardTitle>
        <CardDescription>Connect your Web3 wallet to trade on DEX</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
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
            {!connector.ready && " (Not Available)"}
          </Button>
        ))}
        {connectors.length === 0 && (
          <div className="text-center py-4 text-muted-foreground">
            <p>No wallets available</p>
            <p className="text-sm mt-2">Please install MetaMask or another Web3 wallet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
