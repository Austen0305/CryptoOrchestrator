/**
 * Audit Log Viewer Component
 * Displays audit logs for security and compliance
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  user_id: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
}

interface AuditLogResponse {
  data: AuditLog[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export function AuditLogViewer() {
  const { data, isLoading, error, refetch } = useQuery<AuditLogResponse>({
    queryKey: ["audit-logs"],
    queryFn: () => apiRequest("/api/audit-logs", { method: "GET" }),
    staleTime: 60 * 1000, // 1 minute
  });

  if (isLoading) {
    return <LoadingSkeleton variant="card" />;
  }

  if (error) {
    return <ErrorRetry error={error} onRetry={() => refetch()} />;
  }

  const logs = data?.data || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit Logs</CardTitle>
        <CardDescription>Security and compliance audit trail</CardDescription>
      </CardHeader>
      <CardContent>
        {logs.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">No audit logs found</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>User ID</TableHead>
                <TableHead>IP Address</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                  <TableCell>{log.action}</TableCell>
                  <TableCell className="font-mono text-xs">{log.user_id}</TableCell>
                  <TableCell>{log.ip_address || "N/A"}</TableCell>
                  <TableCell className="max-w-xs truncate">{JSON.stringify(log.details)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
