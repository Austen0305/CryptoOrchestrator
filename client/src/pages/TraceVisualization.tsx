/**
 * Trace Visualization
 * Distributed tracing visualization and analysis
 */

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Search, Filter, Download, Clock, Activity, AlertCircle, CheckCircle2 } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { toast } from "@/hooks/use-toast";

interface Trace {
  trace_id: string;
  service_name: string;
  operation_name: string;
  start_time: string;
  end_time: string;
  duration_ms: number;
  status: string;
  span_count: number;
  error_count: number;
  tags: Record<string, string>;
}

interface Span {
  span_id: string;
  trace_id: string;
  parent_span_id?: string;
  service_name: string;
  operation_name: string;
  start_time: string;
  end_time: string;
  duration_ms: number;
  status: string;
  tags: Record<string, string>;
  logs?: Array<{ timestamp: string; fields: Record<string, any> }>;
}

interface TraceDetail {
  trace: Trace;
  spans: Span[];
  service_map: Record<string, string[]>;
}

export default function TraceVisualization() {
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [serviceFilter, setServiceFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [timeRange, setTimeRange] = useState<string>("1h");

  // Fetch traces
  const { data: traces, isLoading: tracesLoading } = useQuery<Trace[]>({
    queryKey: [
      "/api/observability/traces",
      { service: serviceFilter, status: statusFilter, time_range: timeRange },
    ],
  });

  // Fetch trace detail
  const { data: traceDetail, isLoading: detailLoading } = useQuery<TraceDetail>({
    queryKey: ["/api/observability/traces", selectedTraceId],
    enabled: !!selectedTraceId,
  });

  // Fetch services for filter
  const { data: services } = useQuery<string[]>({
    queryKey: ["/api/observability/services"],
  });

  const filteredTraces = traces?.filter((trace) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        trace.trace_id.toLowerCase().includes(query) ||
        trace.service_name.toLowerCase().includes(query) ||
        trace.operation_name.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const handleExportTrace = async (traceId: string) => {
    try {
      const response = await apiRequest(`/api/observability/traces/${traceId}/export`, {
        method: "GET",
      });
      
      // Create download link
      const blob = new Blob([JSON.stringify(response, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `trace_${traceId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast({
        title: "Trace Exported",
        description: "Trace data exported successfully",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to export trace",
        variant: "destructive",
      });
    }
  };

  const formatDuration = (ms: number): string => {
    if (ms < 1) return `${(ms * 1000).toFixed(0)}μs`;
    if (ms < 1000) return `${ms.toFixed(2)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getStatusBadge = (status: string) => {
    if (status === "ok" || status === "success") {
      return (
        <Badge variant="default" className="bg-green-500">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Success
        </Badge>
      );
    }
    if (status === "error" || status === "failed") {
      return (
        <Badge variant="destructive">
          <AlertCircle className="mr-1 h-3 w-3" />
          Error
        </Badge>
      );
    }
    return (
      <Badge variant="secondary">
        <Activity className="mr-1 h-3 w-3" />
        {status}
      </Badge>
    );
  };

  const renderSpanTree = (spans: Span[], parentId?: string, level: number = 0): React.ReactNode => {
    const children = spans.filter((span) => span.parent_span_id === parentId);
    
    if (children.length === 0) return null;

    return (
      <div className="ml-4">
        {children.map((span) => (
          <div key={span.span_id} className="mb-2 border-l-2 border-muted pl-4">
            <div className="flex items-center justify-between p-2 bg-muted/50 rounded">
              <div className="flex items-center gap-2">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{
                    backgroundColor: span.status === "ok" ? "#10b981" : "#ef4444",
                  }}
                />
                <span className="font-medium">{span.operation_name}</span>
                <Badge variant="outline">{span.service_name}</Badge>
                {getStatusBadge(span.status)}
              </div>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDuration(span.duration_ms)}
                </span>
                <span>{new Date(span.start_time).toLocaleTimeString()}</span>
              </div>
            </div>
            {renderSpanTree(spans, span.span_id, level + 1)}
          </div>
        ))}
      </div>
    );
  };

  if (tracesLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Loading traces...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Trace Visualization</h1>
          <p className="text-muted-foreground">View and analyze distributed traces</p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="search">Search</Label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search"
                  placeholder="Search traces..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="service">Service</Label>
              <Select value={serviceFilter} onValueChange={setServiceFilter}>
                <SelectTrigger id="service">
                  <SelectValue placeholder="All services" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Services</SelectItem>
                  {services?.map((service) => (
                    <SelectItem key={service} value={service}>
                      {service}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger id="status">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="ok">Success</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="timeRange">Time Range</Label>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger id="timeRange">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15m">Last 15 minutes</SelectItem>
                  <SelectItem value="1h">Last hour</SelectItem>
                  <SelectItem value="6h">Last 6 hours</SelectItem>
                  <SelectItem value="24h">Last 24 hours</SelectItem>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trace List */}
        <Card>
          <CardHeader>
            <CardTitle>Traces</CardTitle>
            <CardDescription>
              {filteredTraces?.length || 0} trace{filteredTraces?.length !== 1 ? "s" : ""} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!filteredTraces || filteredTraces.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No traces found. Try adjusting your filters.
              </div>
            ) : (
              <div className="space-y-2">
                {filteredTraces.map((trace) => (
                  <div
                    key={trace.trace_id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedTraceId === trace.trace_id
                        ? "border-primary bg-primary/5"
                        : "hover:bg-muted"
                    }`}
                    onClick={() => setSelectedTraceId(trace.trace_id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs">{trace.trace_id.substring(0, 8)}...</span>
                        {getStatusBadge(trace.status)}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {formatDuration(trace.duration_ms)}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline">{trace.service_name}</Badge>
                      <span className="text-sm">{trace.operation_name}</span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>{trace.span_count} spans</span>
                      {trace.error_count > 0 && (
                        <span className="text-destructive">{trace.error_count} errors</span>
                      )}
                      <span>{new Date(trace.start_time).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Trace Detail */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Trace Details</CardTitle>
                <CardDescription>
                  {selectedTraceId ? `Trace: ${selectedTraceId.substring(0, 16)}...` : "Select a trace to view details"}
                </CardDescription>
              </div>
              {selectedTraceId && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleExportTrace(selectedTraceId)}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {detailLoading ? (
              <div className="text-center py-8 text-muted-foreground">Loading trace details...</div>
            ) : !traceDetail ? (
              <div className="text-center py-8 text-muted-foreground">
                Select a trace from the list to view details
              </div>
            ) : (
              <div className="space-y-4">
                {/* Trace Summary */}
                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Service:</span>
                      <span className="ml-2 font-medium">{traceDetail.trace.service_name}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Operation:</span>
                      <span className="ml-2 font-medium">{traceDetail.trace.operation_name}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Duration:</span>
                      <span className="ml-2 font-medium">{formatDuration(traceDetail.trace.duration_ms)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Spans:</span>
                      <span className="ml-2 font-medium">{traceDetail.trace.span_count}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Start Time:</span>
                      <span className="ml-2 font-medium">
                        {new Date(traceDetail.trace.start_time).toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">End Time:</span>
                      <span className="ml-2 font-medium">
                        {new Date(traceDetail.trace.end_time).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Span Tree */}
                <div>
                  <h3 className="font-semibold mb-3">Span Tree</h3>
                  {traceDetail.spans.length === 0 ? (
                    <div className="text-sm text-muted-foreground">No spans found</div>
                  ) : (
                    <div className="border rounded-lg p-4">
                      {renderSpanTree(traceDetail.spans)}
                    </div>
                  )}
                </div>

                {/* Service Map */}
                {Object.keys(traceDetail.service_map).length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3">Service Dependencies</h3>
                    <div className="space-y-2">
                      {Object.entries(traceDetail.service_map).map(([service, dependencies]) => (
                        <div key={service} className="p-2 bg-muted/50 rounded">
                          <span className="font-medium">{service}</span>
                          {dependencies.length > 0 && (
                            <span className="text-sm text-muted-foreground ml-2">
                              → {dependencies.join(", ")}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
