// Type declarations for wagmi v3
declare module 'wagmi' {
  import type { Config } from '@wagmi/core';
  import { createConfig, http } from '@wagmi/core';
  
  export interface WagmiProviderProps {
    config: Config;
    children: React.ReactNode;
  }
  
  export interface Connector {
    id: string;
    name: string;
  }
  
  export function WagmiProvider(props: WagmiProviderProps): JSX.Element;
  export function useAccount(): { 
    address?: string; 
    isConnected: boolean; 
    chain?: any;
    connector?: Connector;
  };
  export function useConnect(): { 
    connect: (args: any) => void; 
    connectors: any[];
    isPending: boolean;
  };
  export function useDisconnect(): { disconnect: () => void };
  export function useSwitchChain(): { switchChain: (args: any) => void };
  export function useSignMessage(): { 
    signMessage: (args: any) => Promise<string>;
    signMessageAsync: (args: any) => Promise<string>;
  };
  export { createConfig, http };
  export type { Config, Connector };
}

declare module 'wagmi/chains' {
  export * from 'viem/chains';
}

declare module 'wagmi/connectors' {
  export function injected(): any;
  export function metaMask(options?: any): any;
  export function walletConnect(options?: any): any;
  export function coinbaseWallet(options?: any): any;
}

