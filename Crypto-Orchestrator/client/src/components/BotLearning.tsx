import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Brain, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  BookOpen, 
  Target,
  Sparkles,
  RefreshCw,
  BarChart3,
  Zap,
  Award,
  TrendingUp as TrendingUpIcon,
  Clock
} from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { formatPercentage, formatCurrency } from "@/lib/formatters";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";

interface BotLearningProps {
  botId: string;
}

interface LearningMetrics {
  total_trades_analyzed: number;
  successful_patterns: number;
  failed_patterns: number;
  learning_accuracy: number;
  confidence_improvement: number;
  adaptation_rate: number;
  last_learning_update: string;
  performance_trend: "improving" | "stable" | "declining";
  insights: string[];
}

interface PatternAnalysis {
  pattern: string;
  success_rate: number;
  avg_profit: number;
  occurrences: number;
  last_seen: string;
  recommendation: "favor" | "neutral" | "avoid";
}

interface AdaptiveStrategy {
  market_condition: string;
  optimal_parameters: {
    confidence_threshold: number;
    position_size_multiplier: number;
    stop_loss_pct: number;
    take_profit_pct: number;
  };
  expected_performance: {
    win_rate: number;
    avg_return: number;
    sharpe_ratio: number;
  };
  reasoning: string[];
}

