/**
 * Audit Log Viewer Component
 * Displays audit logs for compliance and security monitoring
 */

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { RefreshCw, Shield, AlertCircle, CheckCircle2, XCircle, Filter } from 'lucide-react';
import { apiRequest } from '@/lib/queryClient';
import { useQuery } from '@tanstack/react-query';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { ErrorRetry } from '@/components/ErrorRetry';
import { EmptyState } from '@/components/EmptyState';
import { Pagination } from '@/components/Pagination';

interface AuditLogEntry {
  timestamp: string;
  event_type: string;
  user_id: number | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, any> | null;
  status: string;
  error_message: string | null;
}

interface AuditLogResponse {
  entries: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

export function AuditLogViewer() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [eventType, setEventType] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");

  const { data, isLoading, refetch, isRefetching, error } = useQuery<AuditLogResponse>({
    queryKey: ['audit-logs', page, pageSize, eventType, status],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('page_size', String(pageSize));
      if (eventType !== 'all') params.append('event_type', eventType);
      if (status !== 'all') params.append('status', status);
      
      return await apiRequest<AuditLogResponse>(`/api/audit-logs?${params.toString()}`, {
        method: 'GET',
      });
    },
    refetchInterval: 60000, // Refresh every minute
  });

  const handleRefresh = () => {
    refetch();
  };
  const handlePageSizeChange = (size: number) => {
    setPage(1);
    setPageSize(size);
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const getStatusIcon = (status: string) => {
    if (status === 'success') {
      return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    } else if (status === 'failure') {
      return <XCircle className="h-4 w-4 text-red-500" />;
    } else {
      return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
  };

  if (isLoading && !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Audit Logs
          </CardTitle>
          <CardDescription>Loading audit logs...</CardDescription>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton count={6} className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Audit Logs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorRetry
            title="Failed to load audit logs"
            message={error instanceof Error ? error.message : 'Unable to fetch audit logs. Please try again.'}
            onRetry={handleRefresh}
            error={error as Error}
          />
        </CardContent>
      </Card>
    );
  }

  const hasEntries = data && data.entries.length > 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Audit Logs
            </CardTitle>
            <CardDescription>
              {data ? `${data.total} total entries` : 'No audit logs available'}
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
        
        {/* Filters */}
        <div className="flex items-center gap-2 mt-4">
          <Select value={eventType} onValueChange={setEventType}>
            <SelectTrigger className="w-[180px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Event Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Events</SelectItem>
              <SelectItem value="trade_execution">Trade Execution</SelectItem>
              <SelectItem value="api_key_operation">API Key Operation</SelectItem>
              <SelectItem value="user_action">User Action</SelectItem>
              <SelectItem value="system_event">System Event</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="failure">Failure</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={String(pageSize)} onValueChange={(value) => setPageSize(Number(value))}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Page Size" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="25">25 per page</SelectItem>
              <SelectItem value="50">50 per page</SelectItem>
              <SelectItem value="100">100 per page</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {!hasEntries ? (
          <EmptyState
            icon={AlertCircle}
            title="No audit logs found"
            description="Audit log entries will appear here once system activity is recorded."
          />
        ) : (
          <>
            <ScrollArea className="h-[600px] pr-4">
              <div className="space-y-3">
                {data.entries.map((entry, index) => (
                  <div
                    key={`${entry.timestamp}-${index}`}
                    className="flex items-start justify-between p-3 rounded-lg border bg-card"
                  >
                    <div className="flex items-start gap-3 flex-1">
                      <div className="flex-shrink-0 mt-1">
                        {getStatusIcon(entry.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold">{entry.event_type}</span>
                          <Badge
                            variant={entry.status === 'success' ? 'default' : 'destructive'}
                            className="text-xs"
                          >
                            {entry.status}
                          </Badge>
                          {entry.user_id && (
                            <Badge variant="outline" className="text-xs">
                              User {entry.user_id}
                            </Badge>
                          )}
                        </div>
                        <div className="text-sm text-muted-foreground mb-1">
                          {entry.action}
                        </div>
                        {entry.resource_type && entry.resource_id && (
                          <div className="text-xs text-muted-foreground mb-1">
                            {entry.resource_type}: {entry.resource_id}
                          </div>
                        )}
                        {entry.details && Object.keys(entry.details).length > 0 && (
                          <div className="text-xs text-muted-foreground mt-1">
                            <details>
                              <summary className="cursor-pointer hover:text-foreground">
                                View Details
                              </summary>
                              <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto">
                                {JSON.stringify(entry.details, null, 2)}
                              </pre>
                            </details>
                          </div>
                        )}
                        {entry.error_message && (
                          <div className="text-xs text-red-500 mt-1">
                            Error: {entry.error_message}
                          </div>
                        )}
                        <div className="text-xs text-muted-foreground mt-1">
                          {formatTimestamp(entry.timestamp)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {data.total > pageSize && (
              <Pagination
                page={page}
                pageSize={pageSize}
                totalPages={Math.ceil(data.total / pageSize)}
                totalItems={data.total}
                onPageChange={(page) => setPage(page)}
                onPageSizeChange={handlePageSizeChange}
                pageSizeOptions={[25, 50, 100]}
                className="mt-4"
              />
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

