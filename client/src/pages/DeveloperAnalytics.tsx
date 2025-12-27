import React from "react";
import { DeveloperAnalyticsDashboard } from "@/components/DeveloperAnalyticsDashboard";
import { EnhancedErrorBoundary } from "@/components/EnhancedErrorBoundary";
import { useAuth } from "@/hooks/useAuth";
import { useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import logger from "@/lib/logger";

export default function DeveloperAnalytics() {
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
            <CardDescription>Please log in to access developer analytics</CardDescription>
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
        logger.error("Developer Analytics page error", { error, errorInfo });
      }}
    >
      <div className="container mx-auto p-6">
        <DeveloperAnalyticsDashboard />
      </div>
    </EnhancedErrorBoundary>
  );
}
