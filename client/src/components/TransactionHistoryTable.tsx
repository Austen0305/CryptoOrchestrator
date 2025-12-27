/**
 * Transaction History Table Component
 * Displays transaction history for a specific wallet
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorRetry } from "@/components/ErrorRetry";
import { EmptyState } from "@/components/EmptyState";
import { apiRequest } from "@/lib/queryClient";
import { formatCurrency, formatDate } from "@/lib/formatters";
import { RefreshCw, ExternalLink, Copy, Check } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

interface Transaction {
  transaction_hash: string;
  from_address?: string;
  to_address?: string;
  amount?: number;
  currency?: string;
  status?: "pending" | "confirmed" | "failed";
  timestamp?: string;
  block_number?: number;
  gas_used?: number;
  gas_price?: number;
}

interface TransactionHistoryTableProps {
  walletId: number | string;
  chainId?: number;
}

const CHAIN_EXPLORERS: Record<number, string> = {
  1: "https://etherscan.io/tx/",
  8453: "https://basescan.org/tx/",
  42161: "https://arbiscan.io/tx/",
  137: "https://polygonscan.com/tx/",
  10: "https://optimistic.etherscan.io/tx/",
  43114: "https://snowtrace.io/tx/",
  56: "https://bscscan.com/tx/",
};

export function TransactionHistoryTable({ walletId, chainId = 1 }: TransactionHistoryTableProps) {
  const { toast } = useToast();
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const { data: transactions, isLoading, error, refetch } = useQuery<Transaction[]>({
    queryKey: ["wallet-transactions", walletId],
    queryFn: async () => {
      const response = await apiRequest<Transaction[]>(`/api/wallets/${walletId}/transactions`, {
        method: "GET",
      });
      return response || [];
    },
    retry: 2,
    staleTime: 30000, // 30 seconds
  });

  const handleCopyHash = async (hash: string) => {
    try {
      await navigator.clipboard.writeText(hash);
      setCopiedHash(hash);
      toast({
        title: "Copied",
        description: "Transaction hash copied to clipboard",
      });
      setTimeout(() => setCopiedHash(null), 2000);
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to copy transaction hash",
        variant: "destructive",
      });
    }
  };

  const getExplorerUrl = (hash: string) => {
    const baseUrl = CHAIN_EXPLORERS[chainId] || CHAIN_EXPLORERS[1];
    return `${baseUrl}${hash}`;
  };

  const getStatusBadge = (status?: string) => {
    switch (status?.toLowerCase()) {
      case "confirmed":
        return <Badge variant="default" className="bg-green-500">Confirmed</Badge>;
      case "pending":
        return <Badge variant="secondary">Pending</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
          <CardDescription>Loading transaction history...</CardDescription>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
          <CardDescription>Failed to load transaction history</CardDescription>
        </CardHeader>
        <CardContent>
          <ErrorRetry
            title="Failed to load transactions"
            onRetry={() => refetch()}
            error={error as Error}
          />
        </CardContent>
      </Card>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Transaction History</CardTitle>
              <CardDescription>No transactions found for this wallet</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={RefreshCw}
            title="No Transactions"
            description="This wallet has no transaction history yet. Transactions will appear here once the wallet is used."
            action={{
              label: "Refresh",
              onClick: () => refetch(),
            }}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Transaction History</CardTitle>
            <CardDescription>
              {transactions.length} transaction{transactions.length !== 1 ? "s" : ""} found
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Hash</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>From</TableHead>
                <TableHead>To</TableHead>
                <TableHead>Timestamp</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions && Array.isArray(transactions) && transactions.length > 0 ? transactions.map((tx) => (
                <TableRow key={tx.transaction_hash}>
                  <TableCell className="font-mono text-xs">
                    <div className="flex items-center gap-2">
                      <span className="truncate max-w-[120px]">
                        {tx.transaction_hash.slice(0, 10)}...{tx.transaction_hash.slice(-8)}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => handleCopyHash(tx.transaction_hash)}
                        title="Copy hash"
                      >
                        {copiedHash === tx.transaction_hash ? (
                          <Check className="h-3 w-3 text-green-500" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(tx.status)}</TableCell>
                  <TableCell>
                    {tx.amount !== undefined && tx.currency
                      ? `${formatCurrency(tx.amount)} ${tx.currency}`
                      : "N/A"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {tx.from_address ? (
                      <span className="truncate max-w-[100px] block">
                        {tx.from_address.slice(0, 6)}...{tx.from_address.slice(-4)}
                      </span>
                    ) : (
                      "N/A"
                    )}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {tx.to_address ? (
                      <span className="truncate max-w-[100px] block">
                        {tx.to_address.slice(0, 6)}...{tx.to_address.slice(-4)}
                      </span>
                    ) : (
                      "N/A"
                    )}
                  </TableCell>
                  <TableCell className="text-sm">
                    {tx.timestamp ? formatDate(tx.timestamp) : "N/A"}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={() => window.open(getExplorerUrl(tx.transaction_hash), "_blank")}
                      title="View on explorer"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              )) : (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                    No transactions found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

