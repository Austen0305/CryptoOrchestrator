import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";

export interface StakingOption {
  asset: string;
  apy: number;
  min_amount: number;
  lock_period_days: number;
  description: string;
}

export interface StakingRewards {
  asset: string;
  staked_amount: number;
  apy: number;
  daily_rewards: number;
  monthly_rewards: number;
  yearly_rewards: number;
}

export interface StakeRequest {
  asset: string;
  amount: number;
}

export interface UnstakeRequest {
  asset: string;
  amount: number;
}

export const useStakingOptions = () => {
  return useQuery({
    queryKey: ["staking", "options"],
    queryFn: async () => {
      return await apiRequest<{ options: StakingOption[] }>("/api/staking/options", {
        method: "GET"
      });
    },
    staleTime: 300000, // 5 minutes
  });
};

export const useMyStakes = () => {
  return useQuery({
    queryKey: ["staking", "my-stakes"],
    queryFn: async () => {
      return await apiRequest<{ stakes: Array<{ asset: string; staked_amount: number; rewards: StakingRewards }> }>("/api/staking/my-stakes", {
        method: "GET"
      });
    },
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // 5 minutes
  });
};

export const useStakingRewards = (asset: string) => {
  return useQuery({
    queryKey: ["staking", "rewards", asset],
    queryFn: async () => {
      return await apiRequest<StakingRewards>(`/api/staking/rewards?asset=${asset}`, {
        method: "GET"
      });
    },
    staleTime: 60000,
    refetchInterval: 300000,
  });
};

export const useStake = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: StakeRequest) => {
      return await apiRequest("/api/staking/stake", {
        method: "POST",
        body: request,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["staking"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
  });
};

export const useUnstake = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: UnstakeRequest) => {
      return await apiRequest("/api/staking/unstake", {
        method: "POST",
        body: request,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["staking"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
  });
};

