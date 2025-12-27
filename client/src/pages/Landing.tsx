/**
 * Landing Page - Enhanced marketing site with pricing, visuals, and comprehensive information
 */
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { 
  Check, Zap, TrendingUp, Shield, Code, Brain, ArrowRight, Download, Play, Star, Users, 
  BarChart3, Copy, Trophy, Bell, Lock, DollarSign, Activity, Globe, Sparkles, 
  Award, Clock, Target, LineChart, PieChart, Wallet, CreditCard, MessageSquare,
  ChevronRight, CheckCircle2, ArrowDown, Rocket, Infinity, Crown, UserPlus
} from "lucide-react";
import { Link, useLocation } from "wouter";
import { PricingPlans } from "@/components/PricingPlans";
import { useAuth } from "@/hooks/useAuth";

export default function Landing() {
  const { isAuthenticated } = useAuth();
  const [, setLocation] = useLocation();
  const [showInstallDialog, setShowInstallDialog] = useState(false);
  const [installStep, setInstallStep] = useState(1);
  const [expandedFeature, setExpandedFeature] = useState<number | null>(null);

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      setLocation("/dashboard");
    }
  }, [isAuthenticated, setLocation]);

  if (isAuthenticated) {
    return null;
  }
  
  const features = [
    {
      icon: Brain,
      title: "AI-Powered Trading",
      description: "9+ machine learning models analyzing market patterns 24/7",
      highlight: "9+ ML Models",
      color: "text-purple-500",
      details: [
        "Neural network models for price prediction",
        "Sentiment analysis from news and social media",
        "Pattern recognition across multiple timeframes",
        "Automated strategy optimization",
        "Real-time market regime detection",
        "Ensemble predictions for higher accuracy"
      ]
    },
    {
      icon: TrendingUp,
      title: "Blockchain-Only Trading",
      description: "Trade directly on DEX aggregators - no centralized exchanges needed",
      highlight: "DEX Only",
      color: "text-green-500",
      details: [
        "Trade on 500+ DEXs via aggregators (0x, OKX, Rubic)",
        "Multi-chain support (Ethereum, Base, Arbitrum, Polygon, etc.)",
        "Best price routing across all DEXs",
        "No exchange API keys required",
        "Lower fees - only blockchain gas + DEX fees",
        "Custodial or non-custodial wallet options"
      ]
    },
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "2FA, KYC, encrypted API keys, and bank-level security",
      highlight: "Bank-Level",
      color: "text-blue-500",
      details: [
        "Two-factor authentication (2FA/TOTP)",
        "End-to-end encryption for API keys",
        "KYC/AML compliance tools",
        "IP whitelisting and geofencing",
        "Withdrawal address whitelisting",
        "Audit logs for all transactions",
        "Cold storage integration"
      ]
    },
    {
      icon: Code,
      title: "Strategy Builder",
      description: "Visual editor to create and backtest custom strategies",
      highlight: "Visual Editor",
      color: "text-orange-500",
      details: [
        "Drag-and-drop strategy builder",
        "Historical backtesting engine",
        "Paper trading mode for testing",
        "Custom indicator support",
        "Multi-timeframe analysis",
        "Strategy performance analytics",
        "Export/import strategies"
      ]
    },
    {
      icon: Copy,
      title: "Copy Trading",
      description: "Automatically copy trades from top-performing traders",
      highlight: "Auto-Execute",
      color: "text-pink-500",
      details: [
        "Follow top traders automatically",
        "Customizable copy ratios",
        "Risk management filters",
        "Real-time trade mirroring",
        "Performance tracking and analytics",
        "Leaderboard rankings",
        "Social trading features"
      ]
    },
    {
      icon: Trophy,
      title: "Leaderboards",
      description: "Compete globally and track your performance rankings",
      highlight: "Real-Time",
      color: "text-yellow-500",
      details: [
        "Global and regional rankings",
        "Multiple leaderboard categories",
        "Real-time position updates",
        "Historical performance tracking",
        "Achievement badges and rewards",
        "Public profile showcase",
        "Monthly and yearly competitions"
      ]
    },
    {
      icon: Bell,
      title: "Real-Time Alerts",
      description: "Instant WebSocket notifications for all trading events",
      highlight: "Instant",
      color: "text-red-500",
      details: [
        "WebSocket-based real-time updates",
        "Email and SMS notifications",
        "Price alerts and triggers",
        "Trade execution confirmations",
        "Risk management warnings",
        "Customizable alert rules",
        "Mobile push notifications"
      ]
    },
    {
      icon: Lock,
      title: "Cold Storage",
      description: "Secure offline storage for your digital assets",
      highlight: "Secure",
      color: "text-indigo-500",
      details: [
        "Hardware wallet integration",
        "Multi-signature support",
        "Offline transaction signing",
        "Secure key management",
        "Automated hot-to-cold transfers",
        "Insurance coverage options",
        "Regulatory compliance"
      ]
    }
  ];
  
  const stats = [
    { label: "Active Traders", value: "10K+", icon: Users, color: "text-blue-500" },
    { label: "Trades Executed", value: "1M+", icon: BarChart3, color: "text-green-500" },
    { label: "Total Volume", value: "$500M+", icon: TrendingUp, color: "text-purple-500" },
    { label: "Success Rate", value: "94%", icon: Star, color: "text-yellow-500" }
  ];

  const pricingPlans = [
    {
      name: "Free",
      price: "$0",
      period: "forever",
      description: "Perfect for getting started",
      features: [
        "Basic trading features",
        "Paper trading mode",
        "Up to 5 trading bots",
        "Community support",
        "Basic analytics"
      ],
      popular: false,
      color: "border-blue-500"
    },
    {
      name: "Basic",
      price: "$49",
      period: "month",
      description: "For serious traders",
      features: [
        "All Free features",
        "Live trading enabled",
        "Up to 20 trading bots",
        "Priority support",
        "Advanced analytics",
        "Email notifications"
      ],
      popular: false,
      color: "border-blue-500"
    },
    {
      name: "Pro",
      price: "$99",
      period: "month",
      description: "For professional traders",
      features: [
        "All Basic features",
        "Unlimited trading bots",
        "Advanced ML models",
        "API access",
        "Custom strategies",
        "24/7 priority support",
        "Real-time WebSocket"
      ],
      popular: true,
      color: "border-blue-500"
    },
    {
      name: "Enterprise",
      price: "$299",
      period: "month",
      description: "For teams and institutions",
      features: [
        "All Pro features",
        "Dedicated account manager",
        "Custom integrations",
        "SLA guarantee",
        "White-label options",
        "Team collaboration",
        "Advanced reporting"
      ],
      popular: false,
      color: "border-blue-500"
    }
  ];

  const testimonials = [
    {
      name: "Alex Chen",
      role: "Professional Trader",
      content: "CryptoOrchestrator's AI models have increased my trading accuracy by 40%. The copy trading feature is a game-changer.",
      rating: 5
    },
    {
      name: "Sarah Martinez",
      role: "Crypto Fund Manager",
      content: "The blockchain-only trading and DEX aggregator integration are exactly what we needed. Lower fees and better control over our trades.",
      rating: 5
    },
    {
      name: "James Wilson",
      role: "Day Trader",
      content: "The real-time alerts and automated strategies save me hours every day. Best trading platform I've used.",
      rating: 5
    }
  ];

  const chains = ["Ethereum", "Base", "Arbitrum", "Polygon", "Optimism"];
  
  const handleOneClickInstall = () => {
    setShowInstallDialog(true);
    setInstallStep(1);
  };
  
  const handleInstallStep = async (step: number) => {
    if (step === 1) {
      const script = `#!/bin/bash
# CryptoOrchestrator One-Click Install Script
echo "🚀 Starting CryptoOrchestrator installation..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Clone repository (if not already cloned)
if [ ! -d "Crypto-Orchestrator" ]; then
    echo "📦 Cloning repository..."
    git clone https://github.com/yourusername/Crypto-Orchestrator.git
    cd Crypto-Orchestrator
else
    cd Crypto-Orchestrator
fi

# Create .env file
echo "⚙️  Setting up environment..."
cp .env.example .env
echo "📝 Please edit .env file with your configuration"

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T backend alembic upgrade head

echo "✅ Installation complete!"
echo "🌐 Access the platform at http://localhost:3000"
echo "📊 API docs at http://localhost:8000/docs"
`;
      
      const blob = new Blob([script], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'install-cryptoorchestrator.sh';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setInstallStep(2);
    } else if (step === 2) {
      setInstallStep(3);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="relative">
              <Zap className="h-6 w-6 text-primary animate-pulse" />
              <Sparkles className="h-3 w-3 text-yellow-400 absolute -top-1 -right-1" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
              CryptoOrchestrator
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link href="/register">
              <Button className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90">
                Sign Up Free
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative container mx-auto px-4 py-20 text-center overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-purple-500/10 to-pink-500/10 blur-3xl -z-10" />
        
        <div className="max-w-5xl mx-auto space-y-8 relative z-10">
          <Badge variant="outline" className="mb-4 px-4 py-1.5 text-sm border-primary/50 bg-primary/5">
            <Rocket className="h-3 w-3 mr-1.5 text-primary" />
            Enterprise-Grade Trading Platform
          </Badge>
          
          <h1 className="text-6xl md:text-7xl font-bold tracking-tight bg-gradient-to-r from-foreground via-primary to-purple-500 bg-clip-text text-transparent leading-tight">
            Trade Smarter,
            <br />
            <span className="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">
              Not Harder
            </span>
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            AI-powered trading bots, automatic copy trading, advanced strategies, and comprehensive risk management.
            <br />
            <span className="text-foreground font-semibold">The most advanced crypto trading platform available.</span>
          </p>
          
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-12">
            {stats.map((stat, idx) => {
              const Icon = stat.icon;
              return (
                <div key={idx} className="text-center p-4 rounded-xl bg-card border border-border hover:border-primary/50 transition-colors">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                    <div className="text-3xl font-bold">{stat.value}</div>
                  </div>
                  <div className="text-sm text-muted-foreground font-medium">{stat.label}</div>
                </div>
              );
            })}
          </div>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-8">
            <Link href="/register">
              <Button size="lg" className="gap-2 w-full sm:w-auto text-lg px-8 py-6 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 shadow-lg shadow-primary/25">
                Get Started Free
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
            <Dialog open={showInstallDialog} onOpenChange={setShowInstallDialog}>
              <DialogTrigger asChild>
                <Button size="lg" variant="outline" className="gap-2 w-full sm:w-auto text-lg px-8 py-6 border-2">
                  <Download className="h-5 w-5" />
                  One-Click Install
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>One-Click Installation</DialogTitle>
                  <DialogDescription>
                    Install CryptoOrchestrator in minutes
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  {installStep === 1 && (
                    <div className="space-y-4">
                      <p className="text-sm text-muted-foreground">
                        Download and run our installation script to get started in minutes.
                      </p>
                      <div className="bg-muted p-4 rounded-lg">
                        <h4 className="font-semibold mb-2">Requirements:</h4>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          <li>Docker and Docker Compose installed</li>
                          <li>At least 4GB RAM available</li>
                          <li>10GB free disk space</li>
                        </ul>
                      </div>
                      <Button onClick={() => handleInstallStep(1)} className="w-full gap-2">
                        <Download className="h-4 w-4" />
                        Download Install Script
                      </Button>
                    </div>
                  )}
                  {installStep === 2 && (
                    <div className="space-y-4">
                      <div className="bg-green-500/10 border border-green-500/20 p-4 rounded-lg">
                        <p className="text-sm">✅ Install script downloaded!</p>
                      </div>
                      <div className="space-y-2">
                        <h4 className="font-semibold">Next Steps:</h4>
                        <ol className="list-decimal list-inside space-y-2 text-sm">
                          <li>Make the script executable: <code className="bg-muted px-2 py-1 rounded">chmod +x install-cryptoorchestrator.sh</code></li>
                          <li>Run the script: <code className="bg-muted px-2 py-1 rounded">./install-cryptoorchestrator.sh</code></li>
                          <li>Edit the <code className="bg-muted px-2 py-1 rounded">.env</code> file with your configuration</li>
                          <li>Access the platform at <code className="bg-muted px-2 py-1 rounded">http://localhost:3000</code></li>
                        </ol>
                      </div>
                      <Button onClick={() => handleInstallStep(2)} className="w-full">
                        Got it!
                      </Button>
                    </div>
                  )}
                  {installStep === 3 && (
                    <div className="space-y-4">
                      <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-lg">
                        <p className="text-sm">📚 Need help? Check our documentation:</p>
                        <ul className="list-disc list-inside space-y-1 text-sm mt-2">
                          <li><a href="/docs" className="text-primary hover:underline">Installation Guide</a></li>
                          <li><a href="/docs/api" className="text-primary hover:underline">API Documentation</a></li>
                          <li><a href="/docs/architecture" className="text-primary hover:underline">Architecture Overview</a></li>
                        </ul>
                      </div>
                      <Button onClick={() => setShowInstallDialog(false)} className="w-full">
                        Close
                      </Button>
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>
            <Link href="/login">
              <Button size="lg" variant="outline" className="w-full sm:w-auto text-lg px-8 py-6 border-2">
                Login
              </Button>
            </Link>
          </div>

          {/* Trust indicators */}
          <div className="pt-12 flex flex-col items-center gap-4">
            <p className="text-sm text-muted-foreground">Trusted by traders on</p>
            <div className="flex flex-wrap items-center justify-center gap-6">
              {chains.map((chain, idx) => (
                <div key={idx} className="px-4 py-2 rounded-lg bg-muted/50 border border-border text-sm font-medium">
                  {chain}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <Badge variant="outline" className="mb-4">
            <Sparkles className="h-3 w-3 mr-1" />
            Powerful Features
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold mb-4">Everything You Need to Succeed</h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Comprehensive tools and features designed for both beginners and professional traders
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            const isExpanded = expandedFeature === idx;
            return (
              <Collapsible
                key={idx}
                open={isExpanded}
                onOpenChange={(open) => setExpandedFeature(open ? idx : null)}
                className="h-full flex flex-col"
              >
                <Card className="hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border-blue-500 border rounded-xl bg-card group h-full flex flex-col min-h-[280px]">
                  <CollapsibleTrigger asChild>
                    <button className="w-full text-left cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded-xl flex flex-col flex-1 h-full">
                      <CardHeader className="flex-shrink-0 pb-4">
                        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                          <Icon className={`h-7 w-7 ${feature.color}`} />
                        </div>
                        <div className="flex items-start justify-between gap-2 min-h-[2.75rem]">
                          <CardTitle className="text-xl font-semibold leading-tight flex-1">{feature.title}</CardTitle>
                          {feature.highlight && (
                            <Badge variant="secondary" className="text-xs whitespace-nowrap flex-shrink-0 mt-0.5">
                              {feature.highlight}
                            </Badge>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent className="flex-1 flex flex-col pt-0">
                        <CardDescription className="text-base mb-4 line-clamp-3 min-h-[4.5rem]">
                          {feature.description}
                        </CardDescription>
                        <div className="flex items-center justify-between text-sm text-primary mt-auto pt-2 border-t border-border/30">
                          <span className="font-medium">Click to see all features</span>
                          <ChevronRight className={`h-4 w-4 transition-transform duration-200 flex-shrink-0 ${isExpanded ? 'rotate-90' : ''}`} />
                        </div>
                      </CardContent>
                    </button>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="overflow-hidden transition-all duration-300 data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down">
                    <div className="px-6 pb-6 pt-0 border-t border-border/50">
                      <div className="space-y-3 mt-4">
                        <p className="text-sm font-semibold text-foreground mb-3">All Features:</p>
                        {feature.details.map((detail, detailIdx) => (
                          <div key={detailIdx} className="flex items-start gap-2 text-sm">
                            <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="text-muted-foreground">{detail}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CollapsibleContent>
                </Card>
              </Collapsible>
            );
          })}
        </div>
      </section>

      {/* Pricing Section - Enhanced */}
      <section className="container mx-auto px-4 py-20 bg-gradient-to-b from-background to-muted/30">
        <div className="text-center mb-16">
          <Badge variant="outline" className="mb-4">
            <DollarSign className="h-3 w-3 mr-1" />
            Simple Pricing
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold mb-4">Choose Your Plan</h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Start free, upgrade as you grow. No credit card required to get started.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
          {pricingPlans.map((plan, idx) => (
            <Card 
              key={idx} 
              className={`relative ${plan.color} border rounded-xl bg-card ${plan.popular ? 'shadow-2xl scale-105' : ''} transition-all hover:shadow-xl`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-10">
                  <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-1">
                    <Crown className="h-3 w-3 mr-1" />
                    Most Popular
                  </Badge>
                </div>
              )}
              
              <CardHeader className="text-center pb-4">
                <CardTitle className="text-2xl capitalize mb-2">{plan.name}</CardTitle>
                <div className="flex items-baseline justify-center gap-1 mb-2">
                  <span className="text-5xl font-bold">{plan.price}</span>
                  {plan.period !== "forever" && (
                    <span className="text-muted-foreground">/{plan.period}</span>
                  )}
                </div>
                <CardDescription className="text-base">{plan.description}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <ul className="space-y-3">
                  {plan.features.map((feature, featureIdx) => (
                    <li key={featureIdx} className="flex items-start gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link href="/register">
                  <Button 
                    className={`w-full mt-6 ${plan.popular ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600' : ''}`}
                    variant={plan.popular ? 'default' : 'outline'}
                    size="lg"
                  >
                    {plan.name === "Free" ? "Get Started" : plan.name === "Enterprise" ? "Contact Sales" : "Subscribe Now"}
                    {plan.name !== "Enterprise" && <ArrowRight className="h-4 w-4 ml-2" />}
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="text-center mt-12">
          <p className="text-sm text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 inline mr-1 text-green-500" />
            No credit card required • Cancel anytime • Instant access
          </p>
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <Badge variant="outline" className="mb-4">
            <Rocket className="h-3 w-3 mr-1" />
            Simple Process
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold mb-4">How It Works</h2>
          <p className="text-muted-foreground text-lg">
            Get started in three simple steps
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {[
            { step: "1", title: "Sign Up Free", description: "Create your account in seconds. No credit card required.", icon: UserPlus },
            { step: "2", title: "Create Wallet", description: "Set up a custodial wallet or connect your Web3 wallet. No API keys needed!", icon: Wallet },
            { step: "3", title: "Start Trading", description: "Choose a strategy or create your own. Let AI do the work.", icon: Rocket }
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="text-center relative">
                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center border-2 border-primary/30">
                  <Icon className="h-10 w-10 text-primary" />
                </div>
                <div className="absolute top-0 right-0 w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold text-sm">
                  {item.step}
                </div>
                <h3 className="text-xl font-bold mb-2">{item.title}</h3>
                <p className="text-muted-foreground">{item.description}</p>
                {idx < 2 && (
                  <ChevronRight className="hidden md:block absolute top-10 -right-4 text-muted-foreground h-8 w-8" />
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* Testimonials */}
      <section className="container mx-auto px-4 py-20 bg-muted/30">
        <div className="text-center mb-16">
          <Badge variant="outline" className="mb-4">
            <MessageSquare className="h-3 w-3 mr-1" />
            Testimonials
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold mb-4">What Our Users Say</h2>
          <p className="text-muted-foreground text-lg">
            Join thousands of satisfied traders
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {testimonials.map((testimonial, idx) => (
            <Card key={idx} className="hover:shadow-lg transition-shadow border-blue-500 border rounded-xl bg-card">
              <CardHeader>
                <div className="flex items-center gap-1 mb-2">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <CardDescription className="text-base italic">
                  "{testimonial.content}"
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="font-semibold">{testimonial.name}</div>
                <div className="text-sm text-muted-foreground">{testimonial.role}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Competitive Advantages */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <Badge variant="outline" className="mb-4">
            <Award className="h-3 w-3 mr-1" />
            Why Choose Us
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold mb-4">Competitive Advantages</h2>
          <p className="text-muted-foreground text-lg">
            What makes us better than the competition
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {[
            {
              icon: Zap,
              title: "Automatic Copy Trading",
              description: "Most platforms require manual copying. We automatically execute trades from top traders in real-time.",
              color: "text-yellow-500"
            },
            {
              icon: TrendingUp,
              title: "10x Faster Performance",
              description: "Redis caching and optimized queries make our platform 10x faster than competitors.",
              color: "text-green-500"
            },
            {
              icon: Shield,
              title: "Enterprise Security",
              description: "2FA, KYC, encrypted API keys, and bank-level security features with cold storage support.",
              color: "text-blue-500"
            }
          ].map((advantage, idx) => {
            const Icon = advantage.icon;
            return (
              <Card key={idx} className="text-center hover:shadow-xl transition-all border-blue-500 border rounded-xl bg-card">
                <CardHeader>
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center">
                    <Icon className={`h-8 w-8 ${advantage.color}`} />
                  </div>
                  <CardTitle className="text-xl">{advantage.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base">{advantage.description}</CardDescription>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Demo/Preview Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <Badge variant="outline" className="mb-4">
            <Play className="h-3 w-3 mr-1" />
            See It In Action
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold mb-4">Experience the Power</h2>
          <p className="text-muted-foreground text-lg">
            See what makes CryptoOrchestrator the best trading platform
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {[
            {
              title: "Live Trading Dashboard",
              description: "Real-time portfolio tracking, order book, and trade execution with advanced charts",
              icon: LineChart,
              gradient: "from-blue-500 to-cyan-500"
            },
            {
              title: "AI-Powered Strategies",
              description: "Machine learning models analyzing market patterns in real-time with 94% accuracy",
              icon: Brain,
              gradient: "from-purple-500 to-pink-500"
            }
          ].map((demo, idx) => {
            const Icon = demo.icon;
            return (
              <Card key={idx} className="overflow-hidden hover:shadow-xl transition-all group border-blue-500 border rounded-xl bg-card">
                <div className={`h-64 bg-gradient-to-br ${demo.gradient} flex items-center justify-center relative overflow-hidden`}>
                  <Icon className="h-24 w-24 text-white/20 group-hover:scale-110 transition-transform" />
                  <div className="absolute inset-0 bg-grid-pattern opacity-10" />
                </div>
                <CardHeader>
                  <CardTitle className="text-2xl">{demo.title}</CardTitle>
                  <CardDescription className="text-base">{demo.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Link href="/register">
                    <Button className="w-full" variant="outline" size="lg">
                      {idx === 0 ? "Try Demo" : "Explore Features"}
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <Card className="max-w-4xl mx-auto border-blue-500 border rounded-xl bg-card">
          <CardHeader className="text-center pb-4">
            <Badge variant="outline" className="mb-4">
              <Rocket className="h-3 w-3 mr-1" />
              Ready to Start?
            </Badge>
            <CardTitle className="text-4xl md:text-5xl mb-4">Ready to Start Trading?</CardTitle>
            <CardDescription className="text-xl">
              Join thousands of traders using CryptoOrchestrator to maximize their profits
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/register">
                <Button size="lg" className="w-full sm:w-auto text-lg px-10 py-6 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 shadow-lg shadow-primary/25">
                  Get Started Now
                  <ArrowRight className="h-5 w-5 ml-2" />
                </Button>
              </Link>
              <Button 
                size="lg" 
                variant="outline" 
                className="w-full sm:w-auto text-lg px-10 py-6 border-2"
                onClick={handleOneClickInstall}
              >
                <Download className="h-5 w-5 mr-2" />
                One-Click Install
              </Button>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Instant access
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                No credit card required
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                One-click installation
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Cancel anytime
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
