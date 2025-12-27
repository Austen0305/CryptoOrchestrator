import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, Shield, AlertTriangle, Activity } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { useToast } from "@/hooks/use-toast";

// Helper to get Tailwind text color class for risk
function getRiskLevelTextColor(risk: number) {
  if (risk < 30) return "text-green-600";
  if (risk < 60) return "text-yellow-600";
  return "text-red-600";
}

// Helper to get Tailwind text color class for Sharpe ratio
function getSharpeTextColor(sharpe: number) {
  if (sharpe > 1) return "text-green-600";
  if (sharpe > 0) return "text-blue-600";
  return "text-red-600";
}

interface RiskMetrics {
  portfolioRisk: number;
  maxDrawdown: number;
  var95: number;
  var99: number;
  sharpeRatio: number;
  correlationScore: number;
  diversificationRatio: number;
  exposureByAsset: Record<string, number>;
  leverageRisk: number;
  liquidityRisk: number;
  concentrationRisk: number;
}

interface RiskAlert {
  id: string;
  type: 'warning' | 'critical' | 'info';
  message: string;
  threshold: number;
  currentValue: number;
  timestamp: number;
  acknowledged: boolean;
}

interface RiskLimits {
  maxPositionSize: number;
  maxDailyLoss: number;
  maxPortfolioRisk: number;
  maxLeverage: number;
  maxCorrelation: number;
  minDiversification: number;
}

