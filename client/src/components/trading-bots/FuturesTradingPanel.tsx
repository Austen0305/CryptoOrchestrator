import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { useFuturesPositions } from "@/hooks/useApi";
import { Plus, BarChart3 } from "lucide-react";
import { FuturesPositionCard } from "./FuturesPositionCard";
import { FuturesPositionCreator } from "./FuturesPositionCreator";

export function FuturesTradingPanel() {
  const { data: positions, isLoading, error, refetch } = useFuturesPositions(0, 100, false);
  const [showCreator, setShowCreator] = useState(false);

  if (isLoading) return <LoadingSkeleton count={3} className="h-32 w-full mb-4" />;
  if (error) {
    return (
      <ErrorRetry
        title="Failed to load futures positions"
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
            <BarChart3 className="h-5 w-5" />
            Futures Trading Positions
          </h2>
          <p className="text-muted-foreground mt-1">
            Trade with leverage (1x-125x) on futures markets
          </p>
        </div>
        <Button onClick={() => setShowCreator(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Open Position
        </Button>
      </div>

      {showCreator && (
        <FuturesPositionCreator
          onSuccess={() => {
            setShowCreator(false);
            refetch();
          }}
          onCancel={() => setShowCreator(false)}
        />
      )}

      {positions && Array.isArray(positions) && positions.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {positions.map((position: any) => (
            <FuturesPositionCard key={position.id} position={position} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Futures Positions Yet</h3>
            <p className="text-muted-foreground text-center mb-4">
              Open your first futures position to start trading with leverage
            </p>
            <Button onClick={() => setShowCreator(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Open Position
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

