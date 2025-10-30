import type { Portfolio, InsertTrade, TradingPair } from "@shared/schema";
import { storage } from "../storage";
import { krakenService } from "./krakenService";

export class PaperTradingService {
  async executeTrade(
    pair: string,
    side: "buy" | "sell",
    type: "market" | "limit",
    amount: number,
    price?: number,
    botId?: string
  ): Promise<{ success: boolean; trade?: any; error?: string }> {
    try {
      const portfolio = await storage.getPortfolio("paper");

      const currentPrice = price || (await krakenService.getMarketPrice(pair));
      if (!currentPrice) {
        return { success: false, error: "Could not fetch market price" };
      }

      const feeCalc = krakenService.calculateTotalWithFee(
        amount,
        currentPrice,
        side,
        type === "limit",
        0
      );

      if (side === "buy") {
        if (portfolio.availableBalance < feeCalc.total) {
          return { success: false, error: "Insufficient balance" };
        }

        portfolio.availableBalance -= feeCalc.total;

        const [baseAsset] = pair.split("/");
        if (!portfolio.positions[baseAsset]) {
          portfolio.positions[baseAsset] = {
            asset: baseAsset,
            amount: 0,
            averagePrice: 0,
            currentPrice,
            totalValue: 0,
            profitLoss: 0,
            profitLossPercent: 0,
          };
        }

        const position = portfolio.positions[baseAsset];
        const totalAmount = position.amount + amount;
        position.averagePrice = (position.averagePrice * position.amount + currentPrice * amount) / totalAmount;
        position.amount = totalAmount;
        position.currentPrice = currentPrice;
        position.totalValue = totalAmount * currentPrice;
        position.profitLoss = (currentPrice - position.averagePrice) * totalAmount;
        position.profitLossPercent = ((currentPrice - position.averagePrice) / position.averagePrice) * 100;
      } else {
        const [baseAsset] = pair.split("/");
        const position = portfolio.positions[baseAsset];

        if (!position || position.amount < amount) {
          return { success: false, error: "Insufficient position" };
        }

        portfolio.availableBalance += feeCalc.total;

        position.amount -= amount;
        if (position.amount === 0) {
          delete portfolio.positions[baseAsset];
        } else {
          position.totalValue = position.amount * currentPrice;
          position.currentPrice = currentPrice;
          position.profitLoss = (currentPrice - position.averagePrice) * position.amount;
          position.profitLossPercent = ((currentPrice - position.averagePrice) / position.averagePrice) * 100;
        }
      }

      portfolio.totalBalance = portfolio.availableBalance + Object.values(portfolio.positions).reduce((sum, pos) => sum + pos.totalValue, 0);

      await storage.updatePortfolio("paper", portfolio);

      const trade = await storage.createTrade({
        botId,
        pair,
        side,
        type,
        amount,
        price: currentPrice,
        fee: feeCalc.fee,
        total: feeCalc.subtotal,
        totalWithFee: feeCalc.total,
        status: "completed",
        mode: "paper",
      });

      return { success: true, trade };
    } catch (error) {
      console.error("Error executing paper trade:", error);
      return { success: false, error: error instanceof Error ? error.message : "Unknown error" };
    }
  }

  async getPortfolio(): Promise<Portfolio> {
    return await storage.getPortfolio("paper");
  }

  async updatePortfolioPrices(pairs: TradingPair[]): Promise<void> {
    const portfolio = await storage.getPortfolio("paper");

    for (const asset in portfolio.positions) {
      const pair = pairs.find(p => p.baseAsset === asset);
      if (pair) {
        const position = portfolio.positions[asset];
        position.currentPrice = pair.currentPrice;
        position.totalValue = position.amount * pair.currentPrice;
        position.profitLoss = (pair.currentPrice - position.averagePrice) * position.amount;
        position.profitLossPercent = ((pair.currentPrice - position.averagePrice) / position.averagePrice) * 100;
      }
    }

    portfolio.totalBalance = portfolio.availableBalance + Object.values(portfolio.positions).reduce((sum, pos) => sum + pos.totalValue, 0);

    await storage.updatePortfolio("paper", portfolio);
  }
}

export const paperTradingService = new PaperTradingService();
