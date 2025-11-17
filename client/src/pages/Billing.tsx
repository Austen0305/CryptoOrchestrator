import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { usePayments } from "@/hooks/usePayments";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Check, X, CreditCard, Calendar, AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useLocation } from "wouter";

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
  
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      setLocation("/login");
      return;
    }
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [plansData, subscriptionData] = await Promise.all([
        getPlans(),
        getSubscription(),
      ]);
      setPlans(plansData || []);
      setSubscription(subscriptionData || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load billing information");
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (plan: string, priceId: string, interval: "monthly" | "yearly") => {
    try {
      setProcessing(`upgrade-${plan}`);
      const session = await createCheckout(priceId, plan);
      if (session?.checkout_url) {
        window.location.href = session.checkout_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create checkout session");
    } finally {
      setProcessing(null);
    }
  };

  const handleManage = async () => {
    try {
      setProcessing("manage");
      const session = await createPortal();
      if (session?.portal_url) {
        window.location.href = session.portal_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open customer portal");
    } finally {
      setProcessing(null);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel your subscription? It will remain active until the end of the current billing period.")) {
      return;
    }
    try {
      setProcessing("cancel");
      await cancelSubscription(false);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to cancel subscription");
    } finally {
      setProcessing(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const currentPlan = subscription ? plans.find((p) => p.plan === subscription.plan) : null;
  const isActive = subscription?.status === "active" || subscription?.status === "trialing";

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Billing & Subscription</h1>
          <p className="text-muted-foreground mt-2">
            Manage your subscription and billing information
          </p>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

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
                    ) : plan.price_monthly === 0 ? (
                      <Button
                        onClick={() => handleUpgrade(plan.plan, "", "monthly")}
                        disabled={!plan.stripe_price_id_monthly || processing !== null}
                        className="w-full"
                        variant="outline"
                      >
                        Free Forever
                      </Button>
                    ) : (
                      <div className="w-full space-y-2">
                        {plan.stripe_price_id_monthly && (
                          <Button
                            onClick={() =>
                              handleUpgrade(
                                plan.plan,
                                plan.stripe_price_id_monthly!,
                                "monthly"
                              )
                            }
                            disabled={processing !== null}
                            className="w-full"
                          >
                            {processing === `upgrade-${plan.plan}` ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Processing...
                              </>
                            ) : (
                              "Upgrade"
                            )}
                          </Button>
                        )}
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

