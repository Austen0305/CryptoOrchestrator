/**
 * Strategy Editor Component - Visual strategy builder
 */
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCreateStrategy, useUpdateStrategy, StrategyTemplate, Strategy } from "@/hooks/useStrategies";
import { Loader2, Save, Play, X } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface StrategyEditorProps {
  template?: StrategyTemplate | null;
  strategy?: Strategy | null;
  onClose?: () => void;
}

export function StrategyEditor({ template, strategy, onClose }: StrategyEditorProps) {
  const [name, setName] = useState(strategy?.name || template?.name || "");
  const [description, setDescription] = useState(strategy?.description || template?.description || "");
  const [strategyType, setStrategyType] = useState(
    strategy?.strategy_type || template?.strategy_type || "custom"
  );
  const [category, setCategory] = useState(strategy?.category || template?.category || "technical");
  const [config, setConfig] = useState<Record<string, any>>(
    strategy?.config || template?.config || {}
  );

  const createStrategy = useCreateStrategy();
  const updateStrategy = useUpdateStrategy();

  const handleSave = async () => {
    try {
      if (strategy) {
        // Update existing strategy
        await updateStrategy.mutateAsync({
          strategyId: strategy.id,
          data: {
            name,
            description,
            config,
          },
        });
        toast({
          title: "Strategy Updated",
          description: `${name} has been updated successfully.`,
        });
      } else {
        // Create new strategy
        await createStrategy.mutateAsync({
          name,
          description,
          strategy_type: strategyType,
          category,
          config,
          template_id: template?.strategy_type,
        });
        toast({
          title: "Strategy Created",
          description: `${name} has been created successfully.`,
        });
      }
      onClose?.();
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${strategy ? "update" : "create"} strategy.`,
        variant: "destructive",
      });
    }
  };

  const updateConfigValue = (key: string, value: any) => {
    setConfig((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{strategy ? "Edit Strategy" : "Create Strategy"}</CardTitle>
            <CardDescription>
              {template ? `Using template: ${template.name}` : "Configure your trading strategy"}
            </CardDescription>
          </div>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Strategy Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., My RSI Strategy"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your strategy..."
                rows={3}
              />
            </div>

            {!template && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="type">Strategy Type</Label>
                  <Select value={strategyType} onValueChange={setStrategyType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rsi">RSI</SelectItem>
                      <SelectItem value="macd">MACD</SelectItem>
                      <SelectItem value="breakout">Breakout</SelectItem>
                      <SelectItem value="lstm">LSTM</SelectItem>
                      <SelectItem value="transformer">Transformer</SelectItem>
                      <SelectItem value="custom">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="technical">Technical</SelectItem>
                      <SelectItem value="ml">Machine Learning</SelectItem>
                      <SelectItem value="hybrid">Hybrid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
          </div>

          {/* Configuration */}
          <Tabs defaultValue="risk" className="w-full">
            <TabsList>
              <TabsTrigger value="risk">Risk Management</TabsTrigger>
              <TabsTrigger value="trading">Trading Settings</TabsTrigger>
              <TabsTrigger value="advanced">Advanced</TabsTrigger>
            </TabsList>

            <TabsContent value="risk" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="stopLoss">Stop Loss (%)</Label>
                  <Input
                    id="stopLoss"
                    type="number"
                    value={config.stop_loss_pct || ""}
                    onChange={(e) => updateConfigValue("stop_loss_pct", parseFloat(e.target.value) || 0)}
                    placeholder="2.0"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="takeProfit">Take Profit (%)</Label>
                  <Input
                    id="takeProfit"
                    type="number"
                    value={config.take_profit_pct || ""}
                    onChange={(e) => updateConfigValue("take_profit_pct", parseFloat(e.target.value) || 0)}
                    placeholder="5.0"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="positionSize">Position Size (%)</Label>
                  <Input
                    id="positionSize"
                    type="number"
                    value={config.position_size_pct || ""}
                    onChange={(e) => updateConfigValue("position_size_pct", parseFloat(e.target.value) || 0)}
                    placeholder="10"
                  />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="trading" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="timeframe">Timeframe</Label>
                <Select
                  value={config.timeframe || "1h"}
                  onValueChange={(value) => updateConfigValue("timeframe", value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1m">1 Minute</SelectItem>
                    <SelectItem value="5m">5 Minutes</SelectItem>
                    <SelectItem value="15m">15 Minutes</SelectItem>
                    <SelectItem value="1h">1 Hour</SelectItem>
                    <SelectItem value="4h">4 Hours</SelectItem>
                    <SelectItem value="1d">1 Day</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Strategy-specific settings */}
              {strategyType === "rsi" && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="rsiPeriod">RSI Period</Label>
                    <Input
                      id="rsiPeriod"
                      type="number"
                      value={config.rsi_period || ""}
                      onChange={(e) => updateConfigValue("rsi_period", parseInt(e.target.value) || 14)}
                      placeholder="14"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="oversold">Oversold Threshold</Label>
                    <Input
                      id="oversold"
                      type="number"
                      value={config.oversold_threshold || ""}
                      onChange={(e) => updateConfigValue("oversold_threshold", parseInt(e.target.value) || 30)}
                      placeholder="30"
                    />
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="advanced" className="space-y-4">
              <div className="space-y-2">
                <Label>Advanced Configuration (JSON)</Label>
                <Textarea
                  value={JSON.stringify(config, null, 2)}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value);
                      setConfig(parsed);
                    } catch {
                      // Invalid JSON, ignore
                    }
                  }}
                  rows={10}
                  className="font-mono text-sm"
                />
              </div>
            </TabsContent>
          </Tabs>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2">
            {onClose && (
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
            )}
            <Button
              onClick={handleSave}
              disabled={!name || createStrategy.isPending || updateStrategy.isPending}
            >
              {(createStrategy.isPending || updateStrategy.isPending) ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              {strategy ? "Update Strategy" : "Create Strategy"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
