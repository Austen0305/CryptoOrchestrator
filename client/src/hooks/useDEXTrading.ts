/**
 * DEX Trading Hook
 * Manages DEX trading operations using React Query
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { dexApi, type DEXQuoteRequest, type DEXSwapRequest, type SupportedChain } from "@/lib/api";
import { toast } from "@/components/ui/use-toast";
import { useAuth } from "@/hooks/useAuth";

export function useDEXQuote() {
  return useMutation({
    mutationFn: (request: DEXQuoteRequest) => dexApi.getQuote(request),
    onError: (error: unknown) => {
      const errorMessage = error instanceof Error ? error.message : "Failed to get quote";
      toast({
        title: "Quote Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });
}

export function useDEXSwap() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: DEXSwapRequest) => dexApi.executeSwap(request),
    // Optimistic update: immediately update UI before server confirms
    onMutate: async (request) => {
      // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({ queryKey: ["portfolio"] });
      await queryClient.cancelQueries({ queryKey: ["trades"] });
      
      // Snapshot the previous values
      const previousPortfolio = queryClient.getQueryData(["portfolio"]);
      const previousTrades = queryClient.getQueryData(["trades"]);
      
      // Return a context object with the snapshotted values
      return { previousPortfolio, previousTrades };
    },
    onSuccess: (data) => {
      toast({
        title: "Swap Initiated",
        description: data.custodial
          ? "Your swap is being processed"
          : "Swap calldata ready. Please confirm in your wallet.",
      });
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["trades"] });
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (error: unknown, request, context) => {
      if (context?.previousPortfolio) {
        queryClient.setQueryData(["portfolio"], context.previousPortfolio);
      }
      if (context?.previousTrades) {
        queryClient.setQueryData(["trades"], context.previousTrades);
      }
      const errorMessage = error instanceof Error ? error.message : "Failed to execute swap";
      toast({
        title: "Swap Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["trades"] });
    },
  });
}

export function useSupportedChains() {
  const { isAuthenticated } = useAuth();
  return useQuery<SupportedChain[]>({
    queryKey: ["dex", "supported-chains"],
    queryFn: () => dexApi.getSupportedChains(),
    enabled: isAuthenticated,
    staleTime: 300000, // 5 minutes - chains don't change often
  });
}
