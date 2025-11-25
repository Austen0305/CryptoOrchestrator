/**
 * Pricing Plans Component - Display subscription plans
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { usePricing, PricingInfo } from "@/hooks/usePayments";
import { Loader2, Check, Zap } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useState } from "react";
import { toast } from "@/hooks/use-toast";

export function PricingPlans() {
  const { data: pricing, isLoading } = usePricing();
  const { isAuthenticated } = useAuth();
  const [selectedTier, setSelectedTier] = useState<string | null>(null);

  const handleSubscribe = (tier: string) => {
    if (!isAuthenticated) {
      toast({
        title: "Login Required",
        description: "Please log in to subscribe",
        variant: "destructive",
      });
      return;
    }

    setSelectedTier(tier);
    // In production, redirect to Stripe checkout or open payment modal
    toast({
      title: "Subscription",
      description: `Redirecting to checkout for ${tier} plan...`,
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  const tiers = ['free', 'basic', 'pro', 'enterprise'];
  const tierColors = {
    free: "border-gray-300",
    basic: "border-blue-300",
    pro: "border-purple-300 border-2",
    enterprise: "border-gold-300 border-2"
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold">Choose Your Plan</h2>
        <p className="text-muted-foreground mt-2">
          Select the perfect plan for your trading needs
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {tiers.map((tier) => {
          const plan = pricing?.pricing[tier];
          if (!plan) return null;

          const isPopular = tier === 'pro';
          const isEnterprise = tier === 'enterprise';

          return (
            <Card
              key={tier}
              className={`relative ${tierColors[tier]} ${isPopular ? 'shadow-lg' : ''}`}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-purple-500">
                    <Zap className="h-3 w-3 mr-1" />
                    Most Popular
                  </Badge>
                </div>
              )}

              <CardHeader>
                <CardTitle className="capitalize text-xl">{tier}</CardTitle>
                <div className="mt-2">
                  <span className="text-3xl font-bold">{plan.amount_display}</span>
                  {plan.amount > 0 && (
                    <span className="text-muted-foreground">/{plan.interval}</span>
                  )}
                </div>
                <CardDescription className="mt-2">
                  {plan.amount === 0 ? "Perfect for getting started" : "Full access to all features"}
                </CardDescription>
              </CardHeader>

              <CardContent>
                <div className="space-y-4">
                  <ul className="space-y-2">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Button
                    className={`w-full ${isPopular ? 'bg-purple-500 hover:bg-purple-600' : ''}`}
                    variant={isPopular ? 'default' : 'outline'}
                    onClick={() => handleSubscribe(tier)}
                    disabled={selectedTier === tier}
                  >
                    {plan.amount === 0 ? "Get Started" : isEnterprise ? "Contact Sales" : "Subscribe"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
