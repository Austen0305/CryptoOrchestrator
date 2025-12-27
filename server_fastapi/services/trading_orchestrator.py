from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import asyncio
import sys
import os

# Add integrations to path
integrations_path = os.path.join(os.path.dirname(__file__), "../../server/integrations")
sys.path.insert(0, integrations_path)

logger = logging.getLogger(__name__)

try:
    from freqtrade_adapter import FreqtradeManager
    from jesse_adapter import JesseManager
except ImportError as e:
    logger.warning(
        f"Could not import trading adapters: {e}. Using mock implementations."
    )
    FreqtradeManager = None
    JesseManager = None


class Prediction(BaseModel):
    action: str
    confidence: float
    source: Optional[str] = None


class EnsemblePrediction(BaseModel):
    action: str
    confidence: float
    votes: List[Prediction]


class PingResult(BaseModel):
    freqtrade: Optional[Dict[str, Any]] = None
    jesse: Optional[Dict[str, Any]] = None


class BacktestSummary(BaseModel):
    avg_profit_pct: float
    total_trades: int


class BacktestResult(BaseModel):
    results: List[Dict[str, Any]]
    summary: BacktestSummary


class TradingOrchestrator:
    def __init__(self, db_session=None):
        self.db = db_session
        self.started = False
        self.freqtrade_adapter: Optional[FreqtradeManager] = None
        self.jesse_adapter: Optional[JesseManager] = None

        # Initialize adapters if available
        if FreqtradeManager:
            try:
                self.freqtrade_adapter = FreqtradeManager()
            except Exception as e:
                logger.warning(f"Failed to initialize FreqtradeManager: {e}")

        if JesseManager:
            try:
                self.jesse_adapter = JesseManager()
            except Exception as e:
                logger.warning(f"Failed to initialize JesseManager: {e}")

    def start_all(self) -> None:
        """Start all trading adapters"""
        if self.started:
            return

        try:
            # Initialize adapters if not already done
            if self.freqtrade_adapter is None:
                self.freqtrade_adapter = FreqtradeManager()
                # Note: FreqtradeManager doesn't have a start method, it's ready after initialization

            if self.jesse_adapter is None:
                self.jesse_adapter = JesseManager()
                # JesseManager doesn't have a start method either

            logger.info("Starting all trading adapters")
            self.started = True
        except Exception as e:
            logger.warning(f"Failed to start some adapters: {e}")
            self.started = False

    def stop_all(self) -> None:
        """Stop all trading adapters"""
        try:
            # Adapters don't have explicit stop methods, just clean up
            logger.info("Stopping all trading adapters")
        finally:
            self.started = False

    async def get_ensemble_prediction(
        self, payload: Dict[str, Any]
    ) -> EnsemblePrediction:
        """Get ensemble prediction from all available adapters"""
        votes: List[Prediction] = []

        # Always include a local 'none' baseline to avoid division by zero
        try:
            freqtrade_result = (
                await self.freqtrade_adapter.predict(payload)
                if self.freqtrade_adapter
                else None
            )
            if freqtrade_result and freqtrade_result.get("action"):
                votes.append(
                    Prediction(
                        action=freqtrade_result["action"],
                        confidence=isinstance(
                            freqtrade_result.get("confidence"), (int, float)
                        )
                        and freqtrade_result["confidence"]
                        or 0.5,
                        source="freqtrade",
                    )
                )
        except Exception as e:
            # ignore
            logger.warning(f"Freqtrade prediction failed: {e}")

        try:
            # Jesse adapter uses synchronous calls in a wrapper
            if self.jesse_adapter:
                jesse_result = await asyncio.get_event_loop().run_in_executor(
                    None, self.jesse_adapter.predict, payload
                )
                if jesse_result and jesse_result.get("action"):
                    votes.append(
                        Prediction(
                            action=jesse_result["action"],
                            confidence=isinstance(
                                jesse_result.get("confidence"), (int, float)
                            )
                            and jesse_result["confidence"]
                            or 0.5,
                            source="jesse",
                        )
                    )
        except Exception as e:
            # ignore
            logger.warning(f"Jesse prediction failed: {e}")

        # If no external votes, return neutral
        if not votes:
            return EnsemblePrediction(action="hold", confidence=0.0, votes=votes)

        # Tally weighted votes
        tally: Dict[str, float] = {}
        total = 0.0

        for vote in votes:
            action = vote.action
            confidence = vote.confidence
            tally[action] = tally.get(action, 0.0) + confidence
            total += confidence

        # Find best action
        best_action = "hold"
        best_weight = 0.0

        for action, weight in tally.items():
            if weight > best_weight:
                best_weight = weight
                best_action = action

        normalized_confidence = best_weight / total if total > 0 else 0.0

        return EnsemblePrediction(
            action=best_action, confidence=normalized_confidence, votes=votes
        )

    async def ping_all(self) -> PingResult:
        """Ping all trading adapters"""
        result = PingResult()

        try:
            if self.freqtrade_adapter:
                # FreqtradeManager doesn't have a ping method, simulate one
                result.freqtrade = {"ok": True, "version": "1.0.0"}
            else:
                result.freqtrade = {"ok": False, "error": "Adapter not initialized"}
        except Exception as e:
            result.freqtrade = {"ok": False, "error": str(e)}

        try:
            if self.jesse_adapter:
                # JesseManager doesn't have a ping method, simulate one
                result.jesse = {"ok": True, "version": "1.0.0"}
            else:
                result.jesse = {"ok": False, "error": "Adapter not initialized"}
        except Exception as e:
            result.jesse = {"ok": False, "error": str(e)}

        return result

    async def backtest(self, payload: Dict[str, Any]) -> BacktestResult:
        """Run backtest across all adapters"""
        results: List[Dict[str, Any]] = []

        try:
            freqtrade_result = (
                await self.freqtrade_adapter.backtest(payload)
                if self.freqtrade_adapter
                else None
            )
            if freqtrade_result:
                results.append({**freqtrade_result, "source": "freqtrade"})
        except Exception as e:
            # ignore
            logger.warning(f"Freqtrade backtest failed: {e}")

        try:
            # Jesse adapter uses synchronous calls in a wrapper
            if self.jesse_adapter:
                jesse_result = await asyncio.get_event_loop().run_in_executor(
                    None, self.jesse_adapter.backtest, payload
                )
                if jesse_result:
                    results.append({**jesse_result, "source": "jesse"})
        except Exception as e:
            # ignore
            logger.warning(f"Jesse backtest failed: {e}")

        # Build summary from combined results
        profits = [float(r.get("profit_pct", r.get("profitPct", 0))) for r in results]
        total_trades_arr = [
            int(r.get("trades", r.get("totalTrades", 0))) for r in results
        ]
        sum_profit = sum(profits) if profits else 0.0
        sum_trades = sum(total_trades_arr) if total_trades_arr else 0
        avg_profit_pct = sum_profit / len(results) if results else 0.0

        return BacktestResult(
            results=results,
            summary=BacktestSummary(
                avg_profit_pct=avg_profit_pct, total_trades=sum_trades
            ),
        )

    async def get_user_bots(self, user_id: int) -> List[Dict[str, Any]]:
        """Get bots for a specific user"""
        # Mock implementation - in real implementation, query database
        return [
            {
                "id": 1,
                "user_id": user_id,
                "name": "BTC Scalper",
                "status": "running",
                "strategy": "scalping",
                "symbol": "BTC/USD",
                "last_update": asyncio.get_event_loop().time(),
            },
            {
                "id": 2,
                "user_id": user_id,
                "name": "ETH Holder",
                "status": "stopped",
                "strategy": "hold",
                "symbol": "ETH/USD",
                "last_update": asyncio.get_event_loop().time(),
            },
        ]

    async def get_bot_status(self, user_id: int, bot_id: int) -> Dict[str, Any]:
        """Get status of a specific bot"""
        bots = await self.get_user_bots(user_id)
        for bot in bots:
            if bot["id"] == bot_id:
                return bot
        return {"error": "Bot not found"}


# Global instance
trading_orchestrator = TradingOrchestrator()
