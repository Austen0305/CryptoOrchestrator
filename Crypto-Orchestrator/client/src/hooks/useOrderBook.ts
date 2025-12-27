import { useQuery } from "@tanstack/react-query";
import { marketApi } from "@/lib/api";
import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";

export interface OrderBookEntry {
  price: number;
  amount: number;
  total: number;
}

export interface OrderBookData {
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
  spread: number;
  timestamp: number;
}

/**
 * Hook to fetch order book data for a trading pair
 * @param pair Trading pair (e.g., "BTC/USD")
 * @param autoRefresh Whether to auto-refresh (default: true)
 * @param refreshInterval Refresh interval in milliseconds (default: 1000ms)
 */
export function useOrderBook(
  pair: string,
  autoRefresh: boolean = true,
  refreshInterval: number = 1000
) {
  const { isAuthenticated } = useAuth();
  const [orderBookData, setOrderBookData] = useState<OrderBookData | null>(null);

  const { data, isLoading, error, refetch } = useQuery<OrderBookData | null>({
    queryKey: ["orderbook", pair],
    queryFn: async () => {
      if (!pair) return null;
      const orderBookResponse = await marketApi.getOrderBook(pair);
      
      // Transform API response to our format
      const bids: OrderBookEntry[] = (orderBookResponse.bids || []).map((bid: [number, number], index: number) => {
        const price = bid[0];
        const amount = bid[1];
        const prevTotal = index > 0 ? orderBookData?.bids[index - 1]?.total || 0 : 0;
        return {
          price,
          amount,
          total: prevTotal + (price * amount),
        };
      });

      const asks: OrderBookEntry[] = (orderBookResponse.asks || []).map((ask: [number, number], index: number) => {
        const price = ask[0];
        const amount = ask[1];
        const prevTotal = index > 0 ? orderBookData?.asks[index - 1]?.total || 0 : 0;
        return {
          price,
          amount,
          total: prevTotal + (price * amount),
        };
      });

      // Calculate spread
      const bestBid = bids.length > 0 ? bids[0]?.price || 0 : 0;
      const bestAsk = asks.length > 0 ? asks[0]?.price || 0 : 0;
      const spread = bestAsk > 0 && bestBid > 0 ? bestAsk - bestBid : 0;

      return {
        bids: bids.slice(0, 10), // Top 10 bids
        asks: asks.slice(0, 10), // Top 10 asks
        spread,
        timestamp: Date.now(),
      } as OrderBookData;
    },
    enabled: isAuthenticated && !!pair,
    staleTime: 500, // 500ms for order book data (real-time)
    refetchInterval: isAuthenticated && autoRefresh ? refreshInterval : false,
  });

  useEffect(() => {
    if (data) {
      setOrderBookData(data);
    }
  }, [data]);

  return {
    data: orderBookData,
    isLoading,
    error,
    refetch,
  };
}

