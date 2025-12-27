import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { useTrailingBots } from "@/hooks/useApi";
import { Plus, ArrowUpDown } from "lucide-react";
import { TrailingBotCard } from "./TrailingBotCard";
import { TrailingBotCreator } from "./TrailingBotCreator";

export function TrailingBotPanel() {
  const { data: bots, isLoading, error, refetch } = useTrailingBots();
  const [showCreator, setShowCreator] = useState(false);

  if (isLoading) return <LoadingSkeleton count={3} className="h-32 w-full mb-4" />;
  if (error) {
    return (
      <ErrorRetry
        title="Failed to load trailing bots"
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
            <ArrowUpDown className="h-5 w-5" />
            Trailing Buy/Sell Bots
          </h2>
          <p className="text-muted-foreground mt-1">
            Follow price movements with dynamic stop-loss and take-profit
          </p>
        </div>
        <Button onClick={() => setShowCreator(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Trailing Bot
        </Button>
      </div>

      {showCreator && (
        <TrailingBotCreator
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
            <TrailingBotCard key={bot.id} bot={bot} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <ArrowUpDown className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Trailing Bots Yet</h3>
            <p className="text-muted-foreground text-center mb-4">
              Create your first trailing bot
            </p>
            <Button onClick={() => setShowCreator(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Trailing Bot
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

