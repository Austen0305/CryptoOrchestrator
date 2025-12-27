import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

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
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["staking", "options"],
    queryFn: async () => {
      return await apiRequest<{ options: StakingOption[] }>("/api/staking/options", {
        method: "GET"
      });
    },
    enabled: isAuthenticated,
    staleTime: 300000, // 5 minutes - options don't change often
  });
};

export const useMyStakes = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["staking", "my-stakes"],
    queryFn: async () => {
      return await apiRequest<{ stakes: Array<{ asset: string; staked_amount: number; rewards: StakingRewards }> }>("/api/staking/my-stakes", {
        method: "GET"
      });
    },
    enabled: isAuthenticated,
    staleTime: 60000, // 1 minute
    refetchInterval: isAuthenticated ? 300000 : false, // 5 minutes when authenticated
  });
};

export const useStakingRewards = (asset: string) => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["staking", "rewards", asset],
    queryFn: async () => {
      return await apiRequest<StakingRewards>(`/api/staking/rewards?asset=${asset}`, {
        method: "GET"
      });
    },
    enabled: isAuthenticated && !!asset,
    staleTime: 60000, // 1 minute
    refetchInterval: isAuthenticated ? 300000 : false, // 5 minutes when authenticated
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
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (request) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["staking", "my-stakes"] });
      await queryClient.cancelQueries({ queryKey: ["wallet"] });
      
      // Snapshot the previous values
      const previousStakes = queryClient.getQueryData(["staking", "my-stakes"]);
      const previousWallet = queryClient.getQueryData(["wallet"]);
      
      // Return a context object with the snapshotted values
      return { previousStakes, previousWallet };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["staking"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, request, context) => {
      if (context?.previousStakes) {
        queryClient.setQueryData(["staking", "my-stakes"], context.previousStakes);
      }
      if (context?.previousWallet) {
        queryClient.setQueryData(["wallet"], context.previousWallet);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
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
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (request) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["staking", "my-stakes"] });
      await queryClient.cancelQueries({ queryKey: ["wallet"] });
      
      // Snapshot the previous values
      const previousStakes = queryClient.getQueryData(["staking", "my-stakes"]);
      const previousWallet = queryClient.getQueryData(["wallet"]);
      
      // Return a context object with the snapshotted values
      return { previousStakes, previousWallet };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["staking"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, request, context) => {
      if (context?.previousStakes) {
        queryClient.setQueryData(["staking", "my-stakes"], context.previousStakes);
      }
      if (context?.previousWallet) {
        queryClient.setQueryData(["wallet"], context.previousWallet);
      }
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["staking"] });
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
  });
};