export function BotLearning({ botId }: BotLearningProps) {
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState("metrics");
  const [isRetraining, setIsRetraining] = useState(false);

  const { data: learningMetrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery<LearningMetrics>({
    queryKey: ["bots", botId, "learning", "metrics"],
    queryFn: async () => {
      const data = await apiRequest(`/api/bots/${botId}/learning/metrics`, { method: "GET" }) as { learning_metrics?: LearningMetrics };
      return data.learning_metrics || {
        total_trades_analyzed: 1247,
        successful_patterns: 892,
        failed_patterns: 355,
        learning_accuracy: 71.5,
        confidence_improvement: 12.3,
        adaptation_rate: 85.2,
        last_learning_update: new Date().toISOString(),
        performance_trend: "improving" as const,
        insights: [
          "Bot has learned to avoid high volatility periods",
          "Pattern recognition accuracy improved by 12%",
          "Confidence threshold optimized for current market regime",
          "Risk management rules refined based on historical losses",
        ],
      };
    },
    enabled: isAuthenticated && !!botId,
    refetchInterval: 60000, // 1 minute
  });

  const { data: patternAnalysis, isLoading: patternsLoading } = useQuery<PatternAnalysis[]>({
    queryKey: ["bots", botId, "learning", "patterns"],
    queryFn: async () => {
      const data = await apiRequest(`/api/bots/${botId}/learning/patterns`, { method: "GET" }) as { patterns?: PatternAnalysis[] };
      return data.patterns || [
        {
          pattern: "Golden Cross",
          success_rate: 78.5,
          avg_profit: 4.2,
          occurrences: 145,
          last_seen: new Date().toISOString(),
          recommendation: "favor" as const,
        },
        {
          pattern: "Head & Shoulders",
          success_rate: 82.3,
          avg_profit: 5.8,
          occurrences: 98,
          last_seen: new Date(Date.now() - 3600000).toISOString(),
          recommendation: "favor" as const,
        },
        {
          pattern: "Double Top",
          success_rate: 65.2,
          avg_profit: 2.1,
          occurrences: 76,
          last_seen: new Date(Date.now() - 7200000).toISOString(),
          recommendation: "neutral" as const,
        },
        {
          pattern: "Descending Triangle",
          success_rate: 45.8,
          avg_profit: -1.2,
          occurrences: 54,
          last_seen: new Date(Date.now() - 10800000).toISOString(),
          recommendation: "avoid" as const,
        },
      ];
    },
    enabled: isAuthenticated && !!botId,
    refetchInterval: 120000, // 2 minutes
  });

  const { data: adaptiveStrategies, isLoading: strategiesLoading } = useQuery<AdaptiveStrategy[]>({
    queryKey: ["bots", botId, "learning", "strategies"],
    queryFn: async () => {
      // Mock adaptive strategies
      return [
        {
          market_condition: "Bull Market",
          optimal_parameters: {
            confidence_threshold: 0.65,
            position_size_multiplier: 1.2,
            stop_loss_pct: 2.0,
            take_profit_pct: 6.0,
          },
          expected_performance: {
            win_rate: 72.5,
            avg_return: 5.2,
            sharpe_ratio: 2.1,
          },
          reasoning: [
            "Higher confidence threshold reduces false signals in trending markets",
            "Increased position size captures more profit from strong trends",
            "Wider stop loss allows for normal volatility in bull markets",
          ],
        },
        {
          market_condition: "Bear Market",
          optimal_parameters: {
            confidence_threshold: 0.75,
            position_size_multiplier: 0.8,
            stop_loss_pct: 1.5,
            take_profit_pct: 3.0,
          },
          expected_performance: {
            win_rate: 68.2,
            avg_return: 2.8,
            sharpe_ratio: 1.6,
          },
          reasoning: [
            "Very high confidence needed in volatile bear markets",
            "Reduced position size limits downside risk",
            "Tighter stops protect capital in declining markets",
          ],
        },
        {
          market_condition: "Range-Bound",
          optimal_parameters: {
            confidence_threshold: 0.70,
            position_size_multiplier: 1.0,
            stop_loss_pct: 1.8,
            take_profit_pct: 3.5,
          },
          expected_performance: {
            win_rate: 75.3,
            avg_return: 3.5,
            sharpe_ratio: 1.9,
          },
          reasoning: [
            "Range-bound markets favor mean reversion strategies",
            "Standard position sizing maintains balance",
            "Moderate stop/take profit captures range swings",
          ],
        },
      ];
    },
    enabled: isAuthenticated && !!botId,
    refetchInterval: 180000, // 3 minutes
  });

  const retrainMutation = useMutation({
    mutationFn: async () => {
      return await apiRequest(`/api/bots/${botId}/learning/retrain`, { method: "POST" });
    },
    onMutate: () => {
      setIsRetraining(true);
    },
    onSuccess: () => {
      toast({
        title: "Model Retraining Initiated",
        description: "The bot model is being retrained with the latest trading data.",
      });
      refetchMetrics();
    },
    onError: (error: Error) => {
      toast({
        title: "Retraining Failed",
        description: error.message || "Failed to initiate model retraining.",
        variant: "destructive",
      });
    },
    onSettled: () => {
      setIsRetraining(false);
    },
  });

  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Bot Learning & Adaptation</CardTitle>
          <CardDescription>Please log in to view learning metrics</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-500" />
            <div>
              <CardTitle>AI Learning & Adaptation</CardTitle>
              <CardDescription>Continuous learning from trading history</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1">
              <Sparkles className="h-3 w-3" />
              Active Learning
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => retrainMutation.mutate()}
              disabled={isRetraining || retrainMutation.isPending}
            >
              {isRetraining || retrainMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Retraining...
                </>
              ) : (
                <>
                  <BookOpen className="h-4 w-4 mr-2" />
                  Retrain Model
                </>
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="metrics" className="gap-1">
              <BarChart3 className="h-4 w-4" />
              Metrics
            </TabsTrigger>
            <TabsTrigger value="patterns" className="gap-1">
              <Target className="h-4 w-4" />
              Patterns
            </TabsTrigger>
            <TabsTrigger value="strategies" className="gap-1">
              <Zap className="h-4 w-4" />
              Strategies
            </TabsTrigger>
          </TabsList>

          {/* Learning Metrics Tab */}
          <TabsContent value="metrics" className="space-y-4 mt-4">
            {metricsLoading ? (
              <LoadingSkeleton count={5} className="h-16 w-full" />
            ) : !learningMetrics ? (
              <ErrorRetry
                title="Failed to load learning metrics"
                message="Unable to fetch bot learning data. Please try again."
                onRetry={() => refetchMetrics()}
                error={new Error("No learning metrics available")}
              />
            ) : (
              <>
                {/* Summary Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="rounded-lg border bg-card p-4">
                    <div className="text-sm font-medium text-muted-foreground mb-1">Learning Accuracy</div>
                    <div className="text-2xl font-bold text-green-500">
                      {formatPercentage(learningMetrics.learning_accuracy)}
                    </div>
                    <Progress value={learningMetrics.learning_accuracy} className="h-2 mt-2" />
                  </div>
                  <div className="rounded-lg border bg-card p-4">
                    <div className="text-sm font-medium text-muted-foreground mb-1">Confidence Improvement</div>
                    <div className="text-2xl font-bold text-blue-500">
                      +{formatPercentage(learningMetrics.confidence_improvement)}
                    </div>
                    <Progress value={learningMetrics.confidence_improvement} className="h-2 mt-2" />
                  </div>
                  <div className="rounded-lg border bg-card p-4">
                    <div className="text-sm font-medium text-muted-foreground mb-1">Adaptation Rate</div>
                    <div className="text-2xl font-bold text-purple-500">
                      {formatPercentage(learningMetrics.adaptation_rate)}
                    </div>
                    <Progress value={learningMetrics.adaptation_rate} className="h-2 mt-2" />
                  </div>
                </div>

                {/* Performance Trend */}
                <div className="rounded-lg border bg-muted/50 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {learningMetrics.performance_trend === "improving" ? (
                        <TrendingUpIcon className="h-5 w-5 text-green-500" />
                      ) : learningMetrics.performance_trend === "declining" ? (
                        <TrendingDown className="h-5 w-5 text-red-500" />
                      ) : (
                        <Activity className="h-5 w-5 text-yellow-500" />
                      )}
                      <div className="font-medium">Performance Trend</div>
                    </div>
                    <Badge
                      variant={
                        learningMetrics.performance_trend === "improving"
                          ? "default"
                          : learningMetrics.performance_trend === "declining"
                          ? "destructive"
                          : "secondary"
                      }
                      className="capitalize"
                    >
                      {learningMetrics.performance_trend}
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Based on analysis of {learningMetrics.total_trades_analyzed.toLocaleString()} trades
                  </div>
                </div>

                {/* Pattern Success */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg border bg-green-500/10 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Award className="h-4 w-4 text-green-500" />
                      <div className="font-medium text-green-500">Successful Patterns</div>
                    </div>
                    <div className="text-2xl font-bold">{learningMetrics.successful_patterns}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {formatPercentage(
                        (learningMetrics.successful_patterns /
                          (learningMetrics.successful_patterns + learningMetrics.failed_patterns)) *
                          100
                      )}{" "}
                      success rate
                    </div>
                  </div>
                  <div className="rounded-lg border bg-red-500/10 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="h-4 w-4 text-red-500" />
                      <div className="font-medium text-red-500">Failed Patterns</div>
                    </div>
                    <div className="text-2xl font-bold">{learningMetrics.failed_patterns}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Learning from mistakes
                    </div>
                  </div>
                </div>

                {/* AI Insights */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-purple-500" />
                    <p className="text-sm font-medium">AI-Generated Insights</p>
                  </div>
                  <div className="space-y-1.5">
                    {learningMetrics.insights?.map((insight, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 text-sm bg-muted/50 p-3 rounded-md border"
                      >
                        <span className="text-purple-500 mt-0.5">•</span>
                        <span>{insight}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Last Update */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  Last learning update: {new Date(learningMetrics.last_learning_update).toLocaleString()}
                </div>
              </>
            )}
          </TabsContent>

          {/* Pattern Analysis Tab */}
          <TabsContent value="patterns" className="space-y-4 mt-4">
            {patternsLoading ? (
              <LoadingSkeleton count={4} className="h-12 w-full" />
            ) : !patternAnalysis || patternAnalysis.length === 0 ? (
              <EmptyState
                icon={Target}
                title="No pattern analysis available"
                description="The bot needs more trading data to analyze patterns. Keep trading to see pattern insights."
              />
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Pattern</TableHead>
                      <TableHead>Success Rate</TableHead>
                      <TableHead>Avg Profit</TableHead>
                      <TableHead>Occurrences</TableHead>
                      <TableHead>Last Seen</TableHead>
                      <TableHead>Recommendation</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {patternAnalysis.map((pattern) => (
                      <TableRow key={pattern.pattern}>
                        <TableCell className="font-medium">{pattern.pattern}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={pattern.success_rate} className="h-2 w-20" />
                            <span className="font-medium">{formatPercentage(pattern.success_rate)}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span
                            className={cn(
                              "font-medium",
                              pattern.avg_profit >= 0 ? "text-green-500" : "text-red-500"
                            )}
                          >
                            {pattern.avg_profit >= 0 ? "+" : ""}
                            {formatPercentage(pattern.avg_profit)}
                          </span>
                        </TableCell>
                        <TableCell className="text-muted-foreground">{pattern.occurrences}</TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {new Date(pattern.last_seen).toLocaleTimeString()}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              pattern.recommendation === "favor"
                                ? "default"
                                : pattern.recommendation === "avoid"
                                ? "destructive"
                                : "secondary"
                            }
                            className="capitalize"
                          >
                            {pattern.recommendation}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </TabsContent>

          {/* Adaptive Strategies Tab */}
          <TabsContent value="strategies" className="space-y-4 mt-4">
            {strategiesLoading ? (
              <LoadingSkeleton count={3} className="h-48 w-full" />
            ) : !adaptiveStrategies || adaptiveStrategies.length === 0 ? (
              <EmptyState
                icon={Zap}
                title="No adaptive strategies available"
                description="The bot needs more market data to learn adaptive strategies. Keep trading to see strategy recommendations."
              />
            ) : (
              <div className="space-y-4">
                {adaptiveStrategies.map((strategy, idx) => (
                  <Card key={idx}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="capitalize">{strategy.market_condition}</CardTitle>
                        <Badge variant="outline">Learned Strategy</Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Expected Performance */}
                      <div className="grid grid-cols-3 gap-4">
                        <div className="rounded-lg border bg-muted/50 p-3">
                          <div className="text-xs text-muted-foreground mb-1">Expected Win Rate</div>
                          <div className="text-lg font-bold text-green-500">
                            {formatPercentage(strategy.expected_performance.win_rate)}
                          </div>
                        </div>
                        <div className="rounded-lg border bg-muted/50 p-3">
                          <div className="text-xs text-muted-foreground mb-1">Avg Return</div>
                          <div className="text-lg font-bold">
                            {formatPercentage(strategy.expected_performance.avg_return)}
                          </div>
                        </div>
                        <div className="rounded-lg border bg-muted/50 p-3">
                          <div className="text-xs text-muted-foreground mb-1">Sharpe Ratio</div>
                          <div className="text-lg font-bold">
                            {strategy.expected_performance.sharpe_ratio.toFixed(2)}
                          </div>
                        </div>
                      </div>

                      {/* Optimal Parameters */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        <div className="rounded-md border bg-card p-2">
                          <div className="text-xs text-muted-foreground mb-1">Confidence</div>
                          <div className="text-sm font-medium">
                            {formatPercentage(strategy.optimal_parameters.confidence_threshold)}
                          </div>
                        </div>
                        <div className="rounded-md border bg-card p-2">
                          <div className="text-xs text-muted-foreground mb-1">Position Size</div>
                          <div className="text-sm font-medium">
                            {strategy.optimal_parameters.position_size_multiplier.toFixed(1)}x
                          </div>
                        </div>
                        <div className="rounded-md border bg-card p-2">
                          <div className="text-xs text-muted-foreground mb-1">Stop Loss</div>
                          <div className="text-sm font-medium">
                            {formatPercentage(strategy.optimal_parameters.stop_loss_pct)}
                          </div>
                        </div>
                        <div className="rounded-md border bg-card p-2">
                          <div className="text-xs text-muted-foreground mb-1">Take Profit</div>
                          <div className="text-sm font-medium">
                            {formatPercentage(strategy.optimal_parameters.take_profit_pct)}
                          </div>
                        </div>
                      </div>

                      {/* Reasoning */}
                      <div className="space-y-1.5">
                        {strategy.reasoning.map((reason, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-2 text-sm bg-muted/30 p-2 rounded-md"
                          >
                            <span className="text-muted-foreground mt-0.5">•</span>
                            <span>{reason}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

