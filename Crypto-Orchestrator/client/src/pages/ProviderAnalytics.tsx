import React from "react";
import { ProviderAnalyticsDashboard } from "@/components/ProviderAnalyticsDashboard";
import { EnhancedErrorBoundary } from "@/components/EnhancedErrorBoundary";
import { useAuth } from "@/hooks/useAuth";
import { useLocation, useRoute } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import logger from "@/lib/logger";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";

function ProviderAnalyticsContent() {
  const [, params] = useRoute("/provider-analytics/:providerId?");
  const providerId = params?.providerId ? parseInt(params.providerId, 10) : null;

  // Get current user's provider ID if not specified
  const { user } = useAuth();
  const { data: userProvider, isLoading: providerLoading } = useQuery({
    queryKey: ["user", "signal-provider"],
    queryFn: async () => {
      if (!user?.id) return null;
      try {
        const response = await apiRequest("/api/marketplace/apply", { method: "GET" });
        return response;
      } catch {
        return null;
      }
    },
    enabled: !providerId && !!user?.id,
  });

  const finalProviderId = providerId || (userProvider && typeof userProvider === 'object' && userProvider !== null && 'id' in userProvider ? (userProvider as { id: number }).id : undefined);

  if (providerLoading) {
    return <LoadingSkeleton variant="dashboard" className="h-[600px]" />;
  }

  if (!finalProviderId) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-500" />
            No Provider Found
          </CardTitle>
          <CardDescription>
            You need to apply as a signal provider first to view analytics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <button
            onClick={() => window.location.href = "/marketplace"}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Go to Marketplace
          </button>
        </CardContent>
      </Card>
    );
  }

  return <ProviderAnalyticsDashboard providerId={finalProviderId} />;
}

export default function ProviderAnalytics() {
  const { isAuthenticated } = useAuth();
  const [, setLocation] = useLocation();

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
              Authentication Required
            </CardTitle>
            <CardDescription>Please log in to access provider analytics</CardDescription>
          </CardHeader>
          <CardContent>
            <button
              onClick={() => setLocation("/login")}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Go to Login
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <EnhancedErrorBoundary
      onError={(error, errorInfo) => {
        logger.error("Provider Analytics page error", { error, errorInfo });
      }}
    >
      <div className="container mx-auto p-6">
        <ProviderAnalyticsContent />
      </div>
    </EnhancedErrorBoundary>
  );
}
