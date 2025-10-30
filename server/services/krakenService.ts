import ccxt from "ccxt";
import type { TradingPair, KrakenFee } from "@shared/schema";

export class KrakenService {
  private exchange: any;
  private connected: boolean = false;

  constructor() {
    this.exchange = new ccxt.kraken({
      apiKey: process.env.KRAKEN_API_KEY,
      secret: process.env.KRAKEN_SECRET_KEY,
      enableRateLimit: true,
    });
  }

  async connect(): Promise<void> {
    try {
      await this.exchange.loadMarkets();
      this.connected = true;
      console.log("Connected to Kraken API");
    } catch (error) {
      console.error("Failed to connect to Kraken:", error);
      this.connected = false;
    }
  }

  isConnected(): boolean {
    return this.connected;
  }

  async getAllTradingPairs(): Promise<TradingPair[]> {
    if (!this.connected) {
      await this.connect();
    }

    try {
      const tickers = await this.exchange.fetchTickers();
      const pairs: TradingPair[] = [];

      for (const [symbol, ticker] of Object.entries(tickers)) {
        const [baseAsset, quoteAsset] = symbol.split("/");
        if (!baseAsset || !quoteAsset) continue;
        
        const t = ticker as any;
        
        pairs.push({
          symbol,
          baseAsset,
          quoteAsset,
          currentPrice: t.last || 0,
          change24h: t.percentage || 0,
          volume24h: t.quoteVolume || 0,
          high24h: t.high || 0,
          low24h: t.low || 0,
        });
      }

      return pairs.sort((a, b) => b.volume24h - a.volume24h);
    } catch (error) {
      console.error("Error fetching trading pairs:", error);
      return [];
    }
  }

  async getMarketPrice(pair: string): Promise<number | null> {
    try {
      const ticker = await this.exchange.fetchTicker(pair);
      return ticker.last || null;
    } catch (error) {
      console.error(`Error fetching price for ${pair}:`, error);
      return null;
    }
  }

  async getOrderBook(pair: string): Promise<{ bids: Array<[number, number]>; asks: Array<[number, number]> }> {
    try {
      const orderBook = await this.exchange.fetchOrderBook(pair);
      return {
        bids: orderBook.bids.slice(0, 10),
        asks: orderBook.asks.slice(0, 10),
      };
    } catch (error) {
      console.error(`Error fetching order book for ${pair}:`, error);
      return { bids: [], asks: [] };
    }
  }

  getFees(volumeUSD: number = 0): KrakenFee {
    if (volumeUSD < 50000) {
      return { maker: 0.0016, taker: 0.0026 };
    } else if (volumeUSD < 100000) {
      return { maker: 0.0014, taker: 0.0024 };
    } else if (volumeUSD < 250000) {
      return { maker: 0.0012, taker: 0.0022 };
    } else if (volumeUSD < 500000) {
      return { maker: 0.0010, taker: 0.0020 };
    } else if (volumeUSD < 1000000) {
      return { maker: 0.0008, taker: 0.0018 };
    } else if (volumeUSD < 2500000) {
      return { maker: 0.0006, taker: 0.0016 };
    } else if (volumeUSD < 5000000) {
      return { maker: 0.0004, taker: 0.0014 };
    } else if (volumeUSD < 10000000) {
      return { maker: 0.0002, taker: 0.0012 };
    } else {
      return { maker: 0.0000, taker: 0.0010 };
    }
  }

  calculateFee(amount: number, price: number, isMaker: boolean = false, volumeUSD: number = 0): number {
    const fees = this.getFees(volumeUSD);
    const feeRate = isMaker ? fees.maker : fees.taker;
    const total = amount * price;
    return total * feeRate;
  }

  calculateTotalWithFee(amount: number, price: number, side: "buy" | "sell", isMaker: boolean = false, volumeUSD: number = 0): {
    subtotal: number;
    fee: number;
    total: number;
  } {
    const subtotal = amount * price;
    const fee = this.calculateFee(amount, price, isMaker, volumeUSD);
    const total = side === "buy" ? subtotal + fee : subtotal - fee;

    return { subtotal, fee, total };
  }

  async placeOrder(
    pair: string,
    side: "buy" | "sell",
    type: "market" | "limit",
    amount: number,
    price?: number
  ): Promise<any> {
    try {
      let order;
      if (type === "market") {
        order = side === "buy"
          ? await this.exchange.createMarketBuyOrder(pair, amount)
          : await this.exchange.createMarketSellOrder(pair, amount);
      } else if (type === "limit" && price) {
        order = side === "buy"
          ? await this.exchange.createLimitBuyOrder(pair, amount, price)
          : await this.exchange.createLimitSellOrder(pair, amount, price);
      } else {
        throw new Error("Invalid order type or missing price for limit order");
      }

      return order;
    } catch (error) {
      console.error("Error placing order:", error);
      throw error;
    }
  }

  async getBalance(): Promise<Record<string, number>> {
    try {
      const balance = await this.exchange.fetchBalance();
      return balance.total;
    } catch (error) {
      console.error("Error fetching balance:", error);
      return {};
    }
  }

  async getOHLCV(pair: string, timeframe: string = "1h", limit: number = 100): Promise<any[]> {
    try {
      const ohlcv = await this.exchange.fetchOHLCV(pair, timeframe, undefined, limit);
      return ohlcv;
    } catch (error) {
      console.error(`Error fetching OHLCV for ${pair}:`, error);
      return [];
    }
  }
}

export const krakenService = new KrakenService();
