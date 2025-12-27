import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { PortfolioCard } from "@/components/PortfolioCard";
import { TradingJournal } from "@/components/TradingJournal";
import { PortfolioPieChart } from "@/components/PortfolioPieChart";
import { ProfitCalendar } from "@/components/ProfitCalendar";
import { PerformanceAttribution } from "@/components/PerformanceAttribution";
import { EnhancedErrorBoundary } from "@/components/EnhancedErrorBoundary";
import logger from "@/lib/logger";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { TrendingUp, Target, Percent, Activity } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

function AnalyticsContent() {
  const performanceData = [
    { date: "Mon", profit: 450 },
    { date: "Tue", profit: 680 },
    { date: "Wed", profit: -200 },
    { date: "Thu", profit: 890 },
    { date: "Fri", profit: 1200 },
    { date: "Sat", profit: 750 },
    { date: "Sun", profit: 920 },
  ];

  const portfolioDistribution = [
    { name: "BTC", value: 45, color: "hsl(var(--chart-1))" },
    { name: "ETH", value: 25, color: "hsl(var(--chart-2))" },
    { name: "SOL", value: 15, color: "hsl(var(--chart-3))" },
    { name: "Others", value: 15, color: "hsl(var(--chart-4))" },
  ];

  return (
    <div className="space-y-6 w-full">
      <div>
        <h1 className="text-3xl font-bold" data-testid="analytics-page">Analytics</h1>
        <p className="text-muted-foreground mt-1">
          Track your trading performance and insights
        </p>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="attribution">Performance Attribution</TabsTrigger>
          <TabsTrigger value="journal">Trading Journal</TabsTrigger>
          <TabsTrigger value="calendar">Profit Calendar</TabsTrigger>
          <TabsTrigger value="allocation">Portfolio Allocation</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <PortfolioCard
          title="Total Profit"
          value="$8,420"
          change={15.3}
          icon={TrendingUp}
        />
        <PortfolioCard
          title="Win Rate"
          value="68%"
          change={3.2}
          icon={Target}
        />
        <PortfolioCard
          title="ROI"
          value="24.5%"
          change={5.1}
          icon={Percent}
        />
        <PortfolioCard
          title="Total Trades"
          value="287"
          icon={Activity}
          subtitle="Last 30 days"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Daily P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "hsl(var(--muted-foreground))" }}
                />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "6px",
                  }}
                />
                <Bar
                  dataKey="profit"
                  fill="hsl(var(--chart-1))"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Portfolio Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={portfolioDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {portfolioDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cumulative Returns</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={[
                { month: "Jan", returns: 0 },
                { month: "Feb", returns: 2.5 },
                { month: "Mar", returns: 5.2 },
                { month: "Apr", returns: 8.7 },
                { month: "May", returns: 12.3 },
                { month: "Jun", returns: 15.8 },
                { month: "Jul", returns: 18.4 },
                { month: "Aug", returns: 22.1 },
                { month: "Sep", returns: 24.5 },
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
              <XAxis
                dataKey="month"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
              />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "6px",
                }}
              />
              <Line
                type="monotone"
                dataKey="returns"
                stroke="hsl(var(--chart-1))"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
        </TabsContent>

        <TabsContent value="attribution">
          <PerformanceAttribution />
        </TabsContent>

        <TabsContent value="journal">
          <TradingJournal />
        </TabsContent>

        <TabsContent value="calendar">
          <ProfitCalendar />
        </TabsContent>

        <TabsContent value="allocation">
          <PortfolioPieChart />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default function Analytics() {
  return (
    <EnhancedErrorBoundary
      onError={(error, errorInfo) => {
        logger.error("Analytics page error", { error, errorInfo });
      }}
    >
      <AnalyticsContent />
    </EnhancedErrorBoundary>
  );
}
