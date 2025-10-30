import { BotControlPanel } from "@/components/BotControlPanel";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export default function Bots() {
  const mockBots = [
    {
      id: "bot-1",
      name: "ML Trend Follower",
      strategy: "LSTM Price Prediction",
      status: "running" as const,
      profitLoss: 3245,
      winRate: 68,
      trades: 142,
    },
    {
      id: "bot-2",
      name: "RSI Scalper",
      strategy: "Mean Reversion",
      status: "running" as const,
      profitLoss: 1820,
      winRate: 72,
      trades: 89,
    },
    {
      id: "bot-3",
      name: "Grid Trading Bot",
      strategy: "Grid Strategy",
      status: "stopped" as const,
      profitLoss: -450,
      winRate: 45,
      trades: 56,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Trading Bots</h1>
          <p className="text-muted-foreground mt-1">
            Manage your automated trading strategies
          </p>
        </div>
        <Button data-testid="button-add-bot">
          <Plus className="h-4 w-4 mr-2" />
          Add New Bot
        </Button>
      </div>

      <BotControlPanel bots={mockBots} />
    </div>
  );
}
