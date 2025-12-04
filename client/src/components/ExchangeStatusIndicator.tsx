/**
 * Exchange Status Indicator Component
 * Displays real-time connectivity status for all configured exchanges
 */

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RefreshCw, Wifi, WifiOff, AlertCircle, CheckCircle2 } from 'lucide-react';
import { apiRequest } from '@/lib/queryClient';
import { useQuery } from '@tanstack/react-query';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { ErrorRetry } from '@/components/ErrorRetry';
import { EmptyState } from '@/components/EmptyState';

interface ExchangeStatusData {
  exchange: string;
  is_connected: boolean;
  is_validated: boolean;
  last_checked: string | null;
  error: string | null;
  latency_ms: number | null;
}

interface ExchangeStatusResponse {
  exchanges: ExchangeStatusData[];
  total_exchanges: number;
  connected_exchanges: number;
  validated_exchanges: number;
}

export function ExchangeStatusIndicator() {
  const { data, isLoading, error, refetch, isRefetching } = useQuery<ExchangeStatusResponse>({
    queryKey: ['exchange-status'],
    queryFn: async () => {
      return await apiRequest<ExchangeStatusResponse>('/api/exchange-status', {
        method: 'GET',
      });
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 2,
  });

  const handleRefresh = () => {
    refetch();
  };

  if (isLoading) {
    return (
      <Card className="border-card-border shadow-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            <Wifi className="h-5 w-5 text-primary" />
            Exchange Status
          </CardTitle>
          <CardDescription>Checking exchange connectivity...</CardDescription>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton count={3} className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-card-border shadow-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            <Wifi className="h-5 w-5 text-primary" />
            Exchange Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorRetry
            title="Failed to load exchange status"
            message={error instanceof Error ? error.message : "Unable to fetch exchange status. Please try again."}
            onRetry={handleRefresh}
            error={error as Error}
          />
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.exchanges || data.exchanges.length === 0 || data.total_exchanges === 0) {
    return (
      <Card className="border-card-border shadow-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            <Wifi className="h-5 w-5 text-primary" />
            Exchange Status
          </CardTitle>
          <CardDescription>No exchanges configured</CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={AlertCircle}
            title="No exchanges configured"
            description="Add exchange API keys in Settings to enable real money trading"
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-card-border shadow-md">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg font-bold">
              <Wifi className="h-5 w-5 text-primary" />
              Exchange Status
            </CardTitle>
            <CardDescription className="text-sm">
              {data.connected_exchanges} of {data.total_exchanges} exchanges connected
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefetching}
            className="rounded-md"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {(data.exchanges || []).map((status) => (
            <div
              key={status.exchange}
              className="flex items-center justify-between p-3 md:p-4 rounded-lg border border-border/50 bg-card hover:bg-accent/30 transition-all duration-200"
            >
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0">
                  {status.is_connected ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : status.is_validated ? (
                    <WifiOff className="h-5 w-5 text-yellow-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-gray-400" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{status.exchange.toUpperCase()}</span>
                    {status.is_validated && (
                      <Badge variant="outline" className="text-xs">
                        Validated
                      </Badge>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {status.is_connected ? (
                      <>
                        Connected
                        {status.latency_ms !== null && (
                          <span className="ml-2">
                            ({status.latency_ms.toFixed(0)}ms)
                          </span>
                        )}
                      </>
                    ) : status.is_validated ? (
                      status.error || 'Disconnected'
                    ) : (
                      'Not validated'
                    )}
                  </div>
                </div>
              </div>
              <div>
                <Badge
                  variant={status.is_connected ? 'default' : status.is_validated ? 'secondary' : 'outline'}
                  className={
                    status.is_connected
                      ? 'bg-green-500'
                      : status.is_validated
                      ? 'bg-yellow-500'
                      : ''
                  }
                >
                  {status.is_connected ? 'Online' : status.is_validated ? 'Offline' : 'Not Configured'}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
