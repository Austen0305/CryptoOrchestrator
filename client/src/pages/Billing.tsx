import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { usePayments } from "@/hooks/usePayments";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Check, X, CreditCard, Calendar, AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useLocation } from "wouter";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import logger from "@/lib/logger";

interface Plan {
  plan: string;
  name: string;
  price_monthly: number;
  price_yearly: number;
  stripe_price_id_monthly?: string;
  stripe_price_id_yearly?: string;
  features: string[];
  limits: {
    max_bots: number;
    max_strategies: number;
    max_backtests_per_month: number;
  };
}

interface Subscription {
  plan: string;
  status: string;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
  limits: Record<string, number>;
}

export default function Billing() {
  const { user } = useAuth();
  const [, setLocation] = useLocation();
  const { getPlans, getSubscription, createCheckout, createPortal, cancelSubscription } = usePayments();
  const queryClient = useQueryClient();
  const [processing, setProcessing] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      setLocation("/login");
      return;
    }
  }, [user, setLocation]);

  const { data: plansData, isLoading: plansLoading, error: plansError, refetch: refetchPlans } = useQuery<Plan[]>({
    queryKey: ['billing-plans'],
    queryFn: async () => {
      return await getPlans() || [];
    },
    enabled: !!user,
    retry: 2,
  });

  const { data: subscription, isLoading: subscriptionLoading, error: subscriptionError, refetch: refetchSubscription } = useQuery<Subscription | null>({
    queryKey: ['billing-subscription'],
    queryFn: async () => {
      return await getSubscription() || null;
    },
    enabled: !!user,
    retry: 2,
  });

  const plans = plansData || [];
  const isLoading = plansLoading || subscriptionLoading;
  const error = plansError || subscriptionError;

  const upgradeMutation = useMutation({
    mutationFn: async ({ plan, priceId }: { plan: string; priceId: string }) => {
      return await createCheckout(priceId, plan);
    },
    onSuccess: (session) => {
      // Free subscriptions activate immediately - no redirect needed
      if (session?.checkout_url) {
        // If it's a relative URL, just refresh the subscription data
        if (session.checkout_url.startsWith('/')) {
          queryClient.invalidateQueries({ queryKey: ['billing-subscription'] });
          queryClient.invalidateQueries({ queryKey: ['billing-plans'] });
        } else {
          window.location.href = session.checkout_url;
        }
      }
    },
    onError: (error: Error) => {
      // Error will be shown via toast if usePayments hook handles it
      logger.error('Failed to create subscription', { error });
    },
  });

  const manageMutation = useMutation({
    mutationFn: async () => {
      return await createPortal();
    },
    onSuccess: (session) => {
      if (session?.portal_url) {
        window.location.href = session.portal_url;
      }
    },
    onError: (error: Error) => {
      logger.error('Failed to open customer portal', { error });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: async () => {
      return await cancelSubscription(false);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billing-subscription'] });
    },
    onError: (error: Error) => {
      logger.error('Failed to cancel subscription', { error });
    },
  });

  const handleUpgrade = async (plan: string, priceId: string, interval: "monthly" | "yearly") => {
    setProcessing(`upgrade-${plan}`);
    try {
      await upgradeMutation.mutateAsync({ plan, priceId });
    } finally {
      setProcessing(null);
    }
  };

  const handleManage = async () => {
    setProcessing("manage");
    try {
      await manageMutation.mutateAsync();
    } finally {
      setProcessing(null);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel your subscription? It will remain active until the end of the current billing period.")) {
      return;
    }
    setProcessing("cancel");
    try {
      await cancelMutation.mutateAsync();
    } finally {
      setProcessing(null);
    }
  };

  if (isLoading) {
    return (
      <div className="w-full max-w-6xl mx-auto space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">Billing & Subscription</h1>
          <p className="text-muted-foreground mt-1">Loading billing information...</p>
        </div>
        <LoadingSkeleton count={5} className="h-48 w-full mb-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full max-w-6xl mx-auto space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">Billing & Subscription</h1>
          <p className="text-muted-foreground mt-1">Manage your subscription and billing information</p>
        </div>
        <ErrorRetry
          title="Failed to load billing information"
          message={error instanceof Error ? error.message : "An unexpected error occurred."}
          onRetry={() => { refetchPlans(); refetchSubscription(); }}
          error={error as Error}
        />
      </div>
    );
  }

  const currentPlan = subscription ? plans.find((p) => p.plan === subscription.plan) : null;
  const isActive = subscription?.status === "active" || subscription?.status === "trialing";

  return (
    <div className="w-full max-w-6xl mx-auto">
      <div className="space-y-6 w-full animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">Billing & Subscription</h1>
          <p className="text-muted-foreground mt-1">
            Manage your subscription and billing information
          </p>
        </div>


        {/* Current Subscription */}
        {subscription && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Current Plan</CardTitle>
                  <CardDescription>
                    {currentPlan?.name || subscription.plan}
                  </CardDescription>
                </div>
                <Badge variant={isActive ? "default" : "secondary"}>
                  {subscription.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {subscription.current_period_end && (
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="h-4 w-4" />
                  <span>
                    {subscription.cancel_at_period_end
                      ? `Cancels on ${new Date(subscription.current_period_end).toLocaleDateString()}`
                      : `Renews on ${new Date(subscription.current_period_end).toLocaleDateString()}`}
                  </span>
                </div>
              )}
              {subscription.limits && (
                <div className="space-y-2">
                  <h4 className="font-medium text-sm">Plan Limits:</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>
                      Max Bots: {subscription.limits.max_bots === -1 ? "Unlimited" : subscription.limits.max_bots}
                    </li>
                    <li>
                      Max Strategies: {subscription.limits.max_strategies === -1 ? "Unlimited" : subscription.limits.max_strategies}
                    </li>
                    <li>
                      Max Backtests/Month: {subscription.limits.max_backtests_per_month === -1 ? "Unlimited" : subscription.limits.max_backtests_per_month}
                    </li>
                  </ul>
                </div>
              )}
            </CardContent>
            <CardFooter className="flex gap-2">
              <Button
                onClick={handleManage}
                disabled={processing === "manage"}
                variant="outline"
              >
                {processing === "manage" ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Opening...
                  </>
                ) : (
                  <>
                    <CreditCard className="mr-2 h-4 w-4" />
                    Manage Subscription
                  </>
                )}
              </Button>
              {isActive && !subscription.cancel_at_period_end && (
                <Button
                  onClick={handleCancel}
                  disabled={processing === "cancel"}
                  variant="destructive"
                >
                  {processing === "cancel" ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Cancelling...
                    </>
                  ) : (
                    "Cancel Subscription"
                  )}
                </Button>
              )}
            </CardFooter>
          </Card>
        )}

        {/* Available Plans */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Available Plans</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {plans.map((plan) => {
              const isCurrentPlan = subscription?.plan === plan.plan;
              const isHigherPlan =
                plan.plan === "enterprise" ||
                (plan.plan === "pro" && subscription?.plan !== "pro" && subscription?.plan !== "enterprise") ||
                (plan.plan === "basic" && subscription?.plan === "free");

              return (
                <Card
                  key={plan.plan}
                  className={isCurrentPlan ? "border-primary" : ""}
                >
                  <CardHeader>
                    <CardTitle>{plan.name}</CardTitle>
                    <div className="mt-2">
                      <span className="text-3xl font-bold">
                        ${plan.price_monthly}
                      </span>
                      <span className="text-muted-foreground">/month</span>
                    </div>
                    {plan.price_yearly > 0 && (
                      <p className="text-sm text-muted-foreground mt-1">
                        ${plan.price_yearly}/year (save{" "}
                        {Math.round(
                          ((plan.price_monthly * 12 - plan.price_yearly) /
                            (plan.price_monthly * 12)) *
                            100
                        )}
                        %)
                      </p>
                    )}
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {plan.features.map((feature, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <Check className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                  <CardFooter>
                    {isCurrentPlan ? (
                      <Button disabled className="w-full" variant="outline">
                        Current Plan
                      </Button>
                    ) : (
                      <div className="w-full space-y-2">
                        <Button
                          onClick={() =>
                            handleUpgrade(
                              plan.plan,
                              "free", // All plans are free now
                              "monthly"
                            )
                          }
                          disabled={processing !== null}
                          className="w-full"
                        >
                          {processing === `upgrade-${plan.plan}` ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Activating...
                            </>
                          ) : (
                            (plan as any).is_free || plan.amount === 0 ? "Activate Free Plan" : "Upgrade"
                          )}
                        </Button>
                      </div>
                    )}
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

