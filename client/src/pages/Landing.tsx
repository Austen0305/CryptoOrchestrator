/**
 * Landing Page - Marketing site with pricing and signup
 */
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, Zap, TrendingUp, Shield, Code, Brain, ArrowRight } from "lucide-react";
import { Link } from "wouter";
import { PricingPlans } from "@/components/PricingPlans";

export default function Landing() {
  const features = [
    {
      icon: Brain,
      title: "AI-Powered Trading",
      description: "Advanced machine learning models for market prediction"
    },
    {
      icon: TrendingUp,
      title: "Multi-Exchange Support",
      description: "Trade on Binance, Coinbase, Kraken, and more"
    },
    {
      icon: Shield,
      title: "Risk Management",
      description: "Comprehensive risk analysis and portfolio protection"
    },
    {
      icon: Code,
      title: "Strategy Builder",
      description: "Create custom trading strategies with visual editor"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-3xl mx-auto space-y-6">
          <Badge variant="outline" className="mb-4">
            <Zap className="h-3 w-3 mr-1" />
            Now Available
          </Badge>
          <h1 className="text-5xl font-bold tracking-tight">
            Professional Crypto Trading Platform
          </h1>
          <p className="text-xl text-muted-foreground">
            AI-powered trading bots, advanced strategies, and comprehensive risk management.
            Trade smarter, not harder.
          </p>
          <div className="flex items-center justify-center gap-4 pt-4">
            <Link href="/licensing">
              <Button size="lg" className="gap-2">
                Get Started
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/strategies">
              <Button size="lg" variant="outline">
                View Features
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-2">Powerful Features</h2>
          <p className="text-muted-foreground">
            Everything you need for professional crypto trading
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <Card key={idx}>
                <CardHeader>
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{feature.description}</CardDescription>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Pricing Section */}
      <section className="container mx-auto px-4 py-20">
        <PricingPlans />
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="text-3xl">Ready to Start Trading?</CardTitle>
            <CardDescription className="text-lg">
              Join thousands of traders using CryptoOrchestrator
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Link href="/licensing">
              <Button size="lg" className="w-full md:w-auto gap-2">
                Start Free Trial
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <p className="text-sm text-muted-foreground">
              14-day free trial • No credit card required
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
