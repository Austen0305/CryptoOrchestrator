/**
 * Formatting utilities for currency, percentages, and numbers
 */

export function formatCurrency(value: number | string | undefined | null, currency: string = "USD"): string {
  if (value === undefined || value === null || value === "") return "$0.00";
  
  const numValue = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(numValue)) return "$0.00";
  
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numValue);
}

export function formatPercentage(value: number | string | undefined | null, decimals: number = 2): string {
  if (value === undefined || value === null || value === "") return "0.00%";
  
  const numValue = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(numValue)) return "0.00%";
  
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(numValue / 100);
}

export function formatNumber(value: number | string | undefined | null, decimals: number = 2): string {
  if (value === undefined || value === null || value === "") return "0";
  
  const numValue = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(numValue)) return "0";
  
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(numValue);
}

export function formatLargeNumber(value: number | string | undefined | null): string {
  if (value === undefined || value === null || value === "") return "0";
  
  const numValue = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(numValue)) return "0";
  
  if (Math.abs(numValue) >= 1e9) {
    return `${(numValue / 1e9).toFixed(2)}B`;
  }
  if (Math.abs(numValue) >= 1e6) {
    return `${(numValue / 1e6).toFixed(2)}M`;
  }
  if (Math.abs(numValue) >= 1e3) {
    return `${(numValue / 1e3).toFixed(2)}K`;
  }
  
  return numValue.toFixed(2);
}

export function formatDate(value: Date | string | number | undefined | null, format: string = "PP"): string {
  if (!value) return "";
  
  const date = value instanceof Date ? value : new Date(value);
  if (isNaN(date.getTime())) return "";
  
  // Simple date formatting - for more complex needs, use date-fns format()
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(value: Date | string | number | undefined | null): string {
  if (!value) return "";
  
  const date = value instanceof Date ? value : new Date(value);
  if (isNaN(date.getTime())) return "";
  
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatCompactNumber(value: number | string | undefined | null): string {
  if (value === undefined || value === null || value === "") return "0";
  
  const numValue = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(numValue)) return "0";
  
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(numValue);
}