export function RiskManagement() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Fetch risk metrics
  const { data: riskMetrics, isLoading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useQuery<RiskMetrics>({
    queryKey: ['risk-metrics'],
    queryFn: async () => {
      return await apiRequest<RiskMetrics>('/api/risk-management/metrics', { method: 'GET' });
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 2,
  });

  // Fetch risk alerts
  const { data: riskAlerts, isLoading: alertsLoading, error: alertsError, refetch: refetchAlerts } = useQuery<RiskAlert[]>({
    queryKey: ['risk-alerts'],
    queryFn: async () => {
      return await apiRequest<RiskAlert[]>('/api/risk-management/alerts', { method: 'GET' });
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 2,
  });

  // Fetch risk limits
  const { data: riskLimits, isLoading: limitsLoading, error: limitsError, refetch: refetchLimits } = useQuery<RiskLimits>({
    queryKey: ['risk-limits'],
    queryFn: async () => {
      return await apiRequest<RiskLimits>('/api/risk-management/limits', { method: 'GET' });
    },
    retry: 2,
  });

  const isLoading = metricsLoading || alertsLoading || limitsLoading;
  const error = metricsError || alertsError || limitsError;

  const acknowledgeAlertMutation = useMutation({
    mutationFn: async (alertId: string) => {
      return await apiRequest(`/api/risk-management/alerts/${alertId}/acknowledge`, {
        method: 'POST',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk-alerts'] });
      toast({
        title: "Alert Acknowledged",
        description: "The risk alert has been acknowledged.",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to acknowledge alert.",
        variant: "destructive",
      });
    },
  });

  const updateRiskLimitsMutation = useMutation({
    mutationFn: async (limits: Partial<RiskLimits>) => {
      return await apiRequest<RiskLimits>('/api/risk-management/limits', {
        method: 'POST',
        body: limits,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk-limits'] });
      toast({
        title: "Risk Limits Updated",
        description: "Your risk limits have been updated successfully.",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to update risk limits.",
        variant: "destructive",
      });
    },
  });

  const acknowledgeAlert = (alertId: string) => {
    acknowledgeAlertMutation.mutate(alertId);
  };

  const updateRiskLimits = (limits: Partial<RiskLimits>) => {
    updateRiskLimitsMutation.mutate(limits);
  };

  const handleRetry = () => {
    refetchMetrics();
    refetchAlerts();
    refetchLimits();
  };

  // helper kept internal; color logic inline where used

  const getRiskLevelBgColor = (risk: number) => {
    if (risk < 30) return 'bg-green-100';
    if (risk < 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default: return <Activity className="w-4 h-4 text-blue-500" />;
    }
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(2)}%`;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Risk Management
          </CardTitle>
          <CardDescription>Loading risk metrics...</CardDescription>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton count={5} className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Risk Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorRetry
            title="Failed to load risk data"
            message={error instanceof Error ? error.message : "Unable to fetch risk management data. Please try again."}
            onRetry={handleRetry}
            error={error as Error}
          />
        </CardContent>
      </Card>
    );
  }

  if (!riskMetrics || !riskLimits) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Risk Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Shield}
            title="No risk data available"
            description="Risk metrics and limits are not available at the moment."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          Risk Management
        </CardTitle>
        <CardDescription>
          Monitor and manage your trading risks
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="metrics" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="metrics">Risk Metrics</TabsTrigger>
            <TabsTrigger value="alerts">Risk Alerts</TabsTrigger>
            <TabsTrigger value="settings">Risk Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="metrics" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Portfolio Risk</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className={`text-2xl font-bold ${getRiskLevelTextColor(riskMetrics.portfolioRisk)}`}>
                        {riskMetrics.portfolioRisk.toFixed(1)}
                      </div>
                      <div className="text-sm text-gray-500">Overall Risk Score</div>
                    </div>
                    <div className="text-right">
                      <Badge className={getRiskLevelBgColor(riskMetrics.portfolioRisk)}>
                        {riskMetrics.portfolioRisk < 30 ? 'Low' : riskMetrics.portfolioRisk < 60 ? 'Medium' : 'High'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Max Drawdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-2xl font-bold text-red-600">
                        {formatPercentage(riskMetrics.maxDrawdown)}
                      </div>
                      <div className="text-sm text-gray-500">Maximum Historical</div>
                    </div>
                    <div className="text-right">
                      <Badge className={riskMetrics.maxDrawdown > 5 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}>
                        {riskMetrics.maxDrawdown > 5 ? 'Critical' : 'Warning'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Value at Risk (VaR)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-2xl font-bold text-blue-600">
                        {formatPercentage(riskMetrics.var95)}
                      </div>
                      <div className="text-sm text-gray-500">95% VaR</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-red-600">
                        {formatPercentage(riskMetrics.var99)}
                      </div>
                      <div className="text-sm text-gray-500">99% VaR</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Sharpe Ratio</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className={`text-2xl font-bold ${getSharpeTextColor(riskMetrics.sharpeRatio)}`}>
                        {riskMetrics.sharpeRatio.toFixed(2)}
                      </div>
                      <div className="text-sm text-gray-500">Risk-Adjusted Return</div>
                    </div>
                    <div className="text-right">
                      <Badge className={riskMetrics.sharpeRatio > 1 ? 'bg-green-100 text-green-800' : riskMetrics.sharpeRatio > 0 ? 'bg-blue-100 text-blue-800' : 'bg-red-100 text-red-800'}>
                        {riskMetrics.sharpeRatio > 1 ? 'Excellent' : riskMetrics.sharpeRatio > 0 ? 'Good' : 'Poor'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Diversification</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className={`text-2xl font-bold ${getRiskLevelTextColor(100 - riskMetrics.diversificationRatio * 100)}`}>
                        {(riskMetrics.diversificationRatio * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-500">Diversification Score</div>
                    </div>
                    <div className="text-right">
                      <Badge className={riskMetrics.diversificationRatio > 0.6 ? 'bg-green-100 text-green-800' : riskMetrics.diversificationRatio > 0.3 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}>
                        {riskMetrics.diversificationRatio > 0.6 ? 'Well Diversified' : riskMetrics.diversificationRatio > 0.3 ? 'Moderately Diversified' : 'Poorly Diversified'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Asset Exposure</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(riskMetrics.exposureByAsset).map(([asset, exposure]) => (
                      <div key={asset} className="flex items-center justify-between">
                        <div>
                          <div className="font-semibold">{asset}</div>
                          <div className="text-sm text-gray-500">Asset</div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold">{formatPercentage(exposure)}</div>
                          <div className="text-sm text-gray-500">Exposure</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="alerts" className="space-y-4">
            {!riskAlerts || riskAlerts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <AlertCircle className="w-8 h-8 mx-auto mb-4" />
                <p className="text-lg">No Risk Alerts</p>
                <p className="text-sm">Your portfolio is currently within all risk parameters</p>
              </div>
            ) : (
              <div className="space-y-3">
                {riskAlerts.map(alert => (
                  <Card key={alert.id} className={`border-l-4 ${
                    alert.type === 'critical' ? 'border-l-red-500' : 
                    alert.type === 'warning' ? 'border-l-yellow-500' : 'border-l-blue-500'
                  }`}>
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          {getAlertIcon(alert.type)}
                          <div>
                            <div className="font-semibold">{alert.type === 'critical' ? 'Critical Risk Alert' : 'Risk Warning'}</div>
                            <div className="text-sm text-gray-500">
                              {new Date(alert.timestamp).toLocaleString()}
                            </div>
                          </div>
                        </div>
                        <Badge className={`${
                          alert.type === 'critical' ? 'bg-red-100 text-red-800' : 
                          alert.type === 'warning' ? 'bg-yellow-100 text-yellow-800' : 
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {alert.type === 'critical' ? 'Critical' : alert.type === 'warning' ? 'Warning' : 'Info'}
                        </Badge>
                      </div>

                      <div className="mb-3">
                        <p className="text-sm">{alert.message}</p>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm text-gray-500">Current Value:</div>
                          <div className="font-semibold">{formatPercentage(alert.currentValue)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-500">Threshold:</div>
                          <div className="font-semibold">{formatPercentage(alert.threshold)}</div>
                        </div>
                      </div>
                    </CardContent>

                    {!alert.acknowledged && (
                      <div className="px-4 py-3 border-t">
                        <Button
                          size="sm"
                          onClick={() => acknowledgeAlert(alert.id)}
                          className="w-full"
                        >
                          Acknowledge Alert
                        </Button>
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            {riskLimits && (
              <div className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Position Size Limit</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="text-2xl font-bold">{riskLimits.maxPositionSize}%</div>
                        <div className="text-sm text-gray-500">Maximum Position Size</div>
                      </div>
                      <div className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateRiskLimits({ maxPositionSize: Math.min(50, riskLimits.maxPositionSize + 5) })}
                        >
                          Increase
                        </Button>
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      Limit position size to a percentage of portfolio value
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Daily Loss Limit</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="text-2xl font-bold">{riskLimits.maxDailyLoss}%</div>
                        <div className="text-sm text-gray-500">Maximum Daily Loss</div>
                      </div>
                      <div className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateRiskLimits({ maxDailyLoss: Math.min(10, riskLimits.maxDailyLoss + 1) })}
                        >
                          Increase
                        </Button>
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      Maximum percentage loss allowed per day
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Portfolio Risk Limit</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="text-2xl font-bold">{riskLimits.maxPortfolioRisk}</div>
                        <div className="text-sm text-gray-500">Maximum Risk Score</div>
                      </div>
                      <div className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateRiskLimits({ maxPortfolioRisk: Math.min(80, riskLimits.maxPortfolioRisk + 10) })}
                        >
                          Increase
                        </Button>
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      Maximum overall risk score (0-100)
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Leverage Limit</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="text-2xl font-bold">{riskLimits.maxLeverage}x</div>
                        <div className="text-sm text-gray-500">Maximum Leverage</div>
                      </div>
                      <div className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateRiskLimits({ maxLeverage: Math.min(5, riskLimits.maxLeverage + 1) })}
                        >
                          Increase
                        </Button>
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      Maximum allowed leverage multiplier
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Diversification Requirement</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <div className="text-2xl font-bold">{(riskLimits.minDiversification * 100).toFixed(1)}%</div>
                        <div className="text-sm text-gray-500">Minimum Diversification</div>
                      </div>
                      <div className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateRiskLimits({ minDiversification: Math.max(0.3, riskLimits.minDiversification - 0.1) })}
                        >
                          Decrease
                        </Button>
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      Minimum diversification score required
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
