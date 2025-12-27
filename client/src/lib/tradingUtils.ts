/**
 * Trading utility functions.
 * Centralizes common trading-related operations.
 */

/**
 * Normalize trading mode: 'live' -> 'real' for backend compatibility.
 * 
 * The frontend may use 'live' as a user-friendly term, but the backend
 * uses 'real' to represent live trading mode.
 * 
 * @param mode - Trading mode ('paper', 'real', or 'live')
 * @returns Normalized trading mode ('paper' or 'real')
 * 
 * @example
 * normalizeTradingMode("live") // returns "real"
 * normalizeTradingMode("real") // returns "real"
 * normalizeTradingMode("paper") // returns "paper"
 */
export function normalizeTradingMode(
  mode: "paper" | "real" | "live"
): "paper" | "real" {
  return mode === "live" ? "real" : mode;
}
