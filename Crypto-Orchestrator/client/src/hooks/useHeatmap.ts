/**
 * React Query hooks for market heatmap and correlation data
 */

import { useQuery } from "@tanstack/react-query";
import { marketApi } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

export interface CorrelationMatrixResponse {
  symbols: string[];
  matrix: Record<string, Record<string, number>>;
  calculated_at: string;
}

export interface HeatmapDataResponse {
  data: Record<string, Record<string, number>>;
  metric: string;
  calculated_at: string;
}

/**
 * Hook to fetch correlation matrix for multiple trading pairs
 */
export const useCorrelationMatrix = (
  symbols: string[],
  days: number = 30,
  enabled: boolean = true
) => {
  const { isAuthenticated } = useAuth();

  return useQuery<CorrelationMatrixResponse>({
    queryKey: ["markets", "correlation", "matrix", symbols.sort().join(","), days],
    queryFn: () => marketApi.getCorrelationMatrix(symbols, days),
    enabled: enabled && isAuthenticated && symbols.length >= 2,
    staleTime: 3600000, // 1 hour (correlations don't change frequently)
    retry: 2,
  });
};

/**
 * Hook to fetch heatmap data for multiple trading pairs
 */
export const useHeatmapData = (
  symbols: string[],
  metric: "change_24h" | "volume_24h" | "correlation" = "change_24h",
  days: number = 30,
  enabled: boolean = true
) => {
  const { isAuthenticated } = useAuth();

  return useQuery<HeatmapDataResponse>({
    queryKey: ["markets", "heatmap", symbols.sort().join(","), metric, days],
    queryFn: () => marketApi.getHeatmapData(symbols, metric, days),
    enabled: enabled && isAuthenticated && symbols.length >= 1,
    staleTime: metric === "correlation" ? 3600000 : 300000, // 1 hour for correlation, 5 min for others
    refetchInterval: metric === "correlation" ? false : 60000, // Refresh every minute for change/volume
    retry: 2,
  });
};
