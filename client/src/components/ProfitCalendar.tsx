import React, { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar } from "@/components/ui/calendar";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TrendingUp, TrendingDown, Calendar as CalendarIcon, Download } from "lucide-react";
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday } from "date-fns";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/formatters";

interface DailyProfit {
  date: Date;
  profit: number;
  trades: number;
  winRate: number;
}

export function ProfitCalendar() {
  const [selectedMonth, setSelectedMonth] = React.useState<Date>(new Date());
  const [viewMode, setViewMode] = React.useState<"profit" | "trades" | "winrate">("profit");

  // Mock daily profit data - in production, this would come from the API
  const dailyProfits = useMemo<Map<string, DailyProfit>>(() => {
    const profits = new Map<string, DailyProfit>();
    const today = new Date();
    
    // Generate mock data for the current month
    for (let i = 0; i < 30; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateKey = format(date, "yyyy-MM-dd");
      
      profits.set(dateKey, {
        date,
        profit: Math.random() * 2000 - 500, // Random profit between -500 and 1500
        trades: Math.floor(Math.random() * 10) + 1,
        winRate: Math.random() * 100,
      });
    }
    
    return profits;
  }, []);

  const monthStart = startOfMonth(selectedMonth);
  const monthEnd = endOfMonth(selectedMonth);
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd });

  const getDayData = (date: Date): DailyProfit | null => {
    const dateKey = format(date, "yyyy-MM-dd");
    return dailyProfits.get(dateKey) || null;
  };

  const getDayValue = (day: DailyProfit | null): number => {
    if (!day) return 0;
    switch (viewMode) {
      case "profit":
        return day.profit;
      case "trades":
        return day.trades;
      case "winrate":
        return day.winRate;
      default:
        return 0;
    }
  };

  const getDayColor = (value: number, maxValue: number): string => {
    if (value === 0) return "bg-muted";
    
    const percentage = Math.abs(value) / maxValue;
    const isPositive = value > 0;
    
    if (viewMode === "profit") {
      if (isPositive) {
        return `bg-green-${Math.min(500 + Math.floor(percentage * 400), 900)}`;
      } else {
        return `bg-red-${Math.min(500 + Math.floor(percentage * 400), 900)}`;
      }
    } else {
      // For trades and winrate, use blue scale
      return `bg-blue-${Math.min(500 + Math.floor(percentage * 400), 900)}`;
    }
  };

  const maxValue = useMemo(() => {
    let max = 0;
    dailyProfits.forEach(day => {
      const value = getDayValue(day);
      if (Math.abs(value) > max) max = Math.abs(value);
    });
    return max || 1;
  }, [dailyProfits, viewMode]);

  const monthTotal = useMemo(() => {
    let total = 0;
    let tradeCount = 0;
    let winningDays = 0;
    
    dailyProfits.forEach(day => {
      if (isSameMonth(day.date, selectedMonth)) {
        total += day.profit;
        tradeCount += day.trades;
        if (day.profit > 0) winningDays++;
      }
    });
    
    return { total, tradeCount, winningDays, totalDays: dailyProfits.size };
  }, [dailyProfits, selectedMonth]);

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CalendarIcon className="h-5 w-5" />
              Profit Calendar
            </CardTitle>
            <CardDescription>
              Daily profit/loss heatmap visualization
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Select value={viewMode} onValueChange={(value: any) => setViewMode(value)}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="profit">Profit/Loss</SelectItem>
                <SelectItem value="trades">Trades</SelectItem>
                <SelectItem value="winrate">Win Rate</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Month Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm font-medium text-muted-foreground">Month Total</div>
              <div className={cn(
                "text-2xl font-bold",
                monthTotal.total >= 0 ? "text-green-500" : "text-red-500"
              )}>
                {formatCurrency(monthTotal.total)}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm font-medium text-muted-foreground">Total Trades</div>
              <div className="text-2xl font-bold">{monthTotal.tradeCount}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm font-medium text-muted-foreground">Winning Days</div>
              <div className="text-2xl font-bold text-green-500">{monthTotal.winningDays}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm font-medium text-muted-foreground">Win Rate</div>
              <div className="text-2xl font-bold">
                {monthTotal.totalDays > 0
                  ? `${Math.round((monthTotal.winningDays / monthTotal.totalDays) * 100)}%`
                  : "0%"}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Calendar Grid */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">
              {format(selectedMonth, "MMMM yyyy")}
            </h3>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const newDate = new Date(selectedMonth);
                  newDate.setMonth(newDate.getMonth() - 1);
                  setSelectedMonth(newDate);
                }}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedMonth(new Date())}
              >
                Today
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const newDate = new Date(selectedMonth);
                  newDate.setMonth(newDate.getMonth() + 1);
                  setSelectedMonth(newDate);
                }}
              >
                Next
              </Button>
            </div>
          </div>

          {/* Calendar Header */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div key={day} className="text-center text-sm font-medium text-muted-foreground p-2">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-1">
            {days.map((day) => {
              const dayData = getDayData(day);
              const value = getDayValue(dayData);
              const isCurrentMonth = isSameMonth(day, selectedMonth);
              
              return (
                <div
                  key={day.toISOString()}
                  className={cn(
                    "aspect-square rounded-md border-2 flex flex-col items-center justify-center p-1 cursor-pointer hover:ring-2 hover:ring-primary transition-all",
                    !isCurrentMonth && "opacity-30",
                    isToday(day) && "ring-2 ring-primary",
                    value !== 0 && getDayColor(value, maxValue),
                    value === 0 && "bg-muted",
                    value > 0 && viewMode === "profit" && "bg-green-500/20 border-green-500/50",
                    value < 0 && viewMode === "profit" && "bg-red-500/20 border-red-500/50"
                  )}
                  title={
                    dayData
                      ? `${format(day, "MMM dd")}: ${
                          viewMode === "profit"
                            ? formatCurrency(value)
                            : viewMode === "trades"
                            ? `${value} trades`
                            : `${value.toFixed(1)}% win rate`
                        }`
                      : format(day, "MMM dd")
                  }
                >
                  <div className="text-xs font-medium">
                    {format(day, "d")}
                  </div>
                  {dayData && value !== 0 && (
                    <div className="text-[10px] font-bold mt-0.5">
                      {viewMode === "profit" ? (
                        <span className={value >= 0 ? "text-green-700" : "text-red-700"}>
                          {value >= 0 ? "+" : ""}
                          {formatCurrency(value).replace("$", "").replace(".00", "")}
                        </span>
                      ) : viewMode === "trades" ? (
                        <span className="text-blue-700">{value}</span>
                      ) : (
                        <span className="text-blue-700">{value.toFixed(0)}%</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-green-500/20 border border-green-500/50" />
                <span>Profit</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-red-500/20 border border-red-500/50" />
                <span>Loss</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-muted border" />
                <span>No Data</span>
              </div>
            </div>
            <div className="text-xs">
              Hover over dates for details
            </div>
          </div>
        </div>

        {/* Best/Worst Days */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <div className="font-medium">Best Day</div>
              </div>
              {(() => {
                let bestDay: DailyProfit | null = null;
                dailyProfits.forEach(day => {
                  if (isSameMonth(day.date, selectedMonth)) {
                    if (!bestDay || day.profit > bestDay.profit) {
                      bestDay = day;
                    }
                  }
                });
                return bestDay ? (
                  <div>
                    <div className="text-2xl font-bold text-green-500">
                      {formatCurrency(bestDay.profit)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {format(bestDay.date, "MMM dd, yyyy")} • {bestDay.trades} trades
                    </div>
                  </div>
                ) : (
                  <div className="text-muted-foreground">No data</div>
                );
              })()}
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingDown className="h-4 w-4 text-red-500" />
                <div className="font-medium">Worst Day</div>
              </div>
              {(() => {
                let worstDay: DailyProfit | null = null;
                dailyProfits.forEach(day => {
                  if (isSameMonth(day.date, selectedMonth)) {
                    if (!worstDay || day.profit < worstDay.profit) {
                      worstDay = day;
                    }
                  }
                });
                return worstDay ? (
                  <div>
                    <div className="text-2xl font-bold text-red-500">
                      {formatCurrency(worstDay.profit)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {format(worstDay.date, "MMM dd, yyyy")} • {worstDay.trades} trades
                    </div>
                  </div>
                ) : (
                  <div className="text-muted-foreground">No data</div>
                );
              })()}
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  );
}

