import { PortfolioCard } from "../PortfolioCard";
import { Wallet, TrendingUp, Activity, DollarSign } from "lucide-react";

export default function PortfolioCardExample() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 p-4">
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
  );
}
