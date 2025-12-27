/**
 * Strategy List Component - Display user's strategies
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyStrategiesState } from "@/components/EmptyState";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { useStrategies, Strategy } from "@/hooks/useStrategies";
import { Edit, Trash2, Play, BarChart3, Copy, Globe, Plus } from "lucide-react";
import { formatPercentage, formatCurrency } from "@/lib/formatters";
import { useState, useMemo } from "react";
import { useDeleteStrategy } from "@/hooks/useStrategies";
import { toast } from "@/hooks/use-toast";
import { usePagination } from "@/hooks/usePagination";
import { Pagination } from "@/components/Pagination";

interface StrategyListProps {
  /** Called when editing an existing strategy or creating a new one (pass null for new) */
  onEdit?: (strategy: Strategy | null) => void;
}

export function StrategyList({ onEdit }: StrategyListProps) {
  const { data: strategies, isLoading, error, refetch } = useStrategies(false);
  const deleteStrategy = useDeleteStrategy();
  
  // Pagination
  const pagination = usePagination({
    initialPage: 1,
    initialPageSize: 10,
    totalItems: strategies?.length || 0,
  });

  const paginatedStrategies = useMemo(() => {
    if (!strategies) return [];
    return strategies.slice(pagination.startIndex, pagination.endIndex);
  }, [strategies, pagination.startIndex, pagination.endIndex]);

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
        <CardHeader>
          <CardTitle>My Strategies</CardTitle>
          <CardDescription>Loading strategies...</CardDescription>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton variant="table" count={5} className="h-16" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>My Strategies</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorRetry
            title="Failed to load strategies"
            message={error instanceof Error ? error.message : "Unable to fetch strategies. Please try again."}
            onRetry={() => refetch()}
            error={error as Error}
          />
        </CardContent>
      </Card>
    );
  }

  if (!strategies || strategies.length === 0) {
    return (
      <EmptyStrategiesState onCreateStrategy={() => onEdit?.(null)} />
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>My Strategies</CardTitle>
        <CardDescription>
          Manage your trading strategies ({strategies?.length || 0} total)
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
            {paginatedStrategies.map((strategy) => (
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
                      {strategy.backtest_sharpe_ratio !== null && strategy.backtest_sharpe_ratio !== undefined && (
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
        
        {/* Pagination */}
        {strategies && strategies.length > pagination.pageSize && (
          <div className="mt-4 pt-4 border-t">
            <Pagination
              page={pagination.page}
              pageSize={pagination.pageSize}
              totalPages={pagination.totalPages}
              totalItems={pagination.totalItems}
              onPageChange={(page) => pagination.goToPage(page)}
              onPageSizeChange={(size) => pagination.setPageSize(size)}
              pageSizeOptions={[10, 20, 50]}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
