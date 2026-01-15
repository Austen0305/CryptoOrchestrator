from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import polars as pl

from server_fastapi.core.bus import bus
from server_fastapi.core.events import MarketAbuseDetected, OrderEvent, TradeEvent

# Configure Logging
logger = logging.getLogger("sentinel")


class SentinelService:
    """
    MiCA Article 16 Compliance: Automated Market Abuse Detection.
    Uses Polars for high-performance windowed aggregations.
    """

    def __init__(self, window_minutes: int = 60):
        self.window_minutes = window_minutes

        # Trade Schema (aligned with TradeEvent + Event base)
        self._trade_schema = {
            "correlation_id": pl.Utf8,
            "causation_id": pl.Utf8,
            "trade_id": pl.Utf8,
            "buyer_id": pl.Utf8,
            "seller_id": pl.Utf8,
            "asset": pl.Utf8,
            "amount": pl.Float64,
            "price": pl.Float64,
            "timestamp": pl.Datetime("us", "UTC"),
        }
        self._trade_buffer = pl.DataFrame(schema=self._trade_schema)

        # Order Schema (aligned with OrderEvent + Event base)
        self._order_schema = {
            "correlation_id": pl.Utf8,
            "causation_id": pl.Utf8,
            "order_id": pl.Utf8,
            "user_id": pl.Utf8,
            "asset": pl.Utf8,
            "side": pl.Utf8,
            "amount": pl.Float64,
            "price": pl.Float64,
            "status": pl.Utf8,
            "timestamp": pl.Datetime("us", "UTC"),
        }
        self._order_buffer = pl.DataFrame(schema=self._order_schema)

    async def ingest_trade_async(self, event: TradeEvent) -> None:
        """Async wrapper for trade ingestion."""
        alert = self.ingest_trade(event)
        if alert:
            logger.critical(f"MARKET ABUSE DETECTED: {alert.model_dump_json()}")
            await bus.publish(alert)

    async def ingest_order_async(self, event: OrderEvent) -> None:
        """Async wrapper for order ingestion."""
        alert = self.ingest_order(event)
        if alert:
            logger.critical(f"MARKET ABUSE DETECTED: {alert.model_dump_json()}")
            await bus.publish(alert)

    def detect_sandwich(self, victim_trade: TradeEvent) -> MarketAbuseDetected | None:
        """
        Detects Sandwich Attacks (MEV) by checking if the trade completes a pattern.
        """
        return self._detect_sandwich_pattern(victim_trade)

    def _detect_sandwich_pattern(
        self, current_trade: TradeEvent
    ) -> MarketAbuseDetected | None:
        """
        Detects if the current trade completes a sandwich attack.
        Scenario: Current Trade is the "Back-run" (Attacker selling).
        """
        attacker_id = current_trade.seller_id
        asset = current_trade.asset

        # 1. Get recent trades for this asset
        df = self._trade_buffer.filter(pl.col("asset") == asset)
        if df.height < 3:
            return None

        # 2. Look for a prior BUY by the same attacker (Front-run)
        front_runs = df.filter(
            (pl.col("buyer_id") == attacker_id)
            & (pl.col("timestamp") < current_trade.timestamp)
            & (
                pl.col("timestamp") > current_trade.timestamp - timedelta(seconds=10)
            )  # Tight window
        ).sort("timestamp", descending=True)

        if front_runs.height == 0:
            return None

        last_front_run = front_runs.row(0, named=True)
        front_run_time = last_front_run["timestamp"]

        # 3. Look for a VICTIM buy in between
        victim_trades = df.filter(
            (pl.col("timestamp") > front_run_time)
            & (pl.col("timestamp") < current_trade.timestamp)
            & (pl.col("buyer_id") != attacker_id)
        )

        if victim_trades.height > 0:
            return MarketAbuseDetected(
                abuse_type="MARKET_MANIPULATION_SANDWICH",
                severity="CRITICAL",
                details=(
                    f"Sandwich Attack Detected. Attacker {attacker_id} "
                    f"front-ran {victim_trades.height} trades."
                ),
                timestamp=datetime.now(UTC),
            )

        return None

    def ingest_trade(self, trade: TradeEvent) -> MarketAbuseDetected | None:
        """Ingests a trade and runs immediate anomaly detection."""
        # 1. Add to buffer
        data = trade.model_dump(exclude={"event_name"})
        # Only keep keys that exist in our schema to avoid ShapeError
        filtered_data = {k: v for k, v in data.items() if k in self._trade_schema}

        row = pl.DataFrame([filtered_data], schema=self._trade_schema)

        self._trade_buffer = pl.concat([self._trade_buffer, row], how="vertical")

        # 2. Prune old data
        cutoff = datetime.now(UTC) - timedelta(minutes=self.window_minutes)
        self._trade_buffer = self._trade_buffer.filter(pl.col("timestamp") > cutoff)

        # 3. Detect Anomalies
        wash = self._detect_wash_trading(trade)
        if wash:
            return wash

        return self._detect_sandwich_pattern(trade)

    def ingest_order(self, order: OrderEvent) -> MarketAbuseDetected | None:
        """Ingests an order event and checks for spoofing."""
        # 1. Add to buffer
        data = order.model_dump(exclude={"event_name", "event_id"})
        # Only keep keys that exist in our schema to avoid ShapeError
        filtered_data = {k: v for k, v in data.items() if k in self._order_schema}

        row = pl.DataFrame([filtered_data], schema=self._order_schema)

        self._order_buffer = pl.concat([self._order_buffer, row], how="vertical")

        # 2. Prune old orders
        cutoff = datetime.now(UTC) - timedelta(minutes=self.window_minutes)
        self._order_buffer = self._order_buffer.filter(pl.col("timestamp") > cutoff)

        # 3. Detect Spoofing if CANCELED
        if order.status == "CANCELED":
            return self.detect_spoofing(order)

        return None

    def _detect_wash_trading(
        self, current_trade: TradeEvent
    ) -> MarketAbuseDetected | None:
        """
        Detects Circular Trading patterns: A -> B -> A within window.
        """
        df = self._trade_buffer.filter(pl.col("asset") == current_trade.asset)

        reversal_trades = df.filter(
            (pl.col("buyer_id") == current_trade.seller_id)
            & (pl.col("seller_id") == current_trade.buyer_id)
        )

        if reversal_trades.height > 0:
            return MarketAbuseDetected(
                abuse_type="WASH_TRADING_CIRCULAR",
                severity="HIGH",
                details=(
                    f"Circular trade detected. {current_trade.buyer_id} <-> "
                    f"{current_trade.seller_id} traded same asset within window."
                ),
                timestamp=datetime.now(UTC),
            )

        return None

    def detect_layering(
        self, order_book_snapshot: pl.DataFrame
    ) -> MarketAbuseDetected | None:
        """
        Detects Layering/Spoofing by checking order book imbalance.
        """
        required_cols = {"amount", "side"}
        if not required_cols.issubset(order_book_snapshot.columns):
            return None

        try:
            total_vol = order_book_snapshot.group_by("side").agg(
                pl.col("amount").sum().alias("total_amount")
            )

            buy_vol_row = total_vol.filter(pl.col("side") == "buy")
            sell_vol_row = total_vol.filter(pl.col("side") == "sell")

            buy_vol = buy_vol_row["total_amount"][0] if buy_vol_row.height > 0 else 0.0
            sell_vol = (
                sell_vol_row["total_amount"][0] if sell_vol_row.height > 0 else 0.0
            )

            if sell_vol == 0 or buy_vol == 0:
                return None

            ratio = buy_vol / sell_vol

            if ratio > 10.0:
                return MarketAbuseDetected(
                    abuse_type="MARKET_MANIPULATION_LAYERING",
                    severity="MEDIUM",
                    details=(
                        f"Severe Order Book Imbalance (Buy Side). Ratio: {ratio:.2f}"
                    ),
                    timestamp=datetime.now(UTC),
                )
            elif ratio < 0.1:
                return MarketAbuseDetected(
                    abuse_type="MARKET_MANIPULATION_LAYERING",
                    severity="MEDIUM",
                    details=(
                        f"Severe Order Book Imbalance (Sell Side). Ratio: {ratio:.2f}"
                    ),
                    timestamp=datetime.now(UTC),
                )

        except Exception as e:
            logger.error(f"Error in detect_layering: {e}")
            return None

        return None

    def detect_spoofing(self, canceled_order: OrderEvent) -> MarketAbuseDetected | None:
        """
        Detects Spoofing: Large orders cancelled shortly after placement.
        """
        try:
            original_order = self._order_buffer.filter(
                (pl.col("order_id") == canceled_order.order_id)
                & (pl.col("status") == "NEW")
            )

            if original_order.height == 0:
                return None

            created_at = original_order["timestamp"][0]
            canceled_at = canceled_order.timestamp

            lifetime_seconds = (canceled_at - created_at).total_seconds()

            lifetime_seconds = (canceled_at - created_at).total_seconds()

            if lifetime_seconds < 5.0 and canceled_order.amount > 10.0:
                return MarketAbuseDetected(
                    abuse_type="MARKET_MANIPULATION_SPOOFING",
                    severity="HIGH",
                    details=(
                        f"Potential Spoofing: Large order {canceled_order.amount} "
                        f"units cancelled in {lifetime_seconds:.2f}s"
                    ),
                    timestamp=datetime.now(UTC),
                )

        except Exception as e:
            logger.error(f"Error in detect_spoofing: {e}")
            return None

        return None

    def detect_volume_anomaly(
        self, asset: str, current_volume: float
    ) -> MarketAbuseDetected | None:
        """
        Circuit Breaker: Detects 5σ volume anomalies that may indicate
        coordinated manipulation or market stress.

        Triggers automatic trading pause recommendation.
        """
        df = self._trade_buffer.filter(pl.col("asset") == asset)

        if df.height < 30:  # Need sufficient history
            return None

        try:
            stats = df.select(
                [
                    pl.col("amount").mean().alias("mean"),
                    pl.col("amount").std().alias("std"),
                ]
            ).row(0, named=True)

            mean = stats["mean"]
            std = stats["std"]

            if std == 0:
                return None

            z_score = (current_volume - mean) / std

            if abs(z_score) > 5.0:
                return MarketAbuseDetected(
                    abuse_type="CIRCUIT_BREAKER_VOLUME_ANOMALY",
                    severity="CRITICAL",
                    details=(
                        f"5σ Volume Anomaly for {asset}. "
                        f"Volume: {current_volume:.2f}, Mean: {mean:.2f}, "
                        f"Z-Score: {z_score:.2f}. "
                        f"RECOMMENDATION: Pause trading for 10 minutes."
                    ),
                    timestamp=datetime.now(UTC),
                )

        except Exception as e:
            logger.error(f"Error in detect_volume_anomaly: {e}")
            return None

        return None

    def detect_cross_account_wash_trading(
        self, account_ids: list[str], window_minutes: int = 30
    ) -> MarketAbuseDetected | None:
        """
        Advanced wash trading detection: finds coordinated trading
        across multiple accounts that may be controlled by the same entity.

        MiCA Article 16 requires detection of trades that create
        a misleading appearance of market activity.
        """
        if len(account_ids) < 2:
            return None

        cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)

        try:
            # Find trades where accounts are trading with each other
            set(account_ids)

            suspect_trades = self._trade_buffer.filter(
                (pl.col("timestamp") > cutoff)
                & (pl.col("buyer_id").is_in(account_ids))
                & (pl.col("seller_id").is_in(account_ids))
            )

            if suspect_trades.height > 5:  # Threshold for suspicion
                total_volume = suspect_trades.select(pl.col("amount").sum())[0, 0]

                return MarketAbuseDetected(
                    abuse_type="WASH_TRADING_CROSS_ACCOUNT",
                    severity="HIGH",
                    details=(
                        f"Cross-account wash trading suspected. "
                        f"{len(account_ids)} linked accounts executed "
                        f"{suspect_trades.height} trades totaling "
                        f"{total_volume:.2f} units in {window_minutes} minutes."
                    ),
                    timestamp=datetime.now(UTC),
                )

        except Exception as e:
            logger.error(f"Error in cross-account wash detection: {e}")
            return None

        return None

    def get_health_metrics(self) -> dict:
        """
        Returns health metrics for monitoring and alerting.
        """
        now = datetime.now(UTC)
        recent_cutoff = now - timedelta(minutes=5)

        return {
            "trade_buffer_size": self._trade_buffer.height,
            "order_buffer_size": self._order_buffer.height,
            "window_minutes": self.window_minutes,
            "recent_trades": self._trade_buffer.filter(
                pl.col("timestamp") > recent_cutoff
            ).height,
            "recent_orders": self._order_buffer.filter(
                pl.col("timestamp") > recent_cutoff
            ).height,
            "timestamp": now.isoformat(),
        }
