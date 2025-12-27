/**
 * Treasury Dashboard
 * Comprehensive treasury management for institutional wallets
 */

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  TrendingUp,
  TrendingDown,
  DollarSign,
  Wallet,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useParams } from "wouter";

interface TreasurySummary {
  total_balance_usd: number;
  total_wallets: number;
  active_wallets: number;
  total_transactions_24h: number;
  total_volume_24h: number;
  risk_score: number;
  risk_level: string;
}

interface TreasuryBalance {
  wallet_id: string;
  wallet_name: string;
  balance_usd: number;
  currency: string;
  balance_native: number;
  last_activity: string;
  status: string;
}

interface TreasuryActivity {
  id: string;
  wallet_id: string;
  transaction_type: string;
  amount: number;
  currency: string;
  timestamp: string;
  status: string;
  description?: string;
}

interface RiskMetrics {
  concentration_risk: number;
  liquidity_risk: number;
  operational_risk: number;
  overall_risk_score: number;
  risk_level: string;
}

export default function TreasuryDashboard() {
  const { walletId } = useParams<{ walletId?: string }>();
  const [selectedWallet, setSelectedWallet] = useState<string | null>(walletId || null);
  const [timeRange, setTimeRange] = useState<string>("24h");

  // Fetch treasury summary
  const { data: summary, isLoading: summaryLoading } = useQuery<TreasurySummary>({
    queryKey: ["/api/institutional/treasury/summary", selectedWallet],
  });

  // Fetch treasury balances
  const { data: balances, isLoading: balancesLoading } = useQuery<TreasuryBalance[]>({
    queryKey: ["/api/institutional/treasury/balances", selectedWallet],
  });

  // Fetch treasury activity
  const { data: activity, isLoading: activityLoading } = useQuery<TreasuryActivity[]>({
    queryKey: ["/api/institutional/treasury/activity", selectedWallet, timeRange],
  });

  // Fetch risk metrics
  const { data: riskMetrics, isLoading: riskLoading } = useQuery<RiskMetrics>({
    queryKey: ["/api/institutional/treasury/risk-metrics", selectedWallet],
  });

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const getRiskBadge = (riskLevel: string) => {
    const variants: Record<string, "default" | "destructive" | "secondary"> = {
      low: "default",
      medium: "secondary",
      high: "destructive",
      critical: "destructive",
    };

    const colors: Record<string, string> = {
      low: "bg-green-500",
      medium: "bg-yellow-500",
      high: "bg-orange-500",
      critical: "bg-red-500",
    };

    return (
      <Badge variant={variants[riskLevel] || "secondary"} className={colors[riskLevel] || ""}>
        {riskLevel.toUpperCase()}
      </Badge>
    );
  };

  // Prepare chart data
  const balanceChartData = balances?.map((b) => ({
    name: b.wallet_name,
    balance: b.balance_usd,
  })) || [];

  const activityChartData = activity?.reduce((acc, act) => {
    const date = new Date(act.timestamp).toLocaleDateString();
    const existing = acc.find((item) => item.date === date);
    if (existing) {
      existing.count += 1;
      existing.volume += act.amount;
    } else {
      acc.push({ date, count: 1, volume: act.amount });
    }
    return acc;
  }, [] as Array<{ date: string; count: number; volume: number }>) || [];

  const currencyDistribution = balances?.reduce((acc, b) => {
    const existing = acc.find((item) => item.currency === b.currency);
    if (existing) {
      existing.value += b.balance_usd;
    } else {
      acc.push({ currency: b.currency, value: b.balance_usd });
    }
    return acc;
  }, [] as Array<{ currency: string; value: number }>) || [];

  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];

  if (summaryLoading || balancesLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Loading treasury data...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Treasury Dashboard</h1>
          <p className="text-muted-foreground">Comprehensive treasury management and monitoring</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border rounded-md"
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary ? formatCurrency(summary.total_balance_usd) : "$0.00"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Across {summary?.total_wallets || 0} wallets
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Wallets</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.active_wallets || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              of {summary?.total_wallets || 0} total wallets
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">24h Volume</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary ? formatCurrency(summary.total_volume_24h) : "$0.00"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {summary?.total_transactions_24h || 0} transactions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk Score</CardTitle>
            {riskMetrics?.risk_level === "low" ? (
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {riskMetrics ? riskMetrics.overall_risk_score.toFixed(1) : "0.0"}
            </div>
            <div className="mt-1">
              {riskMetrics ? getRiskBadge(riskMetrics.risk_level) : null}
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="balances">Balances</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="risk">Risk Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Balance Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Balance Distribution</CardTitle>
                <CardDescription>Balance across wallets</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={balanceChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                    <Bar dataKey="balance" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Currency Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Currency Distribution</CardTitle>
                <CardDescription>Balance by currency</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={currencyDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ currency, percent }) => `${currency}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {currencyDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Activity Trend */}
          <Card>
            <CardHeader>
              <CardTitle>Activity Trend</CardTitle>
              <CardDescription>Transaction volume over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={activityChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="count" stroke="#8884d8" name="Transactions" />
                  <Line type="monotone" dataKey="volume" stroke="#82ca9d" name="Volume (USD)" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="balances" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Wallet Balances</CardTitle>
              <CardDescription>Detailed balance information for all wallets</CardDescription>
            </CardHeader>
            <CardContent>
              {!balances || balances.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No wallets found</div>
              ) : (
                <div className="space-y-2">
                  {balances.map((balance) => (
                    <div
                      key={balance.wallet_id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedWallet === balance.wallet_id
                          ? "border-primary bg-primary/5"
                          : "hover:bg-muted"
                      }`}
                      onClick={() => setSelectedWallet(balance.wallet_id)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold">{balance.wallet_name}</h3>
                          <p className="text-sm text-muted-foreground">
                            {balance.currency}: {balance.balance_native.toFixed(6)}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="font-bold">{formatCurrency(balance.balance_usd)}</div>
                          <Badge variant={balance.status === "active" ? "default" : "secondary"}>
                            {balance.status}
                          </Badge>
                        </div>
                      </div>
                      <div className="mt-2 text-xs text-muted-foreground">
                        Last activity: {formatDate(balance.last_activity)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Transaction history</CardDescription>
            </CardHeader>
            <CardContent>
              {!activity || activity.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No activity found</div>
              ) : (
                <div className="space-y-2">
                  {activity.map((act) => (
                    <div key={act.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {act.transaction_type === "deposit" ? (
                            <ArrowDownRight className="h-4 w-4 text-green-500" />
                          ) : (
                            <ArrowUpRight className="h-4 w-4 text-red-500" />
                          )}
                          <div>
                            <div className="font-medium">{act.transaction_type}</div>
                            {act.description && (
                              <div className="text-sm text-muted-foreground">{act.description}</div>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold">
                            {act.transaction_type === "deposit" ? "+" : "-"}
                            {formatCurrency(act.amount)}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {formatDate(act.timestamp)}
                          </div>
                        </div>
                      </div>
                      <div className="mt-2 flex items-center gap-2">
                        <Badge variant="outline">{act.currency}</Badge>
                        <Badge
                          variant={
                            act.status === "completed"
                              ? "default"
                              : act.status === "pending"
                              ? "secondary"
                              : "destructive"
                          }
                        >
                          {act.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          {riskMetrics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Risk Metrics</CardTitle>
                  <CardDescription>Detailed risk analysis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm">Concentration Risk</span>
                      <span className="font-medium">{riskMetrics.concentration_risk.toFixed(1)}</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${riskMetrics.concentration_risk}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm">Liquidity Risk</span>
                      <span className="font-medium">{riskMetrics.liquidity_risk.toFixed(1)}</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${riskMetrics.liquidity_risk}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm">Operational Risk</span>
                      <span className="font-medium">{riskMetrics.operational_risk.toFixed(1)}</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${riskMetrics.operational_risk}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-4 border-t">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold">Overall Risk Score</span>
                      <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold">{riskMetrics.overall_risk_score.toFixed(1)}</span>
                        {getRiskBadge(riskMetrics.risk_level)}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Risk Recommendations</CardTitle>
                  <CardDescription>Suggested actions based on risk analysis</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {riskMetrics.overall_risk_score > 70 && (
                      <div className="p-3 bg-destructive/10 border border-destructive/20 rounded">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-destructive" />
                          <span className="text-sm font-medium">High Risk Detected</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          Consider diversifying holdings and reviewing operational procedures.
                        </p>
                      </div>
                    )}
                    {riskMetrics.concentration_risk > 50 && (
                      <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          <span className="text-sm font-medium">Concentration Risk</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          Consider diversifying across multiple wallets and currencies.
                        </p>
                      </div>
                    )}
                    {riskMetrics.liquidity_risk > 50 && (
                      <div className="p-3 bg-orange-500/10 border border-orange-500/20 rounded">
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-orange-500" />
                          <span className="text-sm font-medium">Liquidity Risk</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          Ensure sufficient liquid assets are available for operations.
                        </p>
                      </div>
                    )}
                    {riskMetrics.overall_risk_score <= 30 && (
                      <div className="p-3 bg-green-500/10 border border-green-500/20 rounded">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                          <span className="text-sm font-medium">Low Risk Profile</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          Treasury is well-diversified and operating within acceptable risk parameters.
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="py-8">
                <div className="text-center text-muted-foreground">
                  {riskLoading ? "Loading risk metrics..." : "No risk metrics available"}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
