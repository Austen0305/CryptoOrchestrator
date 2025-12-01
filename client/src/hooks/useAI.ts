import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

// AI Analysis hooks

export const useBotAIAnalysis = (botId: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["ai", "bot", botId, "analysis"],
    queryFn: async () => {
      return await apiRequest(`/api/ai-analysis/bot/${botId}`, { method: "GET" });
    },
    enabled: isAuthenticated && !!botId,
    refetchInterval: isAuthenticated ? 60000 : false, // 1 minute
  });
};

export const useMarketSentiment = (symbol: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["ai", "sentiment", symbol],
    queryFn: async () => {
      return await apiRequest(`/api/ai-analysis/symbol/${symbol}/sentiment`, { method: "GET" });
    },
    enabled: isAuthenticated && !!symbol,
    refetchInterval: isAuthenticated ? 30000 : false, // 30 seconds
  });
};

