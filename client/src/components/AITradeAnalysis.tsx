import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertCircle, 
  CheckCircle, 
  Target,
  Shield,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '@/lib/queryClient';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { ErrorRetry } from '@/components/ErrorRetry';

interface TradeInsight {
  type: 'strength' | 'weakness' | 'opportunity' | 'threat';
  title: string;
  description: string;
  confidence: number;
  actionable: boolean;
  suggestion?: string;
  priority: number;
  impact_score: number;
}

interface AIAnalysisData {
  bot_id: string;
  symbol: string;
  timestamp: string;
  overall_score: number;
  insights: TradeInsight[];
  market_sentiment: {
    sentiment: string;
    confidence: number;
    indicators: Record<string, number>;
  };
  risk_assessment: {
    overall_risk: string;
    risk_score: number;
    factors: Record<string, number>;
  };
  recommendations: string[];
}

interface AITradeAnalysisProps {
  botId: string;
}

export function AITradeAnalysis({ botId }: AITradeAnalysisProps) {
  const { data: analysis, isLoading, error, refetch, isRefetching } = useQuery<AIAnalysisData>({
    queryKey: ['ai-analysis', botId],
    queryFn: async () => {
      return await apiRequest(`/api/ai-analysis/bot/${botId}`, { method: 'GET' });
    },
    enabled: !!botId,
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    retry: 2,
  });

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'strength':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'weakness':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'opportunity':
        return <TrendingUp className="h-5 w-5 text-blue-500" />;
      case 'threat':
        return <TrendingDown className="h-5 w-5 text-red-500" />;
      default:
        return <Target className="h-5 w-5 text-gray-500" />;
    }
  };

  const getInsightBorderColor = (type: string) => {
    switch (type) {
      case 'strength':
        return 'border-l-green-500';
      case 'weakness':
        return 'border-l-yellow-500';
      case 'opportunity':
        return 'border-l-blue-500';
      case 'threat':
        return 'border-l-red-500';
      default:
        return 'border-l-gray-500';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish':
        return 'text-green-500 bg-green-50 dark:bg-green-950';
      case 'bearish':
        return 'text-red-500 bg-red-50 dark:bg-red-950';
      default:
        return 'text-gray-500 bg-gray-50 dark:bg-gray-950';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'text-green-500 bg-green-50 dark:bg-green-950';
      case 'medium':
        return 'text-yellow-500 bg-yellow-50 dark:bg-yellow-950';
      case 'high':
        return 'text-red-500 bg-red-50 dark:bg-red-950';
      default:
        return 'text-gray-500 bg-gray-50 dark:bg-gray-950';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-6 w-6" />
            AI Trade Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <LoadingSkeleton count={3} className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error || !analysis) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-6 w-6" />
            AI Trade Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorRetry
            title="Failed to load AI analysis"
            message={error instanceof Error ? error.message : 'No data available'}
            onRetry={() => refetch()}
            error={error as Error}
          />
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
              <Sparkles className="h-6 w-6 text-purple-500" />
              AI Trade Analysis
            </CardTitle>
            <CardDescription>
              {analysis.symbol} • Overall Score: {analysis.overall_score.toFixed(1)}/100
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall Score */}
        <div className="p-4 border rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold">Performance Score</span>
            <span className="text-2xl font-bold text-primary">
              {analysis.overall_score.toFixed(0)}/100
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
            <div
              className="bg-primary h-2 rounded-full transition-all"
              style={{ width: `${analysis.overall_score}%` }}
            />
          </div>
        </div>

        {/* Market Sentiment */}
        <div className="p-4 border rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold flex items-center gap-2">
              <Target className="h-5 w-5" />
              Market Sentiment
            </h3>
            <Badge className={getSentimentColor(analysis.market_sentiment.sentiment)}>
              {analysis.market_sentiment.sentiment.toUpperCase()}
            </Badge>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-muted-foreground">Confidence:</span>{' '}
              <span className="font-medium">
                {(analysis.market_sentiment.confidence * 100).toFixed(0)}%
              </span>
            </div>
            {Object.entries(analysis.market_sentiment.indicators).map(([key, value]) => (
              <div key={key}>
                <span className="text-muted-foreground capitalize">{key.replace('_', ' ')}:</span>{' '}
                <span className="font-medium">{value.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Assessment */}
        <div className="p-4 border rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Risk Assessment
            </h3>
            <Badge className={getRiskColor(analysis.risk_assessment.overall_risk)}>
              {analysis.risk_assessment.overall_risk.toUpperCase()} RISK
            </Badge>
          </div>
          <div className="space-y-2">
            {Object.entries(analysis.risk_assessment.factors).map(([factor, score]) => (
              <div key={factor} className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground capitalize flex-1">
                  {factor.replace('_', ' ')}
                </span>
                <div className="w-32 bg-gray-200 rounded-full h-1.5 dark:bg-gray-700">
                  <div
                    className="bg-yellow-500 h-1.5 rounded-full"
                    style={{ width: `${score}%` }}
                  />
                </div>
                <span className="text-sm font-medium w-10 text-right">{score}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Insights */}
        <div className="space-y-3">
          <h3 className="font-semibold">Key Insights</h3>
          {analysis.insights
            .sort((a, b) => b.priority - a.priority)
            .map((insight, idx) => (
              <div
                key={idx}
                className={`border-l-4 ${getInsightBorderColor(insight.type)} pl-4 py-3 bg-muted/30 rounded-r`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    {getInsightIcon(insight.type)}
                    <h4 className="font-semibold">{insight.title}</h4>
                  </div>
                  <div className="flex items-center gap-2">
                    {insight.actionable && (
                      <Badge variant="outline" className="text-xs">
                        Actionable
                      </Badge>
                    )}
                    <Badge variant="secondary" className="text-xs">
                      {Math.round(insight.confidence * 100)}% confident
                    </Badge>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  {insight.description}
                </p>
                {insight.suggestion && (
                  <div className="mt-2 p-2 bg-primary/10 rounded text-sm flex items-start gap-2">
                    <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0 text-primary" />
                    <div>
                      <strong>Suggestion:</strong> {insight.suggestion}
                    </div>
                  </div>
                )}
              </div>
            ))}
        </div>

        {/* Recommendations */}
        {analysis.recommendations.length > 0 && (
          <div className="p-4 border rounded-lg bg-blue-50/50 dark:bg-blue-950/20">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Target className="h-5 w-5 text-blue-500" />
              Recommendations
            </h3>
            <ul className="space-y-2">
              {analysis.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm flex items-start gap-2">
                  <span className="text-blue-500 font-bold">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
