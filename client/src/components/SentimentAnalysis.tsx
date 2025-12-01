import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, TrendingDown, MessageSquare, Twitter, RefreshCw, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";

interface SentimentData {
  overall: number; // -100 to 100
  twitter: number;
  reddit: number;
  news: number;
  fearGreedIndex: number; // 0 to 100
  confidence: number;
  timestamp: Date;
}

interface SentimentAnalysisProps {
  symbol?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const SentimentAnalysis = React.memo(function SentimentAnalysis({ 
  symbol = "BTC", 
  autoRefresh = true,
  refreshInterval = 60000 // 1 minute
}: SentimentAnalysisProps) {
  const { data: sentiment, isLoading, error, refetch, isRefetching } = useQuery<SentimentData>({
    queryKey: ['sentiment-analysis', symbol],
    queryFn: async () => {
      const data = await apiRequest<SentimentData>(`/api/sentiment/${symbol}`, { method: 'GET' });
      // Ensure timestamp is a Date object
      return {
        ...data,
        timestamp: new Date(data.timestamp),
      };
    },
    enabled: !!symbol,
    refetchInterval: autoRefresh ? refreshInterval : false,
    retry: 2,
  });

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Sentiment Analysis
          </CardTitle>
          <CardDescription>Loading sentiment data...</CardDescription>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton count={5} className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Sentiment Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorRetry
            title="Failed to load sentiment analysis"
            message={error instanceof Error ? error.message : "Unable to fetch sentiment data. Please try again."}
            onRetry={() => refetch()}
            error={error as Error}
          />
        </CardContent>
      </Card>
    );
  }

