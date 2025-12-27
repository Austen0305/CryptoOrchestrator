/**
 * Transaction Status Component
 * Shows pending transactions with status, confirmation count, and explorer links
 */
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle2, XCircle, Clock, Loader2, ExternalLink, Copy, Check } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface TransactionStatusProps {
  transactionHash: string;
  chainId: number;
  status?: "pending" | "confirmed" | "failed";
  blockNumber?: number;
  confirmations?: number;
  requiredConfirmations?: number;
  onClose?: () => void;
}

const CHAIN_EXPLORERS: Record<number, string> = {
  1: "https://etherscan.io",
  8453: "https://basescan.org",
  42161: "https://arbiscan.io",
  137: "https://polygonscan.com",
  10: "https://optimistic.etherscan.io",
  43114: "https://snowtrace.io",
  56: "https://bscscan.com",
};

export function TransactionStatus({
  transactionHash,
  chainId,
  status = "pending",
  blockNumber,
  confirmations = 0,
  requiredConfirmations = 1,
  onClose,
}: TransactionStatusProps) {
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);

  const explorerUrl = CHAIN_EXPLORERS[chainId] || CHAIN_EXPLORERS[1];
  const txUrl = `${explorerUrl}/tx/${transactionHash}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(transactionHash);
    setCopied(true);
    toast({
      title: "Copied",
      description: "Transaction hash copied to clipboard",
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusIcon = () => {
    switch (status) {
      case "confirmed":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "failed":
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case "confirmed":
        return (
          <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
            Confirmed
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive">
            Failed
          </Badge>
        );
      default:
        return (
          <Badge className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
            Pending
          </Badge>
        );
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {getStatusIcon()}
            Transaction Status
          </CardTitle>
          {getStatusBadge()}
        </div>
        <CardDescription>
          {status === "confirmed"
            ? "Transaction confirmed on blockchain"
            : status === "failed"
            ? "Transaction failed"
            : "Waiting for blockchain confirmation"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Transaction Hash */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-muted-foreground">Transaction Hash</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
          <code className="text-sm font-mono bg-muted px-3 py-2 rounded block break-all">
            {transactionHash}
          </code>
        </div>

        {/* Status Details */}
        {status === "pending" && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Confirmations</span>
              <span className="font-medium">
                {confirmations} / {requiredConfirmations}
              </span>
            </div>
            {confirmations < requiredConfirmations && (
              <Alert>
                <Loader2 className="h-4 w-4 animate-spin" />
                <AlertDescription>
                  Waiting for {requiredConfirmations - confirmations} more confirmation
                  {requiredConfirmations - confirmations !== 1 ? "s" : ""}...
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {status === "confirmed" && blockNumber && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Block Number</span>
              <span className="font-medium">{blockNumber.toLocaleString()}</span>
            </div>
            <Alert>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <AlertDescription>
                Transaction confirmed and included in block {blockNumber.toLocaleString()}
              </AlertDescription>
            </Alert>
          </div>
        )}

        {status === "failed" && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>
              Transaction failed. Please check the transaction on the blockchain explorer for details.
            </AlertDescription>
          </Alert>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => window.open(txUrl, "_blank")}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            View on Explorer
          </Button>
          {onClose && (
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
