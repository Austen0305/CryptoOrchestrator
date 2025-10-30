import { MarketDataTable } from "../MarketDataTable";

const mockMarkets = [
  { pair: "BTC/USD", price: 47350, change24h: 4.76, volume24h: 2400000000 },
  { pair: "ETH/USD", price: 2580, change24h: -1.23, volume24h: 1200000000 },
  { pair: "SOL/USD", price: 98.45, change24h: 8.92, volume24h: 450000000 },
  { pair: "ADA/USD", price: 0.58, change24h: 3.21, volume24h: 320000000 },
  { pair: "DOT/USD", price: 7.23, change24h: -2.14, volume24h: 180000000 },
];

export default function MarketDataTableExample() {
  return (
    <div className="p-4">
      <MarketDataTable markets={mockMarkets} />
    </div>
  );
}
