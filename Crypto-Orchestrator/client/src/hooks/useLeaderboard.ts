import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

export interface LeaderboardEntry {
  user_id: number;
  username: string;
  email: string;
  total_pnl: number;
  win_rate: number;
  profit_factor: number;
  sharpe_ratio: number;
  total_trades: number;
  avg_win: number;
  avg_loss: number;
}

export interface LeaderboardResponse {
  leaderboard: LeaderboardEntry[];
  metric: string;
  period: string;
  mode: string;
  user_rank?: LeaderboardEntry & { rank: number };
}

export const useLeaderboard = (
  metric: string = "total_pnl",
  period: string = "all_time",
  mode: string = "paper",
  limit: number = 100
) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["leaderboard", metric, period, mode, limit],
    queryFn: async () => {
      const params = new URLSearchParams({
        metric,
        period,
        mode,
        limit: limit.toString(),
      });
      return await apiRequest<LeaderboardResponse>(`/api/leaderboard?${params}`, { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 60000, // 1 minute
    refetchInterval: isAuthenticated ? 300000 : false, // 5 minutes when authenticated
  });
};

export const useMyRank = (
  metric: string = "total_pnl",
  period: string = "all_time",
  mode: string = "paper"
) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["leaderboard", "my-rank", metric, period, mode],
    queryFn: async () => {
      const params = new URLSearchParams({
        metric,
        period,
        mode,
      });
      return await apiRequest<LeaderboardEntry & { rank: number }>(`/api/leaderboard/my-rank?${params}`, { method: "GET" });
    },
    enabled: isAuthenticated,
    staleTime: 60000, // 1 minute
    refetchInterval: isAuthenticated ? 300000 : false, // 5 minutes when authenticated
  });
};

