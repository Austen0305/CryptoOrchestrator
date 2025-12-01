import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { useDCABots } from "@/hooks/useApi";
import { Plus, TrendingUp } from "lucide-react";
import { DCABotCard } from "./DCABotCard";
import { DCABotCreator } from "./DCABotCreator";

export function DCATradingPanel() {
  const { data: bots, isLoading, error, refetch } = useDCABots();
  const [showCreator, setShowCreator] = useState(false);

  if (isLoading) return <LoadingSkeleton count={3} className="h-32 w-full mb-4" />;
  if (error) {
    return (
      <ErrorRetry
        title="Failed to load DCA bots"
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
            <TrendingUp className="h-5 w-5" />
            DCA Trading Bots
          </h2>
          <p className="text-muted-foreground mt-1">
            Buy at regular intervals to average out your purchase price
          </p>
        </div>
        <Button onClick={() => setShowCreator(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create DCA Bot
        </Button>
      </div>

      {showCreator && (
        <DCABotCreator
          onSuccess={() => {
            setShowCreator(false);
            refetch();
          }}
          onCancel={() => setShowCreator(false)}
        />
      )}

      {bots && bots.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {bots.map((bot: any) => (
            <DCABotCard key={bot.id} bot={bot} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No DCA Bots Yet</h3>
            <p className="text-muted-foreground text-center mb-4">
              Create your first DCA bot to start dollar cost averaging
            </p>
            <Button onClick={() => setShowCreator(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create DCA Bot
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

