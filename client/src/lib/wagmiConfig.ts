/**
 * Wagmi Configuration
 * Configures Web3 wallet connections using wagmi v2
 * Supports MetaMask, WalletConnect, Coinbase Wallet, and injected wallets
 */
import { createConfig, http } from "wagmi";
import { mainnet, base, arbitrum, polygon, optimism, avalanche, bsc } from "wagmi/chains";
import { injected, walletConnect, coinbaseWallet } from "wagmi/connectors";
// metaMask connector removed to avoid @metamask/sdk dependency requirement
// The injected() connector already handles MetaMask automatically

// Get WalletConnect project ID from environment (optional, but recommended)
// Get one at: https://cloud.walletconnect.com
const walletConnectProjectId = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID || "";

// Supported chains for DEX trading
// These match the chains supported by our DEX aggregators (0x, OKX, Rubic)
export const supportedChains = [
  mainnet, // Ethereum (chainId: 1)
  base, // Base (chainId: 8453)
  arbitrum, // Arbitrum One (chainId: 42161)
  polygon, // Polygon (chainId: 137)
  optimism, // Optimism (chainId: 10)
  avalanche, // Avalanche (chainId: 43114)
  bsc, // BNB Chain (chainId: 56)
] as const;

// Configure connectors
const connectors = [
  // Injected connector (for any injected wallet like MetaMask, Brave, etc.)
  // This automatically detects MetaMask and other injected wallets
  injected(),
  
  // MetaMask connector (explicit) - optional, only add if @metamask/sdk is available
  // The injected() connector above already handles MetaMask, so this is redundant
  // Keeping commented out to avoid @metamask/sdk dependency requirement
  // metaMask({
  //   dappMetadata: {
  //     name: "CryptoOrchestrator",
  //     url: typeof window !== "undefined" ? window.location.origin : "https://cryptoorchestrator.com",
  //   },
  // }),
  
  // WalletConnect connector (supports 300+ wallets)
  ...(walletConnectProjectId
    ? [
        walletConnect({
          projectId: walletConnectProjectId,
          metadata: {
            name: "CryptoOrchestrator",
            description: "Professional AI-Powered Crypto Trading Platform",
            url: typeof window !== "undefined" ? window.location.origin : "https://cryptoorchestrator.com",
            icons: [
              typeof window !== "undefined"
                ? `${window.location.origin}/favicon.png`
                : "https://cryptoorchestrator.com/favicon.png",
            ],
          },
        }),
      ]
    : []),
  
  // Coinbase Wallet connector
  coinbaseWallet({
    appName: "CryptoOrchestrator",
    appLogoUrl:
      typeof window !== "undefined"
        ? `${window.location.origin}/favicon.png`
        : "https://cryptoorchestrator.com/favicon.png",
  }),
];

// Create wagmi config
export const wagmiConfig = createConfig({
  chains: supportedChains,
  connectors,
  transports: {
    // Use HTTP transport for each chain
    // In production, you might want to use RPC providers like Alchemy or Infura
    [mainnet.id]: http(),
    [base.id]: http(),
    [arbitrum.id]: http(),
    [polygon.id]: http(),
    [optimism.id]: http(),
    [avalanche.id]: http(),
    [bsc.id]: http(),
  },
  // Auto-connect to previously connected wallet
  ssr: false, // Disable SSR for wallet connections
});

// Export chain IDs for easy reference
export const CHAIN_IDS = {
  ETHEREUM: mainnet.id,
  BASE: base.id,
  ARBITRUM: arbitrum.id,
  POLYGON: polygon.id,
  OPTIMISM: optimism.id,
  AVALANCHE: avalanche.id,
  BSC: bsc.id,
} as const;

// Helper to get chain by ID
export function getChainById(chainId: number) {
  return supportedChains.find((chain) => chain.id === chainId);
}

// Helper to get chain name by ID
export function getChainName(chainId: number): string {
  const chain = getChainById(chainId);
  return chain?.name || `Chain ${chainId}`;
}
