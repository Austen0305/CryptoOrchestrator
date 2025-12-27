import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

export interface Indicator {
  id: number;
  name: string;
  description?: string;
  category?: string;
  tags?: string[];
  price: number;
  is_free: boolean;
  language: string;
  download_count: number;
  purchase_count: number;
  average_rating: number;
  total_ratings: number;
  developer: {
    id: number;
    username?: string;
  };
  created_at?: string;
}

export interface IndicatorDetail extends Indicator {
  parameters?: Record<string, any>;
  status: string;
  current_version: number;
  latest_version?: {
    id: number;
    version: number;
    version_name?: string;
  };
  documentation?: string;
  usage_examples?: string;
}

export interface MarketplaceIndicatorsResponse {
  indicators: Indicator[];
  total: number;
  skip: number;
  limit: number;
}

export interface CreateIndicatorRequest {
  name: string;
  code: string;
  language?: string;
  description?: string;
  category?: string;
  tags?: string;
  price?: number;
  is_free?: boolean;
  parameters?: Record<string, any>;
}

export interface RateIndicatorRequest {
  rating: number; // 1-5
  comment?: string;
}

export interface ExecuteIndicatorRequest {
  market_data: Array<{
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    timestamp?: string;
  }>;
  parameters?: Record<string, any>;
}

export interface IndicatorFilters {
  sort_by?: "download_count" | "purchase_count" | "rating" | "price" | "created_at";
  category?: string;
  is_free?: boolean;
  min_rating?: number;
  search?: string;
  skip?: number;
  limit?: number;
}

export const useMarketplaceIndicators = (filters: IndicatorFilters = {}) => {
  const {
    sort_by = "download_count",
    category,
    is_free,
    min_rating,
    search,
    skip = 0,
    limit = 20,
  } = filters;

  return useQuery<MarketplaceIndicatorsResponse>({
    queryKey: ["indicators", "marketplace", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append("skip", skip.toString());
      params.append("limit", limit.toString());
      params.append("sort_by", sort_by);
      if (category) params.append("category", category);
      if (is_free !== undefined) params.append("is_free", is_free.toString());
      if (min_rating !== undefined) params.append("min_rating", min_rating.toString());
      if (search) params.append("search", search);

      return await apiRequest(`/api/indicators/marketplace?${params.toString()}`, {
        method: "GET",
      });
    },
    staleTime: 300000, // 5 minutes
  });
};

export const useIndicatorDetail = (indicatorId: number) => {
  return useQuery<IndicatorDetail>({
    queryKey: ["indicators", "detail", indicatorId],
    queryFn: async () => {
      return await apiRequest(`/api/indicators/${indicatorId}`, { method: "GET" });
    },
    enabled: !!indicatorId,
    staleTime: 120000, // 2 minutes
  });
};

export const useCreateIndicator = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: CreateIndicatorRequest) => {
      return await apiRequest("/api/indicators/create", {
        method: "POST",
        body: request,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["indicators"] });
    },
  });
};

export const usePublishIndicator = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (indicatorId: number) => {
      return await apiRequest(`/api/indicators/${indicatorId}/publish`, {
        method: "POST",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["indicators"] });
    },
  });
};

export const usePurchaseIndicator = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      indicatorId,
      versionId,
    }: {
      indicatorId: number;
      versionId?: number;
    }) => {
      const params = versionId ? `?version_id=${versionId}` : "";
      return await apiRequest(`/api/indicators/${indicatorId}/purchase${params}`, {
        method: "POST",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["indicators"] });
    },
  });
};

export const useRateIndicator = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      indicatorId,
      ...request
    }: { indicatorId: number } & RateIndicatorRequest) => {
      return await apiRequest(`/api/indicators/${indicatorId}/rate`, {
        method: "POST",
        body: request,
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["indicators", "detail", variables.indicatorId] });
      queryClient.invalidateQueries({ queryKey: ["indicators", "marketplace"] });
    },
  });
};

export const useExecuteIndicator = () => {
  return useMutation({
    mutationFn: async ({
      indicatorId,
      ...request
    }: { indicatorId: number } & ExecuteIndicatorRequest) => {
      return await apiRequest(`/api/indicators/${indicatorId}/execute`, {
        method: "POST",
        body: request,
      });
    },
  });
};

export interface VolumeProfileRequest {
  market_data: Array<{
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    timestamp?: string;
  }>;
  bins?: number;
}

export const useVolumeProfile = () => {
  return useMutation({
    mutationFn: async (request: VolumeProfileRequest) => {
      return await apiRequest("/api/indicators/volume-profile", {
        method: "POST",
        body: request,
      });
    },
  });
};
