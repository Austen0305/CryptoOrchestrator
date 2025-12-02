import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/apiClient';
import { useAuth } from '@/hooks/useAuth';
import type { TradingBot } from '@/types';

export function useBots() {
  const queryClient = useQueryClient();

  const { isAuthenticated } = useAuth();

  const { data: bots, isLoading, error } = useQuery<TradingBot[]>({
    queryKey: ['bots'],
    queryFn: async () => {
      const response = await api.get<TradingBot[]>('/bots');
      return response;
    },
    enabled: isAuthenticated, // Do not query until authenticated
    refetchInterval: isAuthenticated ? 10000 : false,
    retry: false, // Avoid noisy retries for auth-related failures
  });

  const createBot = useMutation({
    mutationFn: async (botData: Partial<TradingBot>) => {
      return await api.post<TradingBot>('/bots', botData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });

  const updateBot = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<TradingBot> }) => {
      return await api.put<TradingBot>(`/bots/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });

  const deleteBot = useMutation({
    mutationFn: async (id: number) => {
      return await api.delete(`/bots/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });

  const startBot = useMutation({
    mutationFn: async (id: number) => {
      return await api.post(`/bots/${id}/start`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });

  const stopBot = useMutation({
    mutationFn: async (id: number) => {
      return await api.post(`/bots/${id}/stop`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] });
    },
  });

  return {
    bots: bots ?? [],
    isLoading,
    error,
    createBot,
    updateBot,
    deleteBot,
    startBot,
    stopBot,
  };
}
