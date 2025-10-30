import { TradeHistory } from "../TradeHistory";

const mockTrades = [
  {
    id: "1",
    pair: "BTC/USD",
    type: "buy" as const,
    amount: 0.5,
    price: 47200,
    total: 23600,
    timestamp: "2 mins ago",
    status: "completed" as const,
  },
  {
    id: "2",
    pair: "ETH/USD",
    type: "sell" as const,
    amount: 10,
    price: 2580,
    total: 25800,
    timestamp: "15 mins ago",
    status: "completed" as const,
  },
  {
    id: "3",
    pair: "SOL/USD",
    type: "buy" as const,
    amount: 50,
    price: 98.45,
    total: 4922.5,
    timestamp: "1 hour ago",
    status: "completed" as const,
  },
  {
    id: "4",
    pair: "BTC/USD",
    type: "sell" as const,
    amount: 0.25,
    price: 46800,
    total: 11700,
    timestamp: "3 hours ago",
    status: "completed" as const,
  },
];

export default function TradeHistoryExample() {
  return (
    <div className="max-w-2xl p-4">
      <TradeHistory trades={mockTrades} />
    </div>
  );
}
