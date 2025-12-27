import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, TrendingUp, TrendingDown, BarChart3, Target, Shield, Zap } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";

interface PairAnalysis {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  currentPrice: number;
  volatility: number;
  volumeScore: number;
  momentumScore: number;
  profitabilityScore: number;
  recommendedRiskPerTrade: number;
  recommendedStopLoss: number;
  recommendedTakeProfit: number;
  confidence: number;
  reasoning: string[];
}

interface TradingRecommendations {
  topPairs: PairAnalysis[];
  optimalRiskSettings: {
    conservative: { riskPerTrade: number; stopLoss: number; takeProfit: number };
    moderate: { riskPerTrade: number; stopLoss: number; takeProfit: number };
    aggressive: { riskPerTrade: number; stopLoss: number; takeProfit: number };
  };
  marketSentiment: 'bullish' | 'bearish' | 'neutral';
  lastUpdated: number;
}

export interface RecommendationConfig {
  tradingPair: string;
  riskPerTrade: number;
  stopLoss: number;
  takeProfit: number;
  maxPositionSize: number;
}

interface TradingRecommendationsProps {
  onApplyRecommendation?: (pair: string, config: RecommendationConfig) => void;
}

export const TradingRecommendations = React.memo(function TradingRecommendations({ onApplyRecommendation }: TradingRecommendationsProps) {
  const { isAuthenticated } = useAuth();

  const { data: recommendations, isLoading, error, refetch, isRefetching } = useQuery<TradingRecommendations>({
    queryKey: ['trading-recommendations'],
    queryFn: async () => {
      return await apiRequest<TradingRecommendations>('/api/recommendations', { method: 'GET' });
    },
    enabled: isAuthenticated,
    refetchInterval: 60000, // Refresh every minute
    retry: 2,
  });

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'bearish': return <TrendingDown className="w-4 h-4 text-red-500" />;
      default: return <BarChart3 className="w-4 h-4 text-gray-500" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return 'bg-green-100 text-green-800';
      case 'bearish': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(2)}%`;
  const formatPrice = (price: number) => `$${price.toFixed(2)}`;

  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Trading Recommendations
          </CardTitle>
          <CardDescription>Please log in to view trading recommendations</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Trading Recommendations
          </CardTitle>
          <CardDescription>Loading market analysis...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <LoadingSkeleton count={3} className="h-4" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
              {[1, 2, 3, 4].map((i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <LoadingSkeleton className="h-6 w-24 mb-2" />
                    <LoadingSkeleton className="h-4 w-32 mb-4" />
                    <LoadingSkeleton count={2} className="h-3" />
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Trading Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorRetry
            title="Failed to load recommendations"
            message={error instanceof Error ? error.message : "Unable to fetch trading recommendations. Please try again."}
            onRetry={() => refetch()}
            error={error as Error}
          />
        </CardContent>
      </Card>
    );
  }

  if (!recommendations || !recommendations.topPairs || recommendations.topPairs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Trading Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Target}
            title="No recommendations available"
            description="Trading recommendations are not available at the moment. Check back later."
          />
        </CardContent>
      </Card>
    );
  }

  if (!recommendations) return null;

  return (
    <Card className="border-card-border shadow-md">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg font-bold">
          <Target className="w-5 h-5 text-primary" />
          Trading Recommendations
        </CardTitle>
        <CardDescription className="text-sm">
          AI-powered analysis of trading pairs and optimal parameters
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="pairs" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="pairs">Top Pairs</TabsTrigger>
            <TabsTrigger value="settings">Risk Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="pairs" className="space-y-4">
            <div className="flex items-center gap-2 mb-4">
              {getSentimentIcon(recommendations.marketSentiment)}
              <Badge className={getSentimentColor(recommendations.marketSentiment)}>
                Market Sentiment: {recommendations.marketSentiment.toUpperCase()}
              </Badge>
              <span className="text-sm text-gray-500">
                Updated {new Date(recommendations.lastUpdated).toLocaleTimeString()}
              </span>
            </div>

            <div className="space-y-3">
              {recommendations?.topPairs && Array.isArray(recommendations.topPairs) ? recommendations.topPairs.map((pair, index) => (
                <Card key={pair.symbol} className="border-l-4 border-l-blue-500">
                  <CardContent className="pt-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-semibold text-lg">
                          #{index + 1} {pair.symbol}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {pair.baseAsset}/{pair.quoteAsset} • {formatPrice(pair.currentPrice)}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Badge className={getConfidenceColor(pair.confidence)}>
                          {formatPercentage(pair.confidence)} Confidence
                        </Badge>
                        <Badge variant="outline">
                          Score: {pair.profitabilityScore.toFixed(1)}
                        </Badge>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                      <div className="text-center">
                        <div className="text-sm text-gray-500">Volatility</div>
                        <div className="font-semibold">{formatPercentage(pair.volatility)}</div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-gray-500">Momentum</div>
                        <div className={`font-semibold ${pair.momentumScore > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {pair.momentumScore > 0 ? '+' : ''}{pair.momentumScore.toFixed(2)}%
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-gray-500">Volume</div>
                        <div className="font-semibold">{pair.volumeScore.toFixed(1)}x</div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-gray-500">Risk/Trade</div>
                        <div className="font-semibold">{pair.recommendedRiskPerTrade}%</div>
                      </div>
                    </div>

                    <div className="flex gap-2 mb-3">
                      <Badge variant="secondary" className="flex items-center gap-1">
                        <Shield className="w-3 h-3" />
                        Stop Loss: {pair.recommendedStopLoss}%
                      </Badge>
                      <Badge variant="secondary" className="flex items-center gap-1">
                        <Target className="w-3 h-3" />
                        Take Profit: {pair.recommendedTakeProfit}%
                      </Badge>
                    </div>

                    <div className="space-y-1 mb-3">
                      {pair.reasoning && Array.isArray(pair.reasoning) ? pair.reasoning.slice(0, 2).map((reason, idx) => (
                        <p key={idx} className="text-sm text-gray-600">• {reason}</p>
                      )) : null}
                    </div>

                    {onApplyRecommendation && (
                      <Button
                        size="sm"
                        onClick={() => onApplyRecommendation(pair.symbol, {
                          tradingPair: pair.symbol,
                          riskPerTrade: pair.recommendedRiskPerTrade,
                          stopLoss: pair.recommendedStopLoss,
                          takeProfit: pair.recommendedTakeProfit,
                          maxPositionSize: Math.min(1000, pair.currentPrice * 10),
                        })}
                        className="w-full"
                      >
                        <Zap className="w-4 h-4 mr-2" />
                        Use These Settings
                      </Button>
                    )}
                  </CardContent>
                </Card>
              )) : (
                <div className="text-center text-muted-foreground py-8">
                  No trading pairs available
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Shield className="w-4 h-4 text-green-500" />
                    Conservative
                  </CardTitle>
                  <CardDescription>Lower risk, steady returns</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Risk per Trade:</span>
                      <span className="font-semibold">{recommendations.optimalRiskSettings.conservative.riskPerTrade}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Stop Loss:</span>
                      <span className="font-semibold">{recommendations.optimalRiskSettings.conservative.stopLoss}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Take Profit:</span>
                      <span className="font-semibold">{recommendations.optimalRiskSettings.conservative.takeProfit}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-blue-500" />
                    Moderate
                  </CardTitle>
                  <CardDescription>Balanced risk-reward</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Risk per Trade:</span>
                      <span className="font-semibold">{recommendations.optimalRiskSettings.moderate.riskPerTrade}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Stop Loss:</span>
                      <span className="font-semibold">{recommendations.optimalRiskSettings.moderate.stopLoss}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Take Profit:</span>
                      <span className="font-semibold">{recommendations.optimalRiskSettings.moderate.takeProfit}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Zap className="w-4 h-4 text-orange-500" />
                    Aggressive
                  </CardTitle>
                  <CardDescription>Higher risk, higher potential returns</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Risk per Trade:</span>
                      <span className="font-semibold">{recommendations.optimalRiskSettings.aggressive.riskPerTrade}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Stop Loss:</span>
                      <span className="font-semibold">{recommendations.optimalRiskSettings.aggressive.stopLoss}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Take Profit:</span>
                      <span className="font-semibold">{recommendations.optimalRiskSettings.aggressive.takeProfit}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
});
