/**
 * Utility functions for exporting data to various formats
 */

export interface ExportOptions {
  filename?: string;
  dateFormat?: string;
}

/**
 * Convert data to CSV format and trigger download
 */
export function exportToCSV<T extends Record<string, any>>(
  data: T[],
  options: ExportOptions = {}
): void {
  if (!data || data.length === 0) {
    throw new Error('No data to export');
  }

  const filename = options.filename || `export-${Date.now()}.csv`;
  
  // Get headers from first object
  const headers = Object.keys(data[0]);
  
  // Create CSV content
  const csvContent = [
    // Headers
    headers.join(','),
    // Rows
    ...data.map((row) =>
      headers
        .map((header) => {
          const value = row[header];
          // Handle values that contain commas, quotes, or newlines
          if (
            typeof value === 'string' &&
            (value.includes(',') || value.includes('"') || value.includes('\n'))
          ) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value ?? '';
        })
        .join(',')
    ),
  ].join('\n');

  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  downloadBlob(blob, filename);
}

/**
 * Convert data to JSON format and trigger download
 */
export function exportToJSON<T>(
  data: T,
  options: ExportOptions = {}
): void {
  const filename = options.filename || `export-${Date.now()}.json`;
  
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
  
  downloadBlob(blob, filename);
}

/**
 * Helper function to trigger file download
 */
function downloadBlob(blob: Blob, filename: string): void {
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // Clean up URL
  setTimeout(() => URL.revokeObjectURL(url), 100);
}

/**
 * Format trade data for export
 */
export function formatTradesForExport(trades: any[]) {
  return trades.map((trade) => ({
    Date: new Date(trade.timestamp || trade.date).toISOString(),
    Symbol: trade.symbol || trade.pair,
    Side: trade.side,
    Type: trade.type,
    Price: trade.price,
    Amount: trade.amount,
    Total: trade.total || (trade.price * trade.amount),
    Fee: trade.fee || 0,
    'P&L': trade.pnl || trade.profit || 0,
    Status: trade.status || 'completed',
  }));
}

/**
 * Format portfolio data for export
 */
export function formatPortfolioForExport(portfolio: any) {
  return {
    exportDate: new Date().toISOString(),
    totalBalance: portfolio.totalBalance,
    profitLoss: portfolio.profitLossTotal,
    profitLoss24h: portfolio.profitLoss24h,
    positions: portfolio.positions?.map((pos: any) => ({
      asset: pos.asset,
      balance: pos.balance,
      value: pos.value,
      allocation: pos.allocation,
      avgPrice: pos.avgPrice,
      currentPrice: pos.currentPrice,
      pnl: pos.pnl,
      pnlPercent: pos.pnlPercent,
    })) || [],
  };
}

/**
 * Format bot data for export
 */
export function formatBotsForExport(bots: any[]) {
  return bots.map((bot) => ({
    Name: bot.name,
    Strategy: bot.strategy,
    Status: bot.status,
    Symbol: bot.symbol,
    'Start Date': bot.startDate ? new Date(bot.startDate).toISOString() : '',
    'Total Trades': bot.totalTrades || 0,
    'Win Rate': bot.winRate ? `${bot.winRate}%` : '0%',
    'Total P&L': bot.totalPnl || 0,
    'Current Position': bot.currentPosition || 'None',
  }));
}

/**
 * Format analytics data for export
 */
export function formatAnalyticsForExport(analytics: any) {
  return {
    exportDate: new Date().toISOString(),
    period: analytics.period || 'all-time',
    metrics: {
      totalProfit: analytics.totalProfit,
      totalTrades: analytics.totalTrades,
      winRate: analytics.winRate,
      avgWin: analytics.avgWin,
      avgLoss: analytics.avgLoss,
      largestWin: analytics.largestWin,
      largestLoss: analytics.largestLoss,
      profitFactor: analytics.profitFactor,
      sharpeRatio: analytics.sharpeRatio,
      maxDrawdown: analytics.maxDrawdown,
    },
    dailyPerformance: analytics.dailyData || [],
  };
}

/**
 * Export component data with toast notification
 */
export async function exportWithNotification(
  exportFn: () => void,
  toast: any,
  successMessage = 'Data exported successfully'
): Promise<void> {
  try {
    exportFn();
    toast({
      title: 'Export Successful',
      description: successMessage,
    });
  } catch (error) {
    console.error('Export failed:', error);
    toast({
      title: 'Export Failed',
      description: error instanceof Error ? error.message : 'Failed to export data',
      variant: 'destructive',
    });
  }
}
