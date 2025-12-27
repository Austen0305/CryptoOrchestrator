import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/apiClient';
import { useAuth } from '@/hooks/useAuth';

interface BlockchainStatus {
  isConnected: boolean;
  lastUpdate: number;
  blockchain: string;
}

interface SystemStatus {
  status: string;
  timestamp: string;
  uptime: number;
  version: string;
  services: Record<string, string>;
  blockchainTrading?: string;
}

/**
 * Hook for checking blockchain/DEX trading status
 * Replaces the old exchange status hook
 */
export function useExchangeStatus() {
  const { isAuthenticated } = useAuth();
  const { data, isLoading, error } = useQuery<BlockchainStatus>({
    queryKey: ['blockchain-status'],
    queryFn: async () => {
      const response = await api.get<SystemStatus>('/status');
      return {
        isConnected: response.status === 'running' && response.blockchainTrading === 'active',
        lastUpdate: Date.parse(response.timestamp),
        blockchain: 'Blockchain',
      } satisfies BlockchainStatus;
    },
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000, // 2 minutes for status data
    refetchInterval: isAuthenticated ? 15000 : false, // Poll every 15 seconds when authenticated
    retry: 3,
  });

  return {
    isConnected: data?.isConnected ?? false,
    exchange: data?.blockchain ?? 'Blockchain',
    isLoading,
    error,
  };
}
