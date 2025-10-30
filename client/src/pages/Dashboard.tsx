import { PortfolioCard } from "@/components/PortfolioCard";
import { PriceChart } from "@/components/PriceChart";
import { OrderEntryPanel } from "@/components/OrderEntryPanel";
import { OrderBook } from "@/components/OrderBook";
import { TradeHistory } from "@/components/TradeHistory";
import { Wallet, TrendingUp, Activity, DollarSign } from "lucide-react";

export default function Dashboard() {
  const chartData = [
    { time: "00:00", price: 45200 },
    { time: "04:00", price: 45800 },
    { time: "08:00", price: 45300 },
    { time: "12:00", price: 46200 },
    { time: "16:00", price: 46800 },
    { time: "20:00", price: 47100 },
    { time: "24:00", price: 47350 },
  ];

  const mockBids = [
    { price: 47340, amount: 0.5234, total: 24765 },
    { price: 47335, amount: 1.2341, total: 58405 },
    { price: 47330, amount: 0.8921, total: 42207 },
    { price: 47325, amount: 2.1234, total: 100489 },
    { price: 47320, amount: 0.4567, total: 21608 },
  ];

  const mockAsks = [
    { price: 47355, amount: 0.6234, total: 29521 },
    { price: 47360, amount: 1.4321, total: 67828 },
    { price: 47365, amount: 0.7821, total: 37039 },
    { price: 47370, amount: 2.3421, total: 110952 },
    { price: 47375, amount: 0.5421, total: 25682 },
  ];

  const recentTrades = [
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
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <PortfolioCard
          title="Total Balance"
          value="$125,430"
          change={12.5}
          icon={Wallet}
        />
        <PortfolioCard
          title="24h P&L"
          value="$3,245"
          change={8.2}
          icon={TrendingUp}
        />
        <PortfolioCard
          title="Active Bots"
          value="3"
          icon={Activity}
          subtitle="2 profitable"
        />
        <PortfolioCard
          title="Daily Volume"
          value="$45,200"
          change={-2.4}
          icon={DollarSign}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-[600px]">
          <PriceChart
            pair="BTC/USD"
            currentPrice={47350}
            change24h={4.76}
            data={chartData}
          />
        </div>
        <div className="space-y-6">
          <OrderEntryPanel />
          <OrderBook bids={mockBids} asks={mockAsks} spread={15} />
        </div>
      </div>

      <TradeHistory trades={recentTrades} />
    </div>
  );
}
