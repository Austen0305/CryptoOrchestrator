"""
Market Microstructure Data Service
Provides detailed market microstructure data for high-frequency trading
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Individual trade data point"""

    pair: str
    price: float
    quantity: float
    side: str  # "buy" or "sell"
    timestamp: int  # Nanosecond timestamp
    trade_id: str | None = None


@dataclass
class MarketMicrostructure:
    """Market microstructure metrics"""

    pair: str
    timestamp: int

    # Order book metrics
    bid_ask_spread: float
    mid_price: float
    weighted_mid_price: float

    # Volume metrics
    bid_volume: float  # Total volume on bid side
    ask_volume: float  # Total volume on ask side
    volume_imbalance: float  # (bid_volume - ask_volume) / (bid_volume + ask_volume)

    # Price impact estimates
    price_impact_1pct: float  # Estimated price impact for 1% of daily volume
    price_impact_5pct: float  # Estimated price impact for 5% of daily volume

    # Trade flow
    buy_volume: float  # Volume of buy trades in last period
    sell_volume: float  # Volume of sell trades in last period
    trade_flow_imbalance: (
        float  # (buy_volume - sell_volume) / (buy_volume + sell_volume)
    )

    # Volatility
    realized_volatility: float  # Short-term realized volatility
    bid_ask_volatility: float  # Volatility of bid-ask spread

    # Liquidity
    market_depth: float  # Total liquidity within 1% of mid price
    effective_spread: float  # Effective bid-ask spread accounting for depth


