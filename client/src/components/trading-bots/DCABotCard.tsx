import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useStartDCABot, useStopDCABot, useDeleteDCABot } from "@/hooks/useApi";
import { toast } from "@/hooks/use-toast";
import { Play, Square, Trash2, TrendingUp, TrendingDown } from "lucide-react";
import { useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface DCABotCardProps {
  bot: any;
}

export function DCABotCard({ bot }: DCABotCardProps) {
  const startBot = useStartDCABot();
  const stopBot = useStopDCABot();
  const deleteBot = useDeleteDCABot();

  const handleStart = async () => {
    try {
      await startBot.mutateAsync(bot.id);
      toast({ title: "Bot Started", description: `${bot.name} has been started.` });
    } catch (error) {
      toast({ title: "Error", description: "Failed to start bot.", variant: "destructive" });
    }
  };

  const handleStop = async () => {
    try {
      await stopBot.mutateAsync(bot.id);
      toast({ title: "Bot Stopped", description: `${bot.name} has been stopped.` });
    } catch (error) {
      toast({ title: "Error", description: "Failed to stop bot.", variant: "destructive" });
    }
  };

  const handleDelete = async () => {
    try {
      await deleteBot.mutateAsync(bot.id);
      toast({ title: "Bot Deleted", description: `${bot.name} has been deleted.` });
    } catch (error) {
      toast({ title: "Error", description: "Failed to delete bot.", variant: "destructive" });
    }
  };

  const isActive = bot.is_active || bot.status === "running";
  const profitColor = bot.total_profit >= 0 ? "text-green-500" : "text-red-500";
  const ProfitIcon = bot.total_profit >= 0 ? TrendingUp : TrendingDown;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{bot.name}</CardTitle>
            <CardDescription className="mt-1">
              {bot.symbol} • {bot.exchange}
            </CardDescription>
          </div>
          <Badge variant={isActive ? "default" : "secondary"}>{bot.status}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Orders Executed</p>
            <p className="font-medium">{bot.orders_executed || 0}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Total Invested</p>
            <p className="font-medium">${bot.total_invested?.toFixed(2) || "0.00"}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Average Price</p>
            <p className="font-medium">${bot.average_price?.toFixed(2) || "0.00"}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Profit</p>
            <p className={`font-medium flex items-center gap-1 ${profitColor}`}>
              <ProfitIcon className="h-4 w-4" />
              {bot.profit_percent?.toFixed(2) || "0.00"}%
            </p>
          </div>
        </div>
        <div className="flex gap-2 pt-2">
          {isActive ? (
            <Button variant="outline" size="sm" onClick={handleStop} disabled={stopBot.isPending} className="flex-1">
              <Square className="h-4 w-4 mr-2" />
              Stop
            </Button>
          ) : (
            <Button size="sm" onClick={handleStart} disabled={startBot.isPending} className="flex-1">
              <Play className="h-4 w-4 mr-2" />
              Start
            </Button>
          )}
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" size="sm" disabled={deleteBot.isPending}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete DCA Bot?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete {bot.name}. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </CardContent>
    </Card>
  );
}

