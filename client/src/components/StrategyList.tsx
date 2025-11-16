/**
 * Strategy List Component - Display user's strategies
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useStrategies, Strategy } from "@/hooks/useStrategies";
import { Loader2, Edit, Trash2, Play, BarChart3, Copy, Globe, Plus } from "lucide-react";
import { formatPercentage, formatCurrency } from "@/lib/formatters";
import { useState } from "react";
import { useDeleteStrategy } from "@/hooks/useStrategies";
import { toast } from "@/hooks/use-toast";

interface StrategyListProps {
  onEdit?: (strategy: Strategy) => void;
}

export function StrategyList({ onEdit }: StrategyListProps) {
  const { data: strategies, isLoading } = useStrategies(false);
  const deleteStrategy = useDeleteStrategy();

  const handleDelete = async (strategyId: string, strategyName: string) => {
    if (!confirm(`Are you sure you want to delete "${strategyName}"?`)) {
      return;
    }

    try {
      await deleteStrategy.mutateAsync(strategyId);
      toast({
        title: "Strategy Deleted",
        description: `${strategyName} has been deleted.`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete strategy.",
        variant: "destructive",
      });
    }
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

  if (!strategies || strategies.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground mb-4">No strategies found.</p>
          <Button onClick={() => onEdit?.(null as any)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Your First Strategy
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>My Strategies</CardTitle>
        <CardDescription>
          Manage your trading strategies ({strategies.length} total)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Version</TableHead>
              <TableHead>Performance</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {strategies.map((strategy) => (
              <TableRow key={strategy.id}>
                <TableCell>
                  <div>
                    <div className="font-medium">{strategy.name}</div>
                    {strategy.description && (
                      <div className="text-sm text-muted-foreground">
                        {strategy.description.substring(0, 60)}...
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{strategy.strategy_type.toUpperCase()}</Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{strategy.category}</Badge>
                </TableCell>
                <TableCell>{strategy.version}</TableCell>
                <TableCell>
                  {strategy.backtest_win_rate !== null ? (
                    <div className="space-y-1">
                      <div className="text-sm">
                        Win Rate: {formatPercentage(strategy.backtest_win_rate)}
                      </div>
                      {strategy.backtest_sharpe_ratio !== null && (
                        <div className="text-sm text-muted-foreground">
                          Sharpe: {strategy.backtest_sharpe_ratio.toFixed(2)}
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-muted-foreground text-sm">Not tested</span>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {strategy.is_published && (
                      <Badge variant="default" className="gap-1">
                        <Globe className="h-3 w-3" />
                        Published
                      </Badge>
                    )}
                    {!strategy.is_published && strategy.is_public && (
                      <Badge variant="secondary">Public</Badge>
                    )}
                    {!strategy.is_public && (
                      <Badge variant="outline">Private</Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    {onEdit && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(strategy)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(strategy.id, strategy.name)}
                      disabled={deleteStrategy.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
