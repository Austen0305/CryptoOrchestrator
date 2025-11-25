/**
 * Utility functions for exporting data to various formats
 */

import jsPDF from 'jspdf';
import 'jspdf-autotable';

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
 * Convert data to PDF format and trigger download
 */
export function exportToPDF<T extends Record<string, any>>(
  data: T[],
  options: ExportOptions & {
    title?: string;
    headers?: string[];
    columns?: Array<{ header: string; dataKey: string }>;
  } = {}
): void {
  if (!data || data.length === 0) {
    throw new Error('No data to export');
  }

  const filename = options.filename || `export-${Date.now()}.pdf`;
  const title = options.title || 'Export Report';
  const doc = new jsPDF();

  // Add title
  doc.setFontSize(18);
  doc.text(title, 14, 22);

  // Add export date
  doc.setFontSize(10);
  doc.setTextColor(100, 100, 100);
  doc.text(`Exported: ${new Date().toLocaleString()}`, 14, 30);

  // Prepare table data
  const tableHeaders = options.headers || Object.keys(data[0]);
  const rows = data.map((row) =>
    tableHeaders.map((header) => {
      const value = row[header];
      // Format dates, numbers, etc.
      if (value instanceof Date) {
        return value.toLocaleString();
      }
      if (typeof value === 'number') {
        return value.toLocaleString();
      }
      return value?.toString() || '';
    })
  );

  // Add table
  (doc as any).autoTable({
    head: [tableHeaders],
    body: rows,
    startY: 35,
    styles: { fontSize: 9 },
    headStyles: { fillColor: [66, 139, 202] },
    alternateRowStyles: { fillColor: [245, 247, 250] },
  });

  // Save PDF
  doc.save(filename);
}

/**
 * Export trades to PDF with formatted table
 */
export function exportTradesToPDF(trades: any[], options: ExportOptions = {}): void {
  const filename = options.filename || `trades-${Date.now()}.pdf`;
  const formattedTrades = formatTradesForExport(trades);

  exportToPDF(formattedTrades, {
    ...options,
    filename,
    title: 'Trade History Report',
    headers: ['Date', 'Symbol', 'Side', 'Type', 'Price', 'Amount', 'Total', 'Fee', 'P&L', 'Status'],
  });
}

/**
 * Export portfolio to PDF
 */
export function exportPortfolioToPDF(portfolio: any, options: ExportOptions = {}): void {
  const filename = options.filename || `portfolio-${Date.now()}.pdf`;
  const doc = new jsPDF();

  // Title
  doc.setFontSize(18);
  doc.text('Portfolio Report', 14, 22);

  // Export date
  doc.setFontSize(10);
  doc.setTextColor(100, 100, 100);
  doc.text(`Exported: ${new Date().toLocaleString()}`, 14, 30);

  // Summary section
  doc.setFontSize(14);
  doc.setTextColor(0, 0, 0);
  doc.text('Summary', 14, 45);

  doc.setFontSize(11);
  let yPos = 55;
  doc.text(`Total Balance: $${portfolio.totalBalance?.toLocaleString() || '0'}`, 14, yPos);
  yPos += 10;
  doc.text(`Total P&L: $${portfolio.profitLossTotal?.toLocaleString() || '0'}`, 14, yPos);
  yPos += 10;
  doc.text(`24h P&L: $${portfolio.profitLoss24h?.toLocaleString() || '0'}`, 14, yPos);
  yPos += 15;

  // Positions table
  if (portfolio.positions && portfolio.positions.length > 0) {
    doc.setFontSize(14);
    doc.text('Positions', 14, yPos);
    yPos += 10;

    const formattedPortfolio = formatPortfolioForExport(portfolio);
    const positions = formattedPortfolio.positions || [];

    const headers = ['Asset', 'Balance', 'Value', 'Allocation', 'Avg Price', 'Current Price', 'P&L', 'P&L %'];
    const rows = positions.map((pos: any) => [
      pos.asset,
      pos.balance?.toFixed(8) || '0',
      `$${pos.value?.toLocaleString() || '0'}`,
      `${pos.allocation?.toFixed(2) || '0'}%`,
      `$${pos.avgPrice?.toLocaleString() || '0'}`,
      `$${pos.currentPrice?.toLocaleString() || '0'}`,
      `$${pos.pnl?.toLocaleString() || '0'}`,
      `${pos.pnlPercent?.toFixed(2) || '0'}%`,
    ]);

    (doc as any).autoTable({
      head: [headers],
      body: rows,
      startY: yPos,
      styles: { fontSize: 9 },
      headStyles: { fillColor: [66, 139, 202] },
      alternateRowStyles: { fillColor: [245, 247, 250] },
    });
  }

  doc.save(filename);
}

/**
 * Export analytics to PDF
 */
export function exportAnalyticsToPDF(analytics: any, options: ExportOptions = {}): void {
  const filename = options.filename || `analytics-${Date.now()}.pdf`;
  const doc = new jsPDF();

  // Title
  doc.setFontSize(18);
  doc.text('Analytics Report', 14, 22);

  // Export date
  doc.setFontSize(10);
  doc.setTextColor(100, 100, 100);
  doc.text(`Exported: ${new Date().toLocaleString()}`, 14, 30);

  const formatted = formatAnalyticsForExport(analytics);
  let yPos = 45;

  // Metrics section
  doc.setFontSize(14);
  doc.setTextColor(0, 0, 0);
  doc.text('Performance Metrics', 14, yPos);
  yPos += 10;

  doc.setFontSize(11);
  if (formatted.metrics) {
    const metrics = formatted.metrics;
    doc.text(`Total Profit: $${metrics.totalProfit?.toLocaleString() || '0'}`, 14, yPos);
    yPos += 10;
    doc.text(`Total Trades: ${metrics.totalTrades || 0}`, 14, yPos);
    yPos += 10;
    doc.text(`Win Rate: ${metrics.winRate?.toFixed(2) || '0'}%`, 14, yPos);
    yPos += 10;
    doc.text(`Profit Factor: ${metrics.profitFactor?.toFixed(2) || '0'}`, 14, yPos);
    yPos += 10;
    doc.text(`Sharpe Ratio: ${metrics.sharpeRatio?.toFixed(2) || '0'}`, 14, yPos);
    yPos += 10;
    doc.text(`Max Drawdown: ${metrics.maxDrawdown?.toFixed(2) || '0'}%`, 14, yPos);
    yPos += 15;
  }

  // Daily performance table
  if (formatted.dailyPerformance && formatted.dailyPerformance.length > 0) {
    doc.setFontSize(14);
    doc.text('Daily Performance', 14, yPos);
    yPos += 10;

    const headers = ['Date', 'Profit', 'Trades', 'Win Rate'];
    const rows = formatted.dailyPerformance.map((day: any) => [
      new Date(day.date).toLocaleDateString(),
      `$${day.profit?.toLocaleString() || '0'}`,
      day.trades?.toString() || '0',
      `${day.winRate?.toFixed(2) || '0'}%`,
    ]);

    (doc as any).autoTable({
      head: [headers],
      body: rows,
      startY: yPos,
      styles: { fontSize: 9 },
      headStyles: { fillColor: [66, 139, 202] },
      alternateRowStyles: { fillColor: [245, 247, 250] },
    });
  }

  doc.save(filename);
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
