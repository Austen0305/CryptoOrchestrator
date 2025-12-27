/**
 * SLA Dashboard
 * Real-time SLA metrics and compliance tracking
 */

import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  TrendingUp,
  Activity,
  Clock,
  Target,
} from "lucide-react";

interface SLAMetric {
  sla_name: string;
  sla_type: string;
  target_value: number;
  current_value: number;
  compliance_percentage: number;
  is_compliant: boolean;
  measurement_window_start: string;
  measurement_window_end: string;
  timestamp: string;
  tags: Record<string, string>;
}

interface SLASummary {
  total_slas: number;
  compliant_slas: number;
  non_compliant_slas: number;
  compliance_rate: number;
  average_compliance_percentage: number;
  sla_metrics: Array<{
    name: string;
    type: string;
    target: number;
    current: number;
    compliant: boolean;
    compliance_percentage: number;
  }>;
}

export default function SLADashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery<SLASummary>({
    queryKey: ["sla", "summary"],
    queryFn: async () => {
      return await apiRequest<SLASummary>("/api/observability/sla/summary", {
        method: "GET",
      });
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: metrics, isLoading: metricsLoading } = useQuery<SLAMetric[]>({
    queryKey: ["sla", "metrics"],
    queryFn: async () => {
      return await apiRequest<SLAMetric[]>("/api/observability/sla/metrics", {
        method: "GET",
      });
    },
    refetchInterval: 30000,
  });

  if (summaryLoading || metricsLoading || !summary || !metrics) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-muted rounded w-24"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-muted rounded w-32 mb-2"></div>
                <div className="h-4 bg-muted rounded w-20"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // Prepare compliance chart data
  const complianceData = [
    {
      name: "Compliant",
      value: summary.compliant_slas,
      color: "hsl(142, 76%, 36%)", // green
    },
    {
      name: "Non-Compliant",
      value: summary.non_compliant_slas,
      color: "hsl(0, 84%, 60%)", // red
    },
  ];

  // Prepare SLA type distribution
  const typeDistribution = metrics.reduce((acc, metric) => {
    const type = metric.sla_type;
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const typeData = Object.entries(typeDistribution).map(([type, count]) => ({
    name: type,
    value: count,
  }));

  // Prepare compliance percentage over time (simplified - would need historical data)
  const complianceHistory = summary.sla_metrics.map((metric, index) => ({
    time: `SLA ${index + 1}`,
    compliance: metric.compliance_percentage,
  }));

  // Get status badge
  const getStatusBadge = (compliant: boolean, percentage: number) => {
    if (compliant) {
      return (
        <Badge variant="default" className="bg-green-500">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Compliant
        </Badge>
      );
    } else if (percentage >= 90) {
      return (
        <Badge variant="default" className="bg-yellow-500">
          <AlertTriangle className="w-3 h-3 mr-1" />
          Warning
        </Badge>
      );
    } else {
      return (
        <Badge variant="destructive">
          <XCircle className="w-3 h-3 mr-1" />
          Non-Compliant
        </Badge>
      );
    }
  };

  return (
    <div className="space-y-6 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">SLA Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time Service Level Agreement monitoring and compliance
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total SLAs</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total_slas}</div>
            <p className="text-xs text-muted-foreground">
              Active service level agreements
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Rate</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.compliance_rate.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {summary.compliant_slas} of {summary.total_slas} compliant
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Compliance</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.average_compliance_percentage.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Average across all SLAs
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Non-Compliant</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {summary.non_compliant_slas}
            </div>
            <p className="text-xs text-muted-foreground">
              Requiring attention
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Compliance Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Compliance Distribution</CardTitle>
            <CardDescription>
              Compliant vs Non-Compliant SLAs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={complianceData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value, percent }) =>
                    `${name}: ${value} (${(percent * 100).toFixed(0)}%)`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {complianceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* SLA Type Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>SLA Type Distribution</CardTitle>
            <CardDescription>Breakdown by metric type</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={typeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="hsl(var(--chart-1))" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* SLA Metrics Table */}
      <Card>
        <CardHeader>
          <CardTitle>SLA Metrics</CardTitle>
          <CardDescription>
            Detailed view of all service level agreements
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">SLA Name</th>
                  <th className="text-left p-2">Type</th>
                  <th className="text-left p-2">Target</th>
                  <th className="text-left p-2">Current</th>
                  <th className="text-left p-2">Compliance</th>
                  <th className="text-left p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {summary.sla_metrics.map((metric) => (
                  <tr key={metric.name} className="border-b">
                    <td className="p-2 font-medium">{metric.name}</td>
                    <td className="p-2">
                      <Badge variant="outline">{metric.type}</Badge>
                    </td>
                    <td className="p-2">
                      {metric.type === "availability"
                        ? `${metric.target.toFixed(2)}%`
                        : metric.type === "latency"
                        ? `${metric.target.toFixed(0)}ms`
                        : metric.type === "error_rate"
                        ? `${metric.target.toFixed(2)}%`
                        : `${metric.target.toFixed(0)} req/s`}
                    </td>
                    <td className="p-2">
                      {metric.type === "availability"
                        ? `${metric.current.toFixed(2)}%`
                        : metric.type === "latency"
                        ? `${metric.current.toFixed(0)}ms`
                        : metric.type === "error_rate"
                        ? `${metric.current.toFixed(2)}%`
                        : `${metric.current.toFixed(0)} req/s`}
                    </td>
                    <td className="p-2">
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-muted rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              metric.compliant
                                ? "bg-green-500"
                                : metric.compliance_percentage >= 90
                                ? "bg-yellow-500"
                                : "bg-red-500"
                            }`}
                            style={{
                              width: `${Math.min(100, metric.compliance_percentage)}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm">
                          {metric.compliance_percentage.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="p-2">
                      {getStatusBadge(metric.compliant, metric.compliance_percentage)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
