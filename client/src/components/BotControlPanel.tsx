import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Play, Pause, Settings, TrendingUp } from "lucide-react";

interface BotConfig {
  id: string;
  name: string;
  strategy: string;
  status: "running" | "stopped" | "paused";
  profitLoss: number;
  winRate: number;
  trades: number;
}

interface BotControlPanelProps {
  bots: BotConfig[];
}

export function BotControlPanel({ bots }: BotControlPanelProps) {
  const [botStates, setBotStates] = useState<Record<string, boolean>>(
    bots.reduce((acc, bot) => ({ ...acc, [bot.id]: bot.status === "running" }), {})
  );

  const toggleBot = (botId: string) => {
    setBotStates((prev) => {
      const newState = !prev[botId];
      console.log(`${newState ? "Starting" : "Stopping"} bot ${botId}`);
      return { ...prev, [botId]: newState };
    });
  };

  return (
    <div className="space-y-4">
      {bots.map((bot) => {
        const isRunning = botStates[bot.id];
        const isProfit = bot.profitLoss >= 0;

        return (
          <Card key={bot.id} data-testid={`card-bot-${bot.id}`}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <div className="space-y-1">
                <CardTitle className="text-lg">{bot.name}</CardTitle>
                <p className="text-sm text-muted-foreground">{bot.strategy}</p>
              </div>
              <Badge
                variant={isRunning ? "default" : "secondary"}
                data-testid={`badge-status-${bot.id}`}
              >
                {isRunning ? "Running" : "Stopped"}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">P&L</p>
                  <p
                    className={`text-xl font-mono font-bold ${
                      isProfit ? "text-trading-profit" : "text-trading-loss"
                    }`}
                    data-testid={`text-pnl-${bot.id}`}
                  >
                    {isProfit ? "+" : ""}${bot.profitLoss.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Win Rate</p>
                  <p className="text-xl font-mono font-bold">{bot.winRate}%</p>
                  <Progress value={bot.winRate} className="mt-1 h-1" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Trades</p>
                  <p className="text-xl font-mono font-bold">{bot.trades}</p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={isRunning}
                    onCheckedChange={() => toggleBot(bot.id)}
                    data-testid={`switch-bot-${bot.id}`}
                  />
                  <Label className="cursor-pointer">
                    {isRunning ? "Active" : "Inactive"}
                  </Label>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    data-testid={`button-settings-${bot.id}`}
                  >
                    <Settings className="h-4 w-4 mr-1" />
                    Settings
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    data-testid={`button-performance-${bot.id}`}
                  >
                    <TrendingUp className="h-4 w-4 mr-1" />
                    Performance
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
