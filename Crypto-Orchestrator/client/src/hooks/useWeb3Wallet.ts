/**
 * Web3 Wallet Hook
 * Manages wallet connections using wagmi
 * Supports MetaMask, WalletConnect, Coinbase Wallet, and more
 */
import { useAccount, useConnect, useDisconnect, useSignMessage, type Connector } from "wagmi";
import { useState, useCallback } from "react";
import { toast } from "@/components/ui/use-toast";

// Type guard to check if wagmi is available
function isWagmiAvailable(): boolean {
  try {
    return typeof window !== "undefined" && "ethereum" in window;
  } catch {
    return false;
  }
}

export interface WalletConnection {
  address: string | undefined;
  isConnected: boolean;
  isConnecting: boolean;
  connector: Connector | undefined;
}

export function useWeb3Wallet() {
  const { address, isConnected, connector } = useAccount();
  const { connect, connectors, isPending: isConnecting } = useConnect();
  const { disconnect } = useDisconnect();
  const { signMessageAsync } = useSignMessage();
  const [isSigning, setIsSigning] = useState(false);

  const connectWallet = useCallback(
    async (connectorId?: string) => {
      try {
        const targetConnector = connectorId
          ? connectors.find((c: any) => c.id === connectorId)
          : connectors[0]; // Default to first available

        if (!targetConnector) {
          toast({
            title: "No Wallet Available",
            description: "Please install a Web3 wallet like MetaMask",
            variant: "destructive",
          });
          return;
        }

        await connect({ connector: targetConnector });
        toast({
          title: "Wallet Connected",
          description: `Connected to ${targetConnector.name}`,
        });
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : "Failed to connect wallet";
        toast({
          title: "Connection Failed",
          description: errorMessage,
          variant: "destructive",
        });
      }
    },
    [connect, connectors]
  );

  const disconnectWallet = useCallback(() => {
    disconnect();
    toast({
      title: "Wallet Disconnected",
      description: "Your wallet has been disconnected",
    });
  }, [disconnect]);

  const signMessage = useCallback(
    async (message: string): Promise<string | null> => {
      if (!isConnected || !address) {
        toast({
          title: "Wallet Not Connected",
          description: "Please connect your wallet first",
          variant: "destructive",
        });
        return null;
      }

      try {
        setIsSigning(true);
        const signature = await signMessageAsync({ message });
        return signature;
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : "Failed to sign message";
        toast({
          title: "Signing Failed",
          description: errorMessage,
          variant: "destructive",
        });
        return null;
      } finally {
        setIsSigning(false);
      }
    },
    [isConnected, address, signMessageAsync]
  );

  return {
    address,
    isConnected,
    isConnecting,
    isSigning,
    connector,
    connectors,
    connectWallet,
    disconnectWallet,
    signMessage,
  };
}