class MarketMicrostructureService:
    """
    Service for calculating and providing market microstructure data

    Provides:
    - Real-time microstructure metrics
    - Trade flow analysis
    - Liquidity metrics
    - Price impact estimates
    - Volatility measures
    """

    def __init__(self):
        self.trade_history: dict[str, deque] = {}  # Recent trades per pair
        self.microstructure_cache: dict[str, MarketMicrostructure] = {}
        self.max_trade_history = 10000  # Keep last 10k trades per pair
        self.update_intervals: dict[str, float] = {}  # Update interval per pair
        self.update_tasks: dict[str, asyncio.Task] = {}

    async def record_trade(self, trade: Trade):
        """Record a trade for microstructure analysis"""
        if trade.pair not in self.trade_history:
            self.trade_history[trade.pair] = deque(maxlen=self.max_trade_history)

        self.trade_history[trade.pair].append(trade)

        # Trigger microstructure update
        await self._update_microstructure(trade.pair)

    async def calculate_microstructure(
        self,
        pair: str,
        bids: list[tuple[float, float]],
        asks: list[tuple[float, float]],
        recent_trades: list[Trade] | None = None,
    ) -> MarketMicrostructure:
        """
        Calculate market microstructure metrics

        Args:
            pair: Trading pair
            bids: Bid levels [(price, quantity), ...]
            asks: Ask levels [(price, quantity), ...]
            recent_trades: Recent trades (if None, uses cached history)

        Returns:
            MarketMicrostructure object
        """
        timestamp = time.time_ns()

        # Get recent trades
        if recent_trades is None:
            recent_trades = list(self.trade_history.get(pair, deque()))

        # Calculate order book metrics
        best_bid = bids[0][0] if bids else None
        best_ask = asks[0][0] if asks else None

        if not best_bid or not best_ask:
            raise ValueError(f"Insufficient order book data for {pair}")

        bid_ask_spread = best_ask - best_bid
        mid_price = (best_bid + best_ask) / 2

        # Calculate weighted mid price (volume-weighted)
        bid_volume = sum(qty for _, qty in bids[:10])  # Top 10 levels
        ask_volume = sum(qty for _, qty in asks[:10])
        total_volume = bid_volume + ask_volume

        if total_volume > 0:
            weighted_mid_price = (
                best_bid * ask_volume + best_ask * bid_volume
            ) / total_volume
        else:
            weighted_mid_price = mid_price

        # Volume imbalance
        volume_imbalance = (
            (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0.0
        )

        # Calculate trade flow
        buy_volume = sum(t.quantity for t in recent_trades if t.side == "buy")
        sell_volume = sum(t.quantity for t in recent_trades if t.side == "sell")
        total_trade_volume = buy_volume + sell_volume

        trade_flow_imbalance = (
            (buy_volume - sell_volume) / total_trade_volume
            if total_trade_volume > 0
            else 0.0
        )

        # Estimate price impact (simplified model)
        # In production, use more sophisticated models
        daily_volume_estimate = total_trade_volume * 24 * 60  # Extrapolate to daily
        price_impact_1pct = self._estimate_price_impact(
            bids, asks, daily_volume_estimate * 0.01
        )
        price_impact_5pct = self._estimate_price_impact(
            bids, asks, daily_volume_estimate * 0.05
        )

        # Calculate volatility
        if len(recent_trades) > 10:
            prices = [t.price for t in recent_trades[-100:]]  # Last 100 trades
            realized_volatility = self._calculate_realized_volatility(prices)
        else:
            realized_volatility = 0.0

        # Bid-ask spread volatility
        bid_ask_volatility = (
            abs(bid_ask_spread - (best_ask - best_bid)) / mid_price
            if mid_price > 0
            else 0.0
        )

        # Market depth (liquidity within 1% of mid price)
        depth_range = mid_price * 0.01
        market_depth = sum(
            qty for price, qty in bids if price >= mid_price - depth_range
        ) + sum(qty for price, qty in asks if price <= mid_price + depth_range)

        # Effective spread (accounting for depth)
        effective_spread = self._calculate_effective_spread(bids, asks, mid_price)

        return MarketMicrostructure(
            pair=pair,
            timestamp=timestamp,
            bid_ask_spread=bid_ask_spread,
            mid_price=mid_price,
            weighted_mid_price=weighted_mid_price,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            volume_imbalance=volume_imbalance,
            price_impact_1pct=price_impact_1pct,
            price_impact_5pct=price_impact_5pct,
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            trade_flow_imbalance=trade_flow_imbalance,
            realized_volatility=realized_volatility,
            bid_ask_volatility=bid_ask_volatility,
            market_depth=market_depth,
            effective_spread=effective_spread,
        )

    def _estimate_price_impact(
        self,
        bids: list[tuple[float, float]],
        asks: list[tuple[float, float]],
        target_volume: float,
    ) -> float:
        """
        Estimate price impact for a given trade volume

        Simplified model: walk the order book until target volume is consumed
        """
        if target_volume <= 0:
            return 0.0

        # For buy orders, walk up the ask side
        # For sell orders, walk down the bid side
        # Use average of both for neutral estimate

        # Buy impact (walking up asks)
        buy_impact = 0.0
        remaining_volume = target_volume
        start_price = asks[0][0] if asks else 0.0

        for price, qty in asks:
            if remaining_volume <= 0:
                break
            volume_consumed = min(remaining_volume, qty)
            buy_impact += (price - start_price) * volume_consumed
            remaining_volume -= volume_consumed

        # Sell impact (walking down bids)
        sell_impact = 0.0
        remaining_volume = target_volume
        start_price = bids[0][0] if bids else 0.0

        for price, qty in bids:
            if remaining_volume <= 0:
                break
            volume_consumed = min(remaining_volume, qty)
            sell_impact += (start_price - price) * volume_consumed
            remaining_volume -= volume_consumed

        # Average impact as percentage
        avg_impact = (
            (buy_impact + sell_impact) / (2 * target_volume)
            if target_volume > 0
            else 0.0
        )
        return avg_impact / start_price if start_price > 0 else 0.0

    def _calculate_realized_volatility(self, prices: list[float]) -> float:
        """Calculate realized volatility from price series"""
        if len(prices) < 2:
            return 0.0

        returns = []
        for i in range(1, len(prices)):
            if prices[i - 1] > 0:
                ret = (prices[i] - prices[i - 1]) / prices[i - 1]
                returns.append(ret)

        if not returns:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = variance**0.5

        # Annualize (assuming 1-minute intervals)
        annualized_volatility = volatility * (252 * 24 * 60) ** 0.5

        return annualized_volatility

    def _calculate_effective_spread(
        self,
        bids: list[tuple[float, float]],
        asks: list[tuple[float, float]],
        mid_price: float,
    ) -> float:
        """Calculate effective spread accounting for market depth"""
        if not bids or not asks:
            return 0.0

        best_bid = bids[0][0]
        best_ask = asks[0][0]

        # Weight by depth
        bid_depth = sum(qty for _, qty in bids[:5])
        ask_depth = sum(qty for _, qty in asks[:5])
        total_depth = bid_depth + ask_depth

        if total_depth > 0:
            effective_bid = (
                sum(price * qty for price, qty in bids[:5]) / bid_depth
                if bid_depth > 0
                else best_bid
            )
            effective_ask = (
                sum(price * qty for price, qty in asks[:5]) / ask_depth
                if ask_depth > 0
                else best_ask
            )
            return effective_ask - effective_bid
        else:
            return best_ask - best_bid

    async def _update_microstructure(self, pair: str):
        """Update microstructure cache for a pair"""
        # This would fetch current order book and calculate microstructure
        # For now, it's a placeholder that can be extended
        pass

    async def get_microstructure(self, pair: str) -> MarketMicrostructure | None:
        """Get current microstructure data for a pair"""
        return self.microstructure_cache.get(pair)

    async def start_streaming(self, pair: str, update_interval: float = 0.1):
        """Start streaming microstructure updates"""
        if pair in self.update_tasks and not self.update_tasks[pair].done():
            return

        async def _stream():
            try:
                logger.info(f"Started microstructure streaming for {pair}")
                while True:
                    await asyncio.sleep(update_interval)
                    # Real implementation would fetch order book and calculate here
            except asyncio.CancelledError:
                logger.info(f"Stopped microstructure streaming for {pair}")

        self.update_tasks[pair] = asyncio.create_task(_stream())

    async def stop_streaming(self, pair: str):
        """Stop streaming microstructure updates"""
        if pair in self.update_tasks:
            self.update_tasks[pair].cancel()
            try:
                await self.update_tasks[pair]
            except asyncio.CancelledError:
                pass
            del self.update_tasks[pair]


# Global instance
market_microstructure_service = MarketMicrostructureService()
