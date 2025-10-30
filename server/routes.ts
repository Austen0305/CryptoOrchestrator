import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer } from "ws";
import { storage } from "./storage";
import { krakenService } from "./services/krakenService";
import { paperTradingService } from "./services/paperTradingService";
import { botRunner } from "./services/botRunner";
import { insertTradeSchema, insertBotConfigSchema } from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  const httpServer = createServer(app);
  const wss = new WebSocketServer({ server: httpServer, path: "/ws" });

  wss.on("connection", (ws) => {
    console.log("WebSocket client connected");
    ws.send(JSON.stringify({ type: "connected", message: "Connected to CryptoML Trading Platform" }));
  });

  const broadcastUpdate = (type: string, data: any) => {
    wss.clients.forEach((client) => {
      if (client.readyState === 1) {
        client.send(JSON.stringify({ type, data }));
      }
    });
  };

  await krakenService.connect();

  const ingestMarketData = async () => {
    try {
      const pairs = await krakenService.getAllTradingPairs();
      await storage.updateTradingPairs(pairs);
      await paperTradingService.updatePortfolioPrices(pairs);

      for (const pair of pairs.slice(0, 20)) {
        try {
          const ohlcv = await krakenService.getOHLCV(pair.symbol, "1h", 1);
          if (ohlcv && ohlcv.length > 0) {
            const [timestamp, open, high, low, close, volume] = ohlcv[0];
            await storage.saveMarketData({
              pair: pair.symbol,
              timestamp,
              open,
              high,
              low,
              close,
              volume,
            });
          }
        } catch (error) {
          console.error(`Error ingesting data for ${pair.symbol}:`, error);
        }
      }

      broadcastUpdate("market_data", pairs);
    } catch (error) {
      console.error("Error updating market data:", error);
    }
  };

  ingestMarketData();

  setInterval(ingestMarketData, 60000);

  app.get("/api/markets", async (req, res) => {
    try {
      const pairs = await storage.getTradingPairs();
      res.json(pairs);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch markets" });
    }
  });

  app.get("/api/markets/:pair/ohlcv", async (req, res) => {
    try {
      const { pair } = req.params;
      const { timeframe = "1h", limit = "100" } = req.query;
      const ohlcv = await krakenService.getOHLCV(pair, timeframe as string, parseInt(limit as string));
      res.json(ohlcv);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch OHLCV data" });
    }
  });

  app.get("/api/markets/:pair/orderbook", async (req, res) => {
    try {
      const { pair } = req.params;
      const orderBook = await krakenService.getOrderBook(pair);
      res.json(orderBook);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch order book" });
    }
  });

  app.get("/api/portfolio/:mode", async (req, res) => {
    try {
      const { mode } = req.params;
      if (mode !== "paper" && mode !== "live") {
        return res.status(400).json({ error: "Invalid mode" });
      }
      const portfolio = await storage.getPortfolio(mode);
      res.json(portfolio);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch portfolio" });
    }
  });

  app.get("/api/trades", async (req, res) => {
    try {
      const { botId, mode } = req.query;
      const trades = await storage.getTrades(botId as string, mode as any);
      res.json(trades);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch trades" });
    }
  });

  app.post("/api/trades", async (req, res) => {
    try {
      const validated = insertTradeSchema.parse(req.body);
      
      if (validated.mode === "paper") {
        const result = await paperTradingService.executeTrade(
          validated.pair,
          validated.side,
          validated.type,
          validated.amount,
          validated.price,
          validated.botId
        );

        if (result.success) {
          const portfolio = await storage.getPortfolio("paper");
          broadcastUpdate("portfolio_update", { mode: "paper", portfolio });
          broadcastUpdate("trade_executed", result.trade);
          res.json(result.trade);
        } else {
          res.status(400).json({ error: result.error });
        }
      } else {
        res.status(501).json({ error: "Live trading not implemented yet" });
      }
    } catch (error) {
      res.status(400).json({ error: "Invalid trade data" });
    }
  });

  app.get("/api/bots", async (req, res) => {
    try {
      const bots = await storage.getBots();
      res.json(bots);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch bots" });
    }
  });

  app.get("/api/bots/:id", async (req, res) => {
    try {
      const bot = await storage.getBotById(req.params.id);
      if (!bot) {
        return res.status(404).json({ error: "Bot not found" });
      }
      res.json(bot);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch bot" });
    }
  });

  app.post("/api/bots", async (req, res) => {
    try {
      const validated = insertBotConfigSchema.parse(req.body);
      const bot = await storage.createBot(validated);
      broadcastUpdate("bot_created", bot);
      res.json(bot);
    } catch (error) {
      res.status(400).json({ error: "Invalid bot configuration" });
    }
  });

  app.patch("/api/bots/:id", async (req, res) => {
    try {
      const bot = await storage.updateBot(req.params.id, req.body);
      if (!bot) {
        return res.status(404).json({ error: "Bot not found" });
      }
      broadcastUpdate("bot_updated", bot);
      res.json(bot);
    } catch (error) {
      res.status(500).json({ error: "Failed to update bot" });
    }
  });

  app.delete("/api/bots/:id", async (req, res) => {
    try {
      const success = await storage.deleteBot(req.params.id);
      if (!success) {
        return res.status(404).json({ error: "Bot not found" });
      }
      broadcastUpdate("bot_deleted", { id: req.params.id });
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete bot" });
    }
  });

  app.post("/api/bots/:id/start", async (req, res) => {
    try {
      const result = await botRunner.startBot(req.params.id);
      if (result.success) {
        const bot = await storage.getBotById(req.params.id);
        broadcastUpdate("bot_status_changed", bot);
      }
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: "Failed to start bot" });
    }
  });

  app.post("/api/bots/:id/stop", async (req, res) => {
    try {
      const result = await botRunner.stopBot(req.params.id);
      if (result.success) {
        const bot = await storage.getBotById(req.params.id);
        broadcastUpdate("bot_status_changed", bot);
      }
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: "Failed to stop bot" });
    }
  });

  app.get("/api/bots/:id/model", async (req, res) => {
    try {
      const model = await storage.getMLModelState(req.params.id);
      if (!model) {
        return res.status(404).json({ error: "Model not found" });
      }
      res.json(model);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch model" });
    }
  });

  app.get("/api/bots/:id/performance", async (req, res) => {
    try {
      const metrics = await storage.getPerformanceMetrics(req.params.id);
      if (!metrics) {
        return res.status(404).json({ error: "Metrics not found" });
      }
      res.json(metrics);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch metrics" });
    }
  });

  app.get("/api/fees", async (req, res) => {
    try {
      const { volumeUSD = "0" } = req.query;
      const fees = krakenService.getFees(parseFloat(volumeUSD as string));
      res.json(fees);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch fees" });
    }
  });

  app.post("/api/fees/calculate", async (req, res) => {
    try {
      const { amount, price, side, isMaker, volumeUSD } = req.body;
      const result = krakenService.calculateTotalWithFee(
        amount,
        price,
        side,
        isMaker || false,
        volumeUSD || 0
      );
      res.json(result);
    } catch (error) {
      res.status(400).json({ error: "Invalid calculation parameters" });
    }
  });

  app.get("/api/status", async (req, res) => {
    try {
      const runningBots = await botRunner.getRunningBots();
      res.json({
        krakenConnected: krakenService.isConnected(),
        runningBots: runningBots.length,
        timestamp: Date.now(),
      });
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch status" });
    }
  });

  return httpServer;
}
