import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useCloseFuturesPosition, useUpdatePositionPnl } from "@/hooks/useApi";
import { toast } from "@/hooks/use-toast";
import { X, RefreshCw, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";
import { useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface FuturesPositionCardProps {
  position: any;
}

export function FuturesPositionCard({ position }: FuturesPositionCardProps) {
  const closePosition = useCloseFuturesPosition();
  const updatePnl = useUpdatePositionPnl();

  const handleClose = async () => {
    try {
      await closePosition.mutateAsync({ id: position.id });
      toast({ title: "Position Closed", description: `${position.name || position.symbol} has been closed.` });
    } catch (error) {
      toast({ title: "Error", description: "Failed to close position.", variant: "destructive" });
    }
  };

  const handleUpdatePnl = async () => {
    try {
      await updatePnl.mutateAsync(position.id);
      toast({ title: "P&L Updated", description: "Position P&L has been updated." });
    } catch (error) {
      toast({ title: "Error", description: "Failed to update P&L.", variant: "destructive" });
    }
  };

  const isOpen = position.is_open;
  const pnlColor = position.total_pnl >= 0 ? "text-green-500" : "text-red-500";
  const PnlIcon = position.total_pnl >= 0 ? TrendingUp : TrendingDown;
  const liquidationRisk = position.liquidation_risk || 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{position.name || `${position.side.toUpperCase()} ${position.symbol}`}</CardTitle>
            <CardDescription className="mt-1">
              {position.symbol} • {position.exchange} • {position.leverage}x
            </CardDescription>
          </div>
          <Badge variant={isOpen ? "default" : "secondary"}>
            {position.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Entry Price</p>
            <p className="font-medium">${position.entry_price?.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Current Price</p>
            <p className="font-medium">${position.current_price?.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Quantity</p>
            <p className="font-medium">{position.quantity}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Margin Used</p>
            <p className="font-medium">${position.margin_used?.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Total P&L</p>
            <p className={`font-medium flex items-center gap-1 ${pnlColor}`}>
              <PnlIcon className="h-4 w-4" />
              ${position.total_pnl?.toFixed(2) || "0.00"}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">P&L %</p>
            <p className={`font-medium ${pnlColor}`}>
              {position.pnl_percent?.toFixed(2) || "0.00"}%
            </p>
          </div>
        </div>

        {isOpen && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Liquidation Risk</span>
              <span className={liquidationRisk > 50 ? "text-red-500 font-medium" : "text-muted-foreground"}>
                {liquidationRisk.toFixed(1)}%
              </span>
            </div>
            <Progress value={liquidationRisk} className={liquidationRisk > 50 ? "bg-red-500" : ""} />
            {liquidationRisk > 50 && (
              <div className="flex items-center gap-2 text-sm text-red-500">
                <AlertTriangle className="h-4 w-4" />
                <span>High liquidation risk</span>
              </div>
            )}
          </div>
        )}

        {isOpen && (
          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleUpdatePnl}
              disabled={updatePnl.isPending}
              className="flex-1"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Update P&L
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" size="sm" disabled={closePosition.isPending}>
                  <X className="h-4 w-4" />
                  Close
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Close Position?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will close {position.name || position.symbol} position. This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleClose}>Close Position</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

