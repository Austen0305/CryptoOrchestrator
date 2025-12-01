import { BotControlPanel } from "@/components/BotControlPanel";
import { BotCreator } from "@/components/BotCreator";
import { EmptyBotsState } from "@/components/EmptyState";
import { ErrorRetry } from "@/components/ErrorRetry";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { useBots, useStatus } from "@/hooks/useApi";

export default function Bots() {
  const { data: bots, isLoading: botsLoading, error: botsError, refetch } = useBots();
  const { data: status } = useStatus();

  if (botsLoading) {
    return (
      <div className="space-y-6 w-full">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Trading Bots</h1>
            <p className="text-muted-foreground mt-1">Loading bots...</p>
          </div>
        </div>
        <LoadingSkeleton count={3} className="h-32 w-full mb-4" />
      </div>
    );
  }

  if (botsError) {
    return (
      <div className="space-y-6 w-full">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Trading Bots</h1>
          </div>
        </div>
        <ErrorRetry
          title="Failed to load bots"
          message={botsError instanceof Error ? botsError.message : "An unexpected error occurred."}
          onRetry={() => refetch()}
          error={botsError as Error}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Trading Bots</h1>
          <p className="text-muted-foreground mt-1">
            Manage your automated trading strategies
            {status && (
              <span className="block text-sm mt-1">
                {status.runningBots} bots running • Kraken {status.krakenConnected ? "Connected" : "Disconnected"}
              </span>
            )}
          </p>
        </div>
        <BotCreator />
      </div>

      {bots && bots.length > 0 ? (
        <BotControlPanel bots={bots} />
      ) : (
        <EmptyBotsState onCreate={() => {}} />
      )}
    </div>
  );
}
