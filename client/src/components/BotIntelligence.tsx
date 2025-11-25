import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Brain, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Shield, 
  Target,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  BarChart3,
  Zap
} from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";

interface BotIntelligenceProps {
  botId: string;
}

interface MarketAnalysis {
  action: string;
  confidence: number;
  strength: number;
  risk_score: number;
  reasoning: string[];
  patterns_detected?: string[];
  order_flow?: {
    buy_pressure: number;
    signal: string;
  };
  volume_profile?: {
    poc: number;
    position: string;
  };
  ml_prediction?: {
    prediction: string;
    confidence: number;
  };
  timestamp: string;
}

interface RiskMetrics {
  overall_risk_score: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  current_confidence: number;
  market_regime: string;
  timestamp: string;
}

interface OptimizedParams {
  market_regime: string;
  confidence_threshold: number;
  position_multiplier: number;
  risk_per_trade: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  trailing_stop_enabled: boolean;
  adaptive_reasoning: string[];
}

export function BotIntelligence({ botId }: BotIntelligenceProps) {
  const [activeTab, setActiveTab] = useState("analysis");
  const { isAuthenticated } = useAuth();
  const [isOptimizing, setIsOptimizing] = useState(false);

  const { data: analysis, isLoading: analysisLoading, refetch: refetchAnalysis, error: analysisError } = useQuery<{
    analysis: MarketAnalysis;
    market_condition: string;
  }>({
    queryKey: ["bots", botId, "analysis"],
    queryFn: async () => {
      const response = await apiRequest("GET", `/api/bots/${botId}/analysis`);
      return response.json();
    },
    enabled: isAuthenticated && !!botId,
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 2,
  });

  const { data: riskMetrics, isLoading: riskLoading, refetch: refetchRisk, error: riskError } = useQuery<{
    risk_metrics: RiskMetrics;
    recommendations: {
      suggested_position_size: string;
      stop_loss_adjustment: string;
      warnings: (string | null)[];
    };
  }>({
    queryKey: ["bots", botId, "risk-metrics"],
    queryFn: async () => {
      const response = await apiRequest("GET", `/api/bots/${botId}/risk-metrics`);
      return response.json();
    },
    enabled: isAuthenticated && !!botId,
    refetchInterval: 60000, // Refresh every minute
    retry: 2,
  });

  const optimizeMutation = useMutation<{
    optimized_parameters: OptimizedParams;
  }>({
    mutationFn: async () => {
      const response = await apiRequest("POST", `/api/bots/${botId}/optimize`);
      return response.json();
    },
    onMutate: () => {
      setIsOptimizing(true);
    },
    onSettled: () => {
      setIsOptimizing(false);
    },
  });

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'buy': return <TrendingUp className="h-5 w-5 text-green-500" />;
      case 'sell': return <TrendingDown className="h-5 w-5 text-red-500" />;
      default: return <Activity className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getRiskColor = (risk: number) => {
    if (risk < 0.3) return 'text-green-500';
    if (risk < 0.5) return 'text-yellow-500';
    if (risk < 0.7) return 'text-orange-500';
    return 'text-red-500';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.75) return 'text-green-500';
    if (confidence >= 0.6) return 'text-yellow-500';
    return 'text-orange-500';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-6 w-6 text-purple-500" />
            <div>
              <CardTitle>AI Intelligence</CardTitle>
              <CardDescription>Advanced market analysis & insights</CardDescription>
            </div>
          </div>
          <Badge variant="outline" className="gap-1">
            <Sparkles className="h-3 w-3" />
            Smart Engine v2.0
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="analysis" className="gap-1">
              <BarChart3 className="h-4 w-4" />
              Analysis
            </TabsTrigger>
            <TabsTrigger value="risk" className="gap-1">
              <Shield className="h-4 w-4" />
              Risk
            </TabsTrigger>
            <TabsTrigger value="optimize" className="gap-1">
              <Zap className="h-4 w-4" />
              Optimize
            </TabsTrigger>
          </TabsList>

          {/* Analysis Tab */}
          <TabsContent value="analysis" className="space-y-4 mt-4">
            {analysisError && (
              <div className="rounded-md border border-red-500/50 bg-red-500/10 p-4 text-sm text-red-500">
                Failed to load analysis. Please try again.
              </div>
            )}
            {analysisLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin" />
                Loading analysis...
              </div>
            ) : analysis?.analysis ? (
              <>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getActionIcon(analysis.analysis.action)}
                    <div>
                      <p className="text-sm text-muted-foreground">Current Signal</p>
                      <p className="text-2xl font-bold capitalize">{analysis.analysis.action}</p>
                    </div>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => refetchAnalysis()}>
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Refresh
                  </Button>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Confidence</p>
                    <p className={`text-xl font-bold ${getConfidenceColor(analysis.analysis.confidence)}`}>
                      {(analysis.analysis.confidence * 100).toFixed(0)}%
                    </p>
                    <Progress value={analysis.analysis.confidence * 100} className="h-2 mt-1" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Signal Strength</p>
                    <p className="text-xl font-bold">{analysis.analysis.strength.toFixed(2)}</p>
                    <Progress value={analysis.analysis.strength * 100} className="h-2 mt-1" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Risk Score</p>
                    <p className={`text-xl font-bold ${getRiskColor(analysis.analysis.risk_score)}`}>
                      {analysis.analysis.risk_score.toFixed(2)}
                    </p>
                    <Progress 
                      value={analysis.analysis.risk_score * 100} 
                      className="h-2 mt-1"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4 text-muted-foreground" />
                    <p className="text-sm font-medium">Market Regime: 
                      <Badge variant="outline" className="ml-2 capitalize">
                        {analysis.market_condition}
                      </Badge>
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    AI Reasoning ({analysis.analysis.reasoning.length} factors)
                  </p>
                  <div className="space-y-1.5">
                    {analysis.analysis.reasoning.map((reason, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-sm bg-muted/50 p-2 rounded">
                        <span className="text-muted-foreground mt-0.5">•</span>
                        <span>{reason}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {analysis.analysis.patterns_detected && analysis.analysis.patterns_detected.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Chart Patterns Detected</p>
                    <div className="flex flex-wrap gap-2">
                      {analysis.analysis.patterns_detected.map((pattern, idx) => (
                        <Badge key={idx} variant="secondary" className="capitalize">
                          {pattern.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {analysis.analysis.order_flow && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-muted/30 p-3 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Order Flow</p>
                      <p className="text-sm font-medium capitalize">{analysis.analysis.order_flow.signal}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Buy Pressure: {(analysis.analysis.order_flow.buy_pressure * 100).toFixed(0)}%
                      </p>
                    </div>
                    {analysis.analysis.ml_prediction && (
                      <div className="bg-muted/30 p-3 rounded-lg">
                        <p className="text-xs text-muted-foreground mb-1">ML Prediction</p>
                        <p className="text-sm font-medium capitalize">{analysis.analysis.ml_prediction.prediction}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Confidence: {(analysis.analysis.ml_prediction.confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No analysis data available
              </div>
            )}
          </TabsContent>

          {/* Risk Tab */}
          <TabsContent value="risk" className="space-y-4 mt-4">
            {riskError && (
              <div className="rounded-md border border-red-500/50 bg-red-500/10 p-4 text-sm text-red-500">
                Failed to load risk metrics. Please try again.
              </div>
            )}
            {riskLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin" />
                Loading risk metrics...
              </div>
            ) : riskMetrics?.risk_metrics ? (
              <>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Shield className={`h-6 w-6 ${getRiskColor(riskMetrics.risk_metrics.overall_risk_score)}`} />
                    <div>
                      <p className="text-sm text-muted-foreground">Overall Risk</p>
                      <p className={`text-2xl font-bold ${getRiskColor(riskMetrics.risk_metrics.overall_risk_score)}`}>
                        {riskMetrics.risk_metrics.overall_risk_score.toFixed(2)}
                      </p>
                    </div>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => refetchRisk()}>
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Refresh
                  </Button>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-muted/30 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Volatility</p>
                    <p className="text-lg font-bold">{(riskMetrics.risk_metrics.volatility * 100).toFixed(1)}%</p>
                  </div>
                  <div className="bg-muted/30 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Sharpe Ratio</p>
                    <p className="text-lg font-bold">{riskMetrics.risk_metrics.sharpe_ratio.toFixed(2)}</p>
                  </div>
                  <div className="bg-muted/30 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Max Drawdown</p>
                    <p className="text-lg font-bold text-red-500">
                      {(riskMetrics.risk_metrics.max_drawdown * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-muted/30 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Market Regime</p>
                    <p className="text-lg font-bold capitalize">{riskMetrics.risk_metrics.market_regime}</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium">Recommendations</p>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Badge variant="outline">Position Size</Badge>
                      <span className="capitalize">{riskMetrics.recommendations.suggested_position_size}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Badge variant="outline">Stop Loss</Badge>
                      <span className="capitalize">{riskMetrics.recommendations.stop_loss_adjustment}</span>
                    </div>
                  </div>
                </div>

                {riskMetrics.recommendations.warnings.filter(w => w !== null).length > 0 && (
                  <div className="space-y-2 border-t pt-3">
                    <p className="text-sm font-medium flex items-center gap-2 text-orange-500">
                      <AlertTriangle className="h-4 w-4" />
                      Warnings
                    </p>
                    <div className="space-y-1.5">
                      {riskMetrics.recommendations.warnings
                        .filter(w => w !== null)
                        .map((warning, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-sm bg-orange-500/10 p-2 rounded border border-orange-500/20">
                            <span className="text-orange-500 mt-0.5">⚠</span>
                            <span>{warning}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No risk data available
              </div>
            )}
          </TabsContent>

          {/* Optimize Tab */}
          <TabsContent value="optimize" className="space-y-4 mt-4">
            <div className="text-center space-y-4">
              <p className="text-sm text-muted-foreground">
                Optimize bot parameters based on current market conditions and historical performance
              </p>
              <Button 
                onClick={() => optimizeMutation.mutate()} 
                disabled={isOptimizing || optimizeMutation.isPending || !isAuthenticated}
              >
                {isOptimizing || optimizeMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Optimizing...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Run Optimization
                  </>
                )}
              </Button>
              {optimizeMutation.error && (
                <div className="rounded-md border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-500">
                  Optimization failed. Please try again.
                </div>
              )}
            </div>

            {optimizeMutation.data?.optimized_parameters && (
              <div className="space-y-4 mt-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <p className="font-medium">Optimized Parameters Ready</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-muted/30 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Market Regime</p>
                    <p className="text-sm font-medium capitalize">{optimizeMutation.data.optimized_parameters.market_regime}</p>
                  </div>
                  <div className="bg-muted/30 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Confidence Threshold</p>
                    <p className="text-sm font-medium">{(optimizeMutation.data.optimized_parameters.confidence_threshold * 100).toFixed(0)}%</p>
                  </div>
                  <div className="bg-muted/30 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Position Multiplier</p>
                    <p className="text-sm font-medium">{optimizeMutation.data.optimized_parameters.position_multiplier.toFixed(2)}x</p>
                  </div>
                  <div className="bg-muted/30 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Risk Per Trade</p>
                    <p className="text-sm font-medium">{(optimizeMutation.data.optimized_parameters.risk_per_trade * 100).toFixed(1)}%</p>
                  </div>
                  <div className="bg-muted/30 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Stop Loss</p>
                    <p className="text-sm font-medium">{(optimizeMutation.data.optimized_parameters.stop_loss_pct * 100).toFixed(1)}%</p>
                  </div>
                  <div className="bg-muted/30 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Take Profit</p>
                    <p className="text-sm font-medium">{(optimizeMutation.data.optimized_parameters.take_profit_pct * 100).toFixed(1)}%</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium">Adaptive Reasoning</p>
                  <div className="space-y-1.5">
                    {optimizeMutation.data.optimized_parameters.adaptive_reasoning.map((reason, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-sm bg-muted/50 p-2 rounded">
                        <span className="text-muted-foreground mt-0.5">•</span>
                        <span>{reason}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <Button className="w-full" variant="default">
                  Apply Optimized Parameters
                </Button>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
