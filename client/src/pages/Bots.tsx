import { BotControlPanel } from "@/components/BotControlPanel";
import { BotCreator } from "@/components/BotCreator";
import { EmptyBotsState } from "@/components/EmptyState";
import { ErrorRetry } from "@/components/ErrorRetry";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { OptimizedLoading } from "@/components/OptimizedLoading";
import { useBots, useStatus } from "@/hooks/useApi";
import { EnhancedErrorBoundary } from "@/components/EnhancedErrorBoundary";
import logger from "@/lib/logger";

function BotsContent() {
  const { data: bots, isLoading: botsLoading, error: botsError, refetch } = useBots();
  const { data: status } = useStatus();

  if (botsLoading) {
    return (
      <div className="space-y-6 w-full">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold" data-testid="bots-page">Trading Bots</h1>
            <p className="text-muted-foreground mt-1">Loading bots...</p>
          </div>
        </div>
        <OptimizedLoading variant="skeleton" />
      </div>
    );
  }

  if (botsError) {
    return (
      <div className="space-y-6 w-full">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold" data-testid="bots-page">Trading Bots</h1>
          </div>
        </div>
        <ErrorRetry
          title="Failed to load bots"
          onRetry={() => refetch()}
          error={botsError as Error}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 w-full">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold" data-testid="bots-page">Trading Bots</h1>
          <div className="text-muted-foreground mt-1 text-sm sm:text-base">
            <p>Manage your automated trading strategies</p>
            {status?.runningBots !== undefined ? (
              <p className="text-xs sm:text-sm mt-1">
                {String(status.runningBots || 0)} bots running • Blockchain Trading Active
              </p>
            ) : null}
          </div>
        </div>
        <div className="w-full sm:w-auto">
          <BotCreator />
        </div>
      </div>

      {bots && Array.isArray(bots) && bots.length > 0 ? (
        <BotControlPanel bots={bots} />
      ) : (
        <EmptyBotsState onCreateBot={() => {}} />
      )}
    </div>
  );
}

export default function Bots() {
  return (
    <EnhancedErrorBoundary
      onError={(error, errorInfo) => {
        logger.error("Bots page error", { error, errorInfo });
      }}
    >
      <BotsContent />
    </EnhancedErrorBoundary>
  );
}
