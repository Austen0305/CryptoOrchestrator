import React from "react";
import { MarketplaceAnalyticsDashboard } from "@/components/MarketplaceAnalyticsDashboard";
import { EnhancedErrorBoundary } from "@/components/EnhancedErrorBoundary";
import { useAuth } from "@/hooks/useAuth";
import { useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, AlertCircle } from "lucide-react";
import logger from "@/lib/logger";

export default function AdminAnalytics() {
  const { user, isAuthenticated } = useAuth();
  const [, setLocation] = useLocation();

  // Redirect if not admin
  React.useEffect(() => {
    if (isAuthenticated && user?.role !== "admin") {
      logger.warn("Non-admin user attempted to access admin analytics");
      setLocation("/dashboard");
    }
  }, [isAuthenticated, user?.role, setLocation]);

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
              Authentication Required
            </CardTitle>
            <CardDescription>Please log in to access admin analytics</CardDescription>
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

  if (user?.role !== "admin") {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-red-500" />
              Access Denied
            </CardTitle>
            <CardDescription>You do not have permission to access this page</CardDescription>
          </CardHeader>
          <CardContent>
            <button
              onClick={() => setLocation("/dashboard")}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Go to Dashboard
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <EnhancedErrorBoundary
      onError={(error, errorInfo) => {
        logger.error("Admin Analytics page error", { error, errorInfo });
      }}
    >
      <div className="container mx-auto p-6">
        <MarketplaceAnalyticsDashboard />
      </div>
    </EnhancedErrorBoundary>
  );
}
