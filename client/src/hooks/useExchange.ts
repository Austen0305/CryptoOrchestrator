import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/apiClient';
import { useAuth } from '@/hooks/useAuth';

interface ExchangeStatus {
  isConnected: boolean;
  lastUpdate: number;
  exchange: string;
}

interface SystemStatus {
  status: string;
  timestamp: string;
  uptime: number;
  version: string;
  services: Record<string, string>;
}

export function useExchangeStatus() {
  const { isAuthenticated } = useAuth();
  const { data, isLoading, error } = useQuery<ExchangeStatus>({
    queryKey: ['exchange-status'],
    queryFn: async () => {
      const response = await api.get<SystemStatus>('/status');
      return {
        isConnected: response.status === 'running',
        lastUpdate: Date.parse(response.timestamp),
        exchange: 'System',
      } satisfies ExchangeStatus;
    },
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 15000 : false,
    retry: 3,
  });

  return {
    isConnected: data?.isConnected ?? false,
    exchange: data?.exchange ?? 'Unknown',
    isLoading,
    error,
  };
}