  if (!sentiment) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Sentiment Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={MessageSquare}
            title="No sentiment data available"
            description={`Sentiment analysis for ${symbol} is not available at the moment.`}
          />
        </CardContent>
      </Card>
    );
  }

  const getSentimentLabel = (value: number): { label: string; color: string } => {
    if (value >= 70) return { label: "Very Bullish", color: "text-green-500" };
    if (value >= 40) return { label: "Bullish", color: "text-green-400" };
    if (value >= -40) return { label: "Neutral", color: "text-yellow-500" };
    if (value >= -70) return { label: "Bearish", color: "text-red-400" };
    return { label: "Very Bearish", color: "text-red-500" };
  };

  const getFearGreedLabel = (value: number): { label: string; color: string } => {
    if (value >= 75) return { label: "Extreme Greed", color: "text-red-500" };
    if (value >= 55) return { label: "Greed", color: "text-green-500" };
    if (value >= 45) return { label: "Neutral", color: "text-yellow-500" };
    if (value >= 25) return { label: "Fear", color: "text-orange-500" };
    return { label: "Extreme Fear", color: "text-red-500" };
  };

  const sentimentLabel = sentiment ? getSentimentLabel(sentiment.overall) : null;
  const fearGreedLabel = sentiment ? getFearGreedLabel(sentiment.fearGreedIndex) : null;

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Sentiment Analysis
            </CardTitle>
            <CardDescription>
              Real-time market sentiment for {symbol}
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={cn("h-4 w-4 mr-2", isRefetching && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {sentiment && (
          <>
            {/* Overall Sentiment */}
            <div className="text-center space-y-2">
              <div className="text-4xl font-bold">
                <span className={sentimentLabel?.color}>
                  {sentiment.overall > 0 ? "+" : ""}{sentiment.overall}
                </span>
              </div>
              <div className="flex items-center justify-center gap-2">
                {sentiment.overall >= 0 ? (
                  <TrendingUp className="h-5 w-5 text-green-500" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-red-500" />
                )}
                <span className={cn("font-semibold", sentimentLabel?.color)}>
                  {sentimentLabel?.label}
                </span>
              </div>
              <Progress 
                value={Math.abs(sentiment.overall)} 
                className="h-2 w-full max-w-md mx-auto"
              />
              <div className="text-sm text-muted-foreground">
                Confidence: {sentiment.confidence}%
              </div>
            </div>

            {/* Fear & Greed Index */}
            <div className="rounded-lg border bg-muted/50 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium">Fear & Greed Index</div>
                <Badge variant={sentiment.fearGreedIndex >= 55 ? "default" : "secondary"}>
                  {sentiment.fearGreedIndex}/100
                </Badge>
              </div>
              <Progress value={sentiment.fearGreedIndex} className="h-2 mb-2" />
              <div className={cn("text-sm font-medium", fearGreedLabel?.color)}>
                {fearGreedLabel?.label}
              </div>
            </div>

            {/* Sources Breakdown */}
            <Tabs defaultValue="all" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="all">All</TabsTrigger>
                <TabsTrigger value="twitter">
                  <Twitter className="h-4 w-4 mr-1" />
                  Twitter
                </TabsTrigger>
                <TabsTrigger value="reddit">Reddit</TabsTrigger>
                <TabsTrigger value="news">News</TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="space-y-3 mt-4">
                <SentimentSourceItem
                  label="Twitter"
                  value={sentiment.twitter}
                  icon={<Twitter className="h-4 w-4" />}
                />
                <SentimentSourceItem
                  label="Reddit"
                  value={sentiment.reddit}
                  icon={<MessageSquare className="h-4 w-4" />}
                />
                <SentimentSourceItem
                  label="News"
                  value={sentiment.news}
                  icon={<AlertCircle className="h-4 w-4" />}
                />
              </TabsContent>

              <TabsContent value="twitter" className="mt-4">
                <SentimentSourceDetail
                  source="Twitter"
                  value={sentiment.twitter}
                  description="Sentiment from Twitter/X posts and tweets"
                />
              </TabsContent>

              <TabsContent value="reddit" className="mt-4">
                <SentimentSourceDetail
                  source="Reddit"
                  value={sentiment.reddit}
                  description="Sentiment from Reddit posts and comments"
                />
              </TabsContent>

              <TabsContent value="news" className="mt-4">
                <SentimentSourceDetail
                  source="News"
                  value={sentiment.news}
                  description="Sentiment from news articles and headlines"
                />
              </TabsContent>
            </Tabs>

            {/* Last Updated */}
            <div className="text-xs text-muted-foreground text-center">
              Last updated: {sentiment.timestamp.toLocaleTimeString()}
              {autoRefresh && <span className="ml-2">• Auto-refreshing every {refreshInterval / 1000}s</span>}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
});

function SentimentSourceItem({ 
  label, 
  value, 
  icon 
}: { 
  label: string; 
  value: number; 
  icon: React.ReactNode 
}) {
  const sentimentLabel = getSentimentLabel(value);
  
  return (
    <div className="flex items-center justify-between p-3 rounded-md border">
      <div className="flex items-center gap-2">
        {icon}
        <span className="font-medium">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={cn("font-bold", sentimentLabel.color)}>
          {value > 0 ? "+" : ""}{value}
        </span>
        <Badge variant="outline" className={sentimentLabel.color}>
          {sentimentLabel.label}
        </Badge>
      </div>
    </div>
  );
}

function SentimentSourceDetail({
  source,
  value,
  description
}: {
  source: string;
  value: number;
  description: string;
}) {
  const sentimentLabel = getSentimentLabel(value);
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{source} Sentiment</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center space-y-4">
          <div className="text-3xl font-bold">
            <span className={sentimentLabel.color}>
              {value > 0 ? "+" : ""}{value}
            </span>
          </div>
          <Progress value={Math.abs(value)} className="h-3" />
          <Badge variant="outline" className={sentimentLabel.color}>
            {sentimentLabel.label}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

function getSentimentLabel(value: number): { label: string; color: string } {
  if (value >= 70) return { label: "Very Bullish", color: "text-green-500" };
  if (value >= 40) return { label: "Bullish", color: "text-green-400" };
  if (value >= -40) return { label: "Neutral", color: "text-yellow-500" };
  if (value >= -70) return { label: "Bearish", color: "text-red-400" };
  return { label: "Very Bearish", color: "text-red-500" };
}

