import { useState, useCallback, useMemo } from "react";
import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TradingRecommendations, type RecommendationConfig } from "@/components/TradingRecommendations";
import { useCreateBot } from "@/hooks/useApi";
import { toast } from "@/hooks/use-toast";
import { Plus, Loader2, Target, AlertTriangle } from "lucide-react";
import { botConfigSchema, formatValidationErrors } from "@/lib/validation";
import { FormFieldError } from "@/components/FormFieldError";
import { useTradingMode } from "@/contexts/TradingModeContext";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { InsertBotConfig } from "../../../shared/schema";
import type { z } from "zod";

type BotFormData = z.infer<typeof botConfigSchema>;

const strategies = [
  { value: "smart_adaptive", label: "Smart Adaptive (AI v2.0)" },
  { value: "q-learning", label: "Q-Learning (ML)" },
  { value: "mean-reversion", label: "Mean Reversion" },
  { value: "trend-following", label: "Trend Following" },
  { value: "grid-trading", label: "Grid Trading" },
];

const tradingPairs = [
  { value: "BTC/USD", label: "BTC/USD" },
  { value: "ETH/USD", label: "ETH/USD" },
  { value: "SOL/USD", label: "SOL/USD" },
  { value: "ADA/USD", label: "ADA/USD" },
  { value: "DOT/USD", label: "DOT/USD" },
];

export const BotCreator = React.memo(function BotCreator() {
  const [open, setOpen] = useState(false);
  const createBotMutation = useCreateBot();
  const { mode, isRealMoney } = useTradingMode();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    reset,
  } = useForm<BotFormData>({
    resolver: zodResolver(botConfigSchema as any),
    defaultValues: {
      maxPositionSize: 0.1,
      stopLoss: 2.0,
      takeProfit: 5.0,
      riskPerTrade: 1.0,
    },
  });

  const onSubmit = async (data: BotFormData) => {
    try {
      // Use current trading mode instead of always defaulting to paper
      // Normalize "real" to "live" for bot config
      const botMode = mode === "real" ? "live" : mode;
      const botData: InsertBotConfig = {
        ...data,
        mode: botMode, // Use current trading mode (paper or live)
        status: "stopped",
      };
      
      // Show warning if creating bot in real money mode
      if (isRealMoney) {
        const confirmed = window.confirm(
          `⚠️ WARNING: You are creating a bot in REAL MONEY trading mode.\n\n` +
          `This bot will execute trades using your actual funds.\n\n` +
          `Make sure you:\n` +
          `1. Have tested this strategy in paper trading mode\n` +
          `2. Understand the risks involved\n` +
          `3. Have sufficient funds available\n\n` +
          `Do you want to continue?`
        );
        
        if (!confirmed) {
          return;
        }
      }

      await createBotMutation.mutateAsync(botData);
      toast({
        title: "Bot Created",
        description: `${data.name} has been created successfully.`,
      });
      reset();
      setOpen(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create bot. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleApplyRecommendation = useCallback((pair: string, config: RecommendationConfig) => {
    setValue("tradingPair", pair);
    setValue("riskPerTrade", config.riskPerTrade);
    setValue("stopLoss", config.stopLoss);
    setValue("takeProfit", config.takeProfit);
    setValue("maxPositionSize", config.maxPositionSize);

    toast({
      title: "Settings Applied",
      description: `Applied recommended settings for ${pair}`,
    });
  }, [setValue, toast]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button aria-label="Create new trading bot">
          <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
          Create Bot
        </Button>
      </DialogTrigger>
      <DialogContent 
        className="sm:max-w-[800px] max-h-[80vh] overflow-y-auto"
        aria-describedby="bot-creator-description"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Create New Trading Bot
          </DialogTitle>
          <DialogDescription id="bot-creator-description">
            Configure and launch a new automated trading bot
          </DialogDescription>
        </DialogHeader>

        {isRealMoney && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <div className="font-semibold mb-1">Real Money Trading Mode Active</div>
              <div className="text-sm">
                This bot will execute trades using your actual funds. Make sure you have tested your strategy in paper trading mode first.
              </div>
            </AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="manual" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="manual">Manual Setup</TabsTrigger>
            <TabsTrigger value="recommended">AI Recommendations</TabsTrigger>
          </TabsList>

          <TabsContent value="manual" className="space-y-4">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Bot Name</Label>
            <Input
              id="name"
              placeholder="e.g., ML Trend Follower"
              {...register("name")}
            />
            <FormFieldError error={errors.name?.message} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="strategy">Strategy</Label>
            <Select onValueChange={(value) => setValue("strategy", value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select a strategy" />
              </SelectTrigger>
              <SelectContent>
                {strategies.map((strategy) => (
                  <SelectItem key={strategy.value} value={strategy.value}>
                    {strategy.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormFieldError error={errors.strategy?.message} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="tradingPair">Trading Pair</Label>
            <Select onValueChange={(value) => setValue("tradingPair", value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select a trading pair" />
              </SelectTrigger>
              <SelectContent>
                {tradingPairs.map((pair) => (
                  <SelectItem key={pair.value} value={pair.value}>
                    {pair.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormFieldError error={errors.tradingPair?.message} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="maxPositionSize">Max Position Size</Label>
              <Input
                id="maxPositionSize"
                type="number"
                step="0.01"
                placeholder="0.1"
                {...register("maxPositionSize", { valueAsNumber: true })}
              />
              <FormFieldError error={errors.maxPositionSize?.message} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="riskPerTrade">Risk per Trade (%)</Label>
              <Input
                id="riskPerTrade"
                type="number"
                step="0.1"
                placeholder="1.0"
                {...register("riskPerTrade", { valueAsNumber: true })}
              />
              <FormFieldError error={errors.riskPerTrade?.message} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="stopLoss">Stop Loss (%)</Label>
              <Input
                id="stopLoss"
                type="number"
                step="0.1"
                placeholder="2.0"
                {...register("stopLoss", { valueAsNumber: true })}
              />
              <FormFieldError error={errors.stopLoss?.message} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="takeProfit">Take Profit (%)</Label>
              <Input
                id="takeProfit"
                type="number"
                step="0.1"
                placeholder="5.0"
                {...register("takeProfit", { valueAsNumber: true })}
              />
              <FormFieldError error={errors.takeProfit?.message} />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => setOpen(false)}
              aria-label="Cancel bot creation"
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={createBotMutation.isPending}
              aria-label={createBotMutation.isPending ? "Creating bot, please wait" : "Create trading bot"}
            >
              {createBotMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" aria-hidden="true" />
                  Creating...
                </>
              ) : (
                "Create Bot"
              )}
            </Button>
          </div>
            </form>
          </TabsContent>

          <TabsContent value="recommended" className="space-y-4">
            <TradingRecommendations onApplyRecommendation={handleApplyRecommendation} />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
});
