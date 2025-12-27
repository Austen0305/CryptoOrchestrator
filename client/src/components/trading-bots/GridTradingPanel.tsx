import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { GridBotCreator } from "./GridBotCreator";
import { GridBotCard } from "./GridBotCard";
import { useGridBots, useStartGridBot, useStopGridBot, useDeleteGridBot } from "@/hooks/useApi";
import { Plus, Grid } from "lucide-react";

export function GridTradingPanel() {
  const { data: bots, isLoading, error, refetch } = useGridBots();
  const [showCreator, setShowCreator] = useState(false);

  if (isLoading) {
    return <LoadingSkeleton count={3} className="h-32 w-full mb-4" />;
  }

  if (error) {
    return (
      <ErrorRetry
        title="Failed to load grid bots"
        message={error instanceof Error ? error.message : "An unexpected error occurred."}
        onRetry={() => refetch()}
        error={error as Error}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold flex items-center gap-2">
            <Grid className="h-5 w-5" />
            Grid Trading Bots
          </h2>
          <p className="text-muted-foreground mt-1">
            Place buy and sell orders in a grid pattern to profit from volatility
          </p>
        </div>
        <Button onClick={() => setShowCreator(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Grid Bot
        </Button>
      </div>

      {showCreator && (
        <GridBotCreator
          onSuccess={() => {
            setShowCreator(false);
            refetch();
          }}
          onCancel={() => setShowCreator(false)}
        />
      )}

      {bots && Array.isArray(bots) && bots.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {bots.map((bot: any) => (
            <GridBotCard key={bot.id} bot={bot} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Grid className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Grid Bots Yet</h3>
            <p className="text-muted-foreground text-center mb-4">
              Create your first grid trading bot to start profiting from market volatility
            </p>
            <Button onClick={() => setShowCreator(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Grid Bot
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

