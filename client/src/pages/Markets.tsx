import { MarketDataTable } from "@/components/MarketDataTable";

export default function Markets() {
  const mockMarkets = [
    { pair: "BTC/USD", price: 47350, change24h: 4.76, volume24h: 2400000000 },
    { pair: "ETH/USD", price: 2580, change24h: -1.23, volume24h: 1200000000 },
    { pair: "SOL/USD", price: 98.45, change24h: 8.92, volume24h: 450000000 },
    { pair: "ADA/USD", price: 0.58, change24h: 3.21, volume24h: 320000000 },
    { pair: "DOT/USD", price: 7.23, change24h: -2.14, volume24h: 180000000 },
    { pair: "MATIC/USD", price: 0.92, change24h: 5.67, volume24h: 280000000 },
    { pair: "LINK/USD", price: 14.82, change24h: -3.45, volume24h: 220000000 },
    { pair: "UNI/USD", price: 6.45, change24h: 7.23, volume24h: 190000000 },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Markets</h1>
        <p className="text-muted-foreground mt-1">
          Browse and trade cryptocurrency pairs
        </p>
      </div>

      <MarketDataTable markets={mockMarkets} />
    </div>
  );
}
