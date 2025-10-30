import { BotControlPanel } from "../BotControlPanel";

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

export default function BotControlPanelExample() {
  return (
    <div className="max-w-3xl p-4">
      <BotControlPanel bots={mockBots} />
    </div>
  );
}
