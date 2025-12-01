import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { GridTradingPanel } from "@/components/trading-bots/GridTradingPanel";
import { DCATradingPanel } from "@/components/trading-bots/DCATradingPanel";
import { InfinityGridPanel } from "@/components/trading-bots/InfinityGridPanel";
import { TrailingBotPanel } from "@/components/trading-bots/TrailingBotPanel";
import { FuturesTradingPanel } from "@/components/trading-bots/FuturesTradingPanel";
import { Grid, TrendingUp, Infinity, ArrowUpDown, BarChart3 } from "lucide-react";

export default function TradingBots() {
  return (
    <div className="space-y-6 w-full">
      <div>
        <h1 className="text-3xl font-bold">Advanced Trading Bots</h1>
        <p className="text-muted-foreground mt-1">
          Professional trading automation with competitive features
        </p>
      </div>

      <Tabs defaultValue="grid" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="grid" className="flex items-center gap-2">
            <Grid className="h-4 w-4" />
            Grid Trading
          </TabsTrigger>
          <TabsTrigger value="dca" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            DCA Bot
          </TabsTrigger>
          <TabsTrigger value="infinity" className="flex items-center gap-2">
            <Infinity className="h-4 w-4" />
            Infinity Grid
          </TabsTrigger>
          <TabsTrigger value="trailing" className="flex items-center gap-2">
            <ArrowUpDown className="h-4 w-4" />
            Trailing Bot
          </TabsTrigger>
          <TabsTrigger value="futures" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Futures
          </TabsTrigger>
        </TabsList>

        <TabsContent value="grid" className="mt-6">
          <GridTradingPanel />
        </TabsContent>

        <TabsContent value="dca" className="mt-6">
          <DCATradingPanel />
        </TabsContent>

        <TabsContent value="infinity" className="mt-6">
          <InfinityGridPanel />
        </TabsContent>

        <TabsContent value="trailing" className="mt-6">
          <TrailingBotPanel />
        </TabsContent>

        <TabsContent value="futures" className="mt-6">
          <FuturesTradingPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}

