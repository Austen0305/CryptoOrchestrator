export type OhlcvBar = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

/**
 * Generate synthetic OHLCV bars for quick demos/tests.
 * @param n Number of bars
 * @param startPrice Starting price
 * @param intervalMs Milliseconds between bars
 */
export function generateOhlcv(n = 50, startPrice = 100, intervalMs = 60_000): OhlcvBar[] {
  const now = Date.now();
  const out: OhlcvBar[] = [];
  let price = startPrice;
  for (let i = n - 1; i >= 0; i--) {
    const ts = new Date(now - i * intervalMs).toISOString();
    // small random walk
    const drift = (Math.random() - 0.5) * 0.8;
    const open = price;
    const close = price + drift;
    const high = Math.max(open, close) + Math.random() * 0.4;
    const low = Math.min(open, close) - Math.random() * 0.4;
    const volume = 8 + Math.floor(Math.random() * 10);
    out.push({ timestamp: ts, open, high, low, close, volume });
    price = close;
  }
  return out;
}
