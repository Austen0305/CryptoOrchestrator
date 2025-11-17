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
  const { data, isLoading, refetch, isRefetching } = useQuery<ExchangeStatusResponse>({
    queryKey: ['exchange-status'],
    queryFn: async () => {
      return await apiRequest<ExchangeStatusResponse>('/api/exchange-status', {
        method: 'GET',
      });
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const handleRefresh = () => {
    refetch();
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wifi className="h-5 w-5" />
            Exchange Status
          </CardTitle>
          <CardDescription>Checking exchange connectivity...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4 text-muted-foreground">
            Loading...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.total_exchanges === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wifi className="h-5 w-5" />
            Exchange Status
          </CardTitle>
          <CardDescription>No exchanges configured</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4 text-muted-foreground">
            <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>Add exchange API keys in Settings to enable real money trading</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Wifi className="h-5 w-5" />
              Exchange Status
            </CardTitle>
            <CardDescription>
              {data.connected_exchanges} of {data.total_exchanges} exchanges connected
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {data.exchanges.map((status) => (
            <div
              key={status.exchange}
              className="flex items-center justify-between p-3 rounded-lg border bg-card"
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
