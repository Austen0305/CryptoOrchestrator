import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  useAnalyticsThresholds,
  useCreateAnalyticsThreshold,
  useUpdateAnalyticsThreshold,
  useDeleteAnalyticsThreshold,
  useTestAnalyticsThreshold,
  type AnalyticsThreshold,
  type CreateThresholdRequest,
} from "@/hooks/useMarketplace";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import {
  Bell,
  Plus,
  Edit,
  Trash2,
  Play,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

// Threshold type and metric options
const THRESHOLD_TYPES = [
  { value: "provider", label: "Provider" },
  { value: "developer", label: "Developer" },
  { value: "copy_trading", label: "Copy Trading" },
  { value: "indicator_marketplace", label: "Indicator Marketplace" },
  { value: "marketplace_overview", label: "Marketplace Overview" },
];

const METRICS = {
  provider: [
    { value: "total_return", label: "Total Return (%)" },
    { value: "sharpe_ratio", label: "Sharpe Ratio" },
    { value: "win_rate", label: "Win Rate (%)" },
    { value: "max_drawdown", label: "Max Drawdown (%)" },
    { value: "profit_factor", label: "Profit Factor" },
    { value: "average_rating", label: "Average Rating" },
    { value: "follower_count_change", label: "Follower Count Change" },
  ],
  developer: [
    { value: "indicator_revenue_drop_percent", label: "Revenue Drop (%)" },
    { value: "indicator_purchase_count_change", label: "Purchase Count Change" },
    { value: "indicator_average_rating", label: "Average Rating" },
  ],
  copy_trading: [
    { value: "revenue_drop_percent", label: "Revenue Drop (%)" },
    { value: "total_providers_change", label: "Total Providers Change" },
  ],
  indicator_marketplace: [
    { value: "indicator_revenue_drop_percent", label: "Revenue Drop (%)" },
    { value: "total_indicators_change", label: "Total Indicators Change" },
  ],
  marketplace_overview: [
    { value: "platform_revenue_drop_percent", label: "Platform Revenue Drop (%)" },
    { value: "total_providers_change", label: "Total Providers Change" },
    { value: "total_indicators_change", label: "Total Indicators Change" },
  ],
};

const OPERATORS = [
  { value: "gt", label: "Greater Than (>)", symbol: ">" },
  { value: "lt", label: "Less Than (<)", symbol: "<" },
  { value: "eq", label: "Equals (=)", symbol: "=" },
  { value: "gte", label: "Greater Than or Equal (≥)", symbol: "≥" },
  { value: "lte", label: "Less Than or Equal (≤)", symbol: "≤" },
  { value: "percent_change_down", label: "Percent Change Down (%)", symbol: "↓" },
  { value: "percent_change_up", label: "Percent Change Up (%)", symbol: "↑" },
];

interface ThresholdFormProps {
  threshold?: AnalyticsThreshold;
  onClose: () => void;
}

function ThresholdForm({ threshold, onClose }: ThresholdFormProps) {
  const { toast } = useToast();
  const createMutation = useCreateAnalyticsThreshold();
  const updateMutation = useUpdateAnalyticsThreshold();
  
  const [formData, setFormData] = useState<CreateThresholdRequest>({
    threshold_type: threshold?.threshold_type || "provider",
    metric: threshold?.metric || "",
    operator: threshold?.operator || "lt",
    threshold_value: threshold?.threshold_value || 0,
    context: threshold?.context || {},
    enabled: threshold?.enabled ?? true,
    notification_channels: threshold?.notification_channels || {
      email: true,
      push: true,
      in_app: true,
    },
    cooldown_minutes: threshold?.cooldown_minutes || 60,
    name: threshold?.name || "",
    description: threshold?.description || "",
  });

  const availableMetrics = METRICS[formData.threshold_type as keyof typeof METRICS] || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (threshold) {
        await updateMutation.mutateAsync({
          thresholdId: threshold.id,
          ...formData,
        });
        toast({
          title: "Threshold Updated",
          description: "Analytics threshold has been updated successfully",
        });
      } else {
        await createMutation.mutateAsync(formData);
        toast({
          title: "Threshold Created",
          description: "Analytics threshold has been created successfully",
        });
      }
      onClose();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error?.message || "Failed to save threshold",
        variant: "destructive",
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="e.g., Low Return Alert"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="threshold_type">Threshold Type</Label>
        <Select
          value={formData.threshold_type}
          onValueChange={(value) => {
            setFormData({ ...formData, threshold_type: value, metric: "" });
          }}
        >
          <SelectTrigger id="threshold_type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {THRESHOLD_TYPES.map((type) => (
              <SelectItem key={type.value} value={type.value}>
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="metric">Metric</Label>
        <Select
          value={formData.metric}
          onValueChange={(value) => setFormData({ ...formData, metric: value })}
        >
          <SelectTrigger id="metric">
            <SelectValue placeholder="Select a metric" />
          </SelectTrigger>
          <SelectContent>
            {availableMetrics.map((metric) => (
              <SelectItem key={metric.value} value={metric.value}>
                {metric.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="operator">Operator</Label>
          <Select
            value={formData.operator}
            onValueChange={(value) => setFormData({ ...formData, operator: value })}
          >
            <SelectTrigger id="operator">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {OPERATORS.map((op) => (
                <SelectItem key={op.value} value={op.value}>
                  {op.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="threshold_value">Threshold Value</Label>
          <Input
            id="threshold_value"
            type="number"
            step="0.01"
            value={formData.threshold_value}
            onChange={(e) =>
              setFormData({ ...formData, threshold_value: parseFloat(e.target.value) || 0 })
            }
          />
        </div>
      </div>

      {(formData.threshold_type === "provider" || formData.threshold_type === "developer") && (
        <div className="space-y-2">
          <Label htmlFor="context">
            {formData.threshold_type === "provider" ? "Provider ID" : "Developer ID"}
          </Label>
          <Input
            id="context"
            type="number"
            placeholder={`Enter ${formData.threshold_type} ID`}
            onChange={(e) => {
              const id = parseInt(e.target.value);
              setFormData({
                ...formData,
                context: {
                  [`${formData.threshold_type}_id`]: id,
                },
              });
            }}
            value={
              formData.context?.[`${formData.threshold_type}_id`]?.toString() || ""
            }
          />
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="cooldown_minutes">Cooldown (minutes)</Label>
        <Input
          id="cooldown_minutes"
          type="number"
          min="1"
          value={formData.cooldown_minutes}
          onChange={(e) =>
            setFormData({ ...formData, cooldown_minutes: parseInt(e.target.value) || 60 })
          }
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Optional description for this threshold"
          rows={3}
        />
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          id="enabled"
          checked={formData.enabled}
          onCheckedChange={(checked) => setFormData({ ...formData, enabled: checked })}
        />
        <Label htmlFor="enabled">Enabled</Label>
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
          {threshold ? "Update" : "Create"} Threshold
        </Button>
      </DialogFooter>
    </form>
  );
}

export function AnalyticsThresholdManager() {
  const { toast } = useToast();
  const { data: thresholds, isLoading, error } = useAnalyticsThresholds();
  const deleteMutation = useDeleteAnalyticsThreshold();
  const testMutation = useTestAnalyticsThreshold();
  const [editingThreshold, setEditingThreshold] = useState<AnalyticsThreshold | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const handleDelete = async (thresholdId: number) => {
    if (!confirm("Are you sure you want to delete this threshold?")) return;

    try {
      await deleteMutation.mutateAsync(thresholdId);
      toast({
        title: "Threshold Deleted",
        description: "Analytics threshold has been deleted successfully",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error?.message || "Failed to delete threshold",
        variant: "destructive",
      });
    }
  };

  const handleTest = async (thresholdId: number) => {
    try {
      const result = await testMutation.mutateAsync(thresholdId) as { triggered?: boolean; alert?: { current_value?: string | number; threshold_value?: string | number } } | undefined;
      const triggered = result?.triggered ?? !!(result as { alert?: unknown } | undefined)?.alert;
      toast({
        title: triggered ? "Threshold Triggered" : "Threshold Not Met",
        description: triggered
          ? `The threshold condition is currently met. Current value: ${result?.alert?.current_value ?? 'N/A'}, Threshold: ${result?.alert?.threshold_value ?? 'N/A'}`
          : "The threshold condition is not currently met",
        variant: triggered ? "default" : "default",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error?.message || "Failed to test threshold",
        variant: "destructive",
      });
    }
  };

  if (isLoading) {
    return <LoadingSkeleton variant="dashboard" className="h-[400px]" />;
  }

  if (error) {
    return <ErrorRetry error={error} onRetry={() => window.location.reload()} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Analytics Thresholds</h2>
          <p className="text-muted-foreground">
            Configure alerts for analytics metrics (revenue drops, follower count changes, etc.)
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Threshold
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create Analytics Threshold</DialogTitle>
              <DialogDescription>
                Set up alerts for when analytics metrics exceed configured thresholds
              </DialogDescription>
            </DialogHeader>
            <ThresholdForm onClose={() => setIsCreateDialogOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>

      {!thresholds || thresholds.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="No Thresholds Configured"
          description="Create your first analytics threshold to receive alerts when metrics exceed your configured values"
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Configured Thresholds</CardTitle>
            <CardDescription>
              {thresholds.length} threshold{thresholds.length !== 1 ? "s" : ""} configured
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Metric</TableHead>
                  <TableHead>Condition</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Triggered</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {thresholds.map((threshold) => {
                  const operator = OPERATORS.find((op) => op.value === threshold.operator);
                  return (
                    <TableRow key={threshold.id}>
                      <TableCell className="font-medium">
                        {threshold.name || "Unnamed Threshold"}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{threshold.threshold_type}</Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {threshold.metric}
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-sm">
                          {operator?.symbol || threshold.operator} {threshold.threshold_value}
                        </span>
                      </TableCell>
                      <TableCell>
                        {threshold.enabled ? (
                          <Badge variant="default" className="bg-green-500">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Enabled
                          </Badge>
                        ) : (
                          <Badge variant="secondary">
                            <XCircle className="h-3 w-3 mr-1" />
                            Disabled
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {threshold.last_triggered_at
                          ? new Date(threshold.last_triggered_at).toLocaleString()
                          : "Never"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleTest(threshold.id)}
                            disabled={testMutation.isPending}
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingThreshold(threshold)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(threshold.id)}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {editingThreshold && (
        <Dialog open={!!editingThreshold} onOpenChange={() => setEditingThreshold(null)}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Analytics Threshold</DialogTitle>
              <DialogDescription>
                Update threshold configuration
              </DialogDescription>
            </DialogHeader>
            <ThresholdForm
              threshold={editingThreshold}
              onClose={() => setEditingThreshold(null)}
            />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
