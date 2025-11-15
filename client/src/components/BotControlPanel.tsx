import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Settings, TrendingUp, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { useStartBot, useStopBot } from "@/hooks/useApi";
import { useIntegrationsStatus, useStartIntegrations, useStopIntegrations } from "@/hooks/useApi";
import { toast } from "@/hooks/use-toast";
import type { BotConfig } from "../../../shared/schema";
import { BotIntelligence } from "./BotIntelligence";

interface BotControlPanelProps {
  bots: BotConfig[];
}

export function BotControlPanel({ bots }: BotControlPanelProps) {
  const startBotMutation = useStartBot();
  const stopBotMutation = useStopBot();
  const [pendingActions, setPendingActions] = useState<Set<string>>(new Set());
  const [expandedBots, setExpandedBots] = useState<Set<string>>(new Set());
  const integrationsStatus = useIntegrationsStatus();
  const startIntegrationsMut = useStartIntegrations();
  const stopIntegrationsMut = useStopIntegrations();

  const toggleBot = async (botId: string, currentStatus: string) => {
    if (pendingActions.has(botId)) return;

    setPendingActions(prev => new Set(prev).add(botId));

    try {
      if (currentStatus === "running") {
        await stopBotMutation.mutateAsync(botId);
        toast({
          title: "Bot Stopped",
          description: "The trading bot has been stopped successfully.",
        });
      } else {
        await startBotMutation.mutateAsync(botId);
        toast({
          title: "Bot Started",
          description: "The trading bot has been started successfully.",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${currentStatus === "running" ? "stop" : "start"} bot. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setPendingActions(prev => {
        const newSet = new Set(prev);
        newSet.delete(botId);
        return newSet;
      });
    }
  };

  const toggleIntelligence = (botId: string) => {
    setExpandedBots(prev => {
      const newSet = new Set(prev);
      if (newSet.has(botId)) {
        newSet.delete(botId);
      } else {
        newSet.add(botId);
      }
      return newSet;
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Button size="sm" onClick={() => startIntegrationsMut.mutate()} disabled={startIntegrationsMut.isPending}>
            Start Adapters
          </Button>
          <Button size="sm" variant="destructive" onClick={() => stopIntegrationsMut.mutate()} disabled={stopIntegrationsMut.isPending}>
            Stop Adapters
          </Button>
        </div>
        <div>
          <span className="text-sm text-muted-foreground">Adapters:</span>
          <Badge className="ml-2">{integrationsStatus.data ? 'online' : 'offline'}</Badge>
        </div>
      </div>
      {bots.map((bot) => {
        const isRunning = bot.status === "running";
        const isProfit = bot.profitLoss >= 0;
        const isPending = pendingActions.has(bot.id);
  const isExpanded = expandedBots.has(bot.id);

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
                {isPending ? (
                  <div className="flex items-center gap-1">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    {isRunning ? "Stopping..." : "Starting..."}
                  </div>
                ) : (
                  bot.status.charAt(0).toUpperCase() + bot.status.slice(1)
                )}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">P&L</p>
                  <p
                    className={`text-xl font-mono font-bold ${
                      isProfit ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                    }`}
                    data-testid={`text-pnl-${bot.id}`}
                  >
                    {isProfit ? "+" : ""}${bot.profitLoss.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Win Rate</p>
                  <p className="text-xl font-mono font-bold">{bot.winRate.toFixed(1)}%</p>
                  <Progress value={bot.winRate} className="mt-1 h-1" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Trades</p>
                  <p className="text-xl font-mono font-bold">{bot.totalTrades}</p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={isRunning}
                    onCheckedChange={() => toggleBot(bot.id, bot.status)}
                    disabled={isPending || startBotMutation.isPending || stopBotMutation.isPending}
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
                    onClick={() => toggleIntelligence(bot.id)}
                    data-testid={`button-intelligence-${bot.id}`}
                  >
                    {isExpanded ? <ChevronUp className="h-4 w-4 mr-1" /> : <ChevronDown className="h-4 w-4 mr-1" />}
                    AI Intelligence
                  </Button>
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

              {isExpanded && (
                <div className="pt-4 border-t">
                  <BotIntelligence botId={bot.id} />
                </div>
              )}
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
