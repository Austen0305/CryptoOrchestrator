import logging
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import polars as pl
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PerformanceMetrics(BaseModel):
    botId: str
    period: str
    totalReturn: float
    sharpeRatio: float
    maxDrawdown: float
    winRate: float
    averageWin: float
    averageLoss: float
    profitFactor: float
    totalTrades: int


@dataclass
class Trade:
    timestamp: int
    side: str
    total: float
    totalWithFee: float = 0.0
    fee: float = 0.0
    pair: str = ""


@dataclass
class BotConfig:
    id: str
    name: str


class AnalyticsEngine:
    def __init__(self, storage=None):
        self.storage = storage

    async def analyze(self, params: dict[str, Any], db_session=None) -> dict[str, Any]:
        """Analyze data based on type and parameters"""
        analysis_type = params.get("type")
        user_id = params.get("user_id")

        if analysis_type == "summary":
            return await self._analyze_summary(user_id, db_session)
        elif analysis_type == "performance":
            bot_id = params.get("bot_id")
            period = params.get("period", "30d")
            return await self._analyze_performance(user_id, bot_id, period, db_session)
        elif analysis_type == "pnl_chart":
            bot_id = params.get("bot_id")
            period = params.get("period", "30d")
            return await self._analyze_pnl_chart(user_id, bot_id, period, db_session)
        elif analysis_type == "dashboard":
            return await self._analyze_dashboard(user_id, db_session)
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")

    async def _analyze_dashboard(self, user_id: int, db_session=None) -> dict[str, Any]:
        """Analyze dashboard data for summary view using real database data"""
        try:
            from sqlalchemy import func, select

            from ..models.bot import Bot
            from ..models.trade import Trade

            if not db_session:
                from ..database import get_db_context

                async with get_db_context() as session:
                    return await self._analyze_dashboard(user_id, session)

            # Get real bot count
            bot_count_query = select(func.count(Bot.id)).where(Bot.user_id == user_id)
            bot_result = await db_session.execute(bot_count_query)
            total_bots = bot_result.scalar() or 0

            active_bots_query = select(func.count(Bot.id)).where(
                Bot.user_id == user_id, Bot.active
            )
            active_result = await db_session.execute(active_bots_query)
            active_bots = active_result.scalar() or 0

            # Get real trade statistics
            trades_query = select(Trade).where(Trade.user_id == user_id)
            trades_result = await db_session.execute(trades_query)
            all_trades = list(trades_result.scalars().all())

            # Convert to Polars DataFrame for aggregation
            trade_dicts = []
            for t in all_trades:
                trade_dicts.append(
                    {
                        "bot_id": t.bot_id,
                        "pnl": t.pnl or 0.0,
                        "executed_at": t.executed_at,
                        "side": t.side,
                    }
                )

            if not trade_dicts:
                df = pl.DataFrame(
                    {"bot_id": [], "pnl": [], "executed_at": [], "side": []}
                )
            else:
                df = pl.DataFrame(trade_dicts)

            total_trades = df.height
            total_pnl = df["pnl"].sum() if total_trades > 0 else 0.0

            # Win rate
            winning_count = df.filter(pl.col("pnl") > 0).height
            win_rate = winning_count / total_trades if total_trades > 0 else 0.0

            # Bot Performance Metrics
            bot_metrics = []
            bots_query = select(Bot).where(Bot.user_id == user_id)
            bots_result = await db_session.execute(bots_query)
            bots = list(bots_result.scalars().all())

            # Use aggregation to speed up bot stats
            if total_trades > 0:
                bot_stats = df.group_by("bot_id").agg(
                    [
                        pl.count("pnl").alias("total_trades"),
                        pl.col("pnl").sum().alias("total_pnl"),
                        pl.col("pnl")
                        .filter(pl.col("pnl") > 0)
                        .count()
                        .alias("winning_trades"),
                        pl.col("pnl")
                        .filter(pl.col("pnl") < 0)
                        .count()
                        .alias("losing_trades"),
                    ]
                )
            else:
                bot_stats = pl.DataFrame()

            best_bot_id = None
            worst_bot_id = None
            best_pnl = float("-inf")
            worst_pnl = float("inf")

            for bot in bots:
                if bot_stats.height > 0:
                    stats = bot_stats.filter(pl.col("bot_id") == bot.id)
                else:
                    stats = pl.DataFrame()

                if stats.height == 0:
                    continue

                row = stats.row(0, named=True)
                bot_pnl = row["total_pnl"]
                b_total = row["total_trades"]
                b_wins = row["winning_trades"]
                b_losers = row["losing_trades"]

                if bot_pnl > best_pnl:
                    best_pnl = bot_pnl
                    best_bot_id = bot.id
                if bot_pnl < worst_pnl:
                    worst_pnl = bot_pnl
                    worst_bot_id = bot.id

                bot_win_rate = b_wins / b_total if b_total > 0 else 0.0

                # Max Drawdown calculation requires sequential scan, do it per bot
                # Filter df for this bot
                bot_df = df.filter(pl.col("bot_id") == bot.id).sort("executed_at")
                pnl_series = bot_df["pnl"]

                # Calculate running cumulative sum
                cum_pnl = pnl_series.cum_sum()
                # Calculate running max
                running_max = cum_pnl.cum_max()

                # Using simple peak - current for absolute drawdown
                drawdowns = running_max - cum_pnl
                max_dd = drawdowns.max() if drawdowns.len() > 0 else 0.0

                bot_metrics.append(
                    {
                        "bot_id": bot.id,
                        "bot_name": bot.name,
                        "total_trades": b_total,
                        "winning_trades": b_wins,
                        "losing_trades": b_losers,
                        "win_rate": bot_win_rate,
                        "total_pnl": bot_pnl,
                        "max_drawdown": max_dd,
                        "sharpe_ratio": 0.0,
                        "current_balance": 0.0,
                    }
                )

            dashboard_data = {
                "summary": {
                    "total_bots": total_bots,
                    "active_bots": active_bots,
                    "total_trades": total_trades,
                    "total_pnl": total_pnl,
                    "win_rate": win_rate,
                    "best_performing_bot": best_bot_id,
                    "worst_performing_bot": worst_bot_id,
                },
                "details": {"metrics": bot_metrics, "chart_data": []},
            }

            return dashboard_data

        except Exception as e:
            logger.error(
                f"Error analyzing dashboard for user {user_id}: {e}", exc_info=True
            )
            # In production, return empty data
            from ..config.settings import get_settings

            settings = get_settings()
            if settings.production_mode or settings.is_production:
                return {
                    "summary": {
                        "total_bots": 0,
                        "active_bots": 0,
                        "total_trades": 0,
                        "total_pnl": 0.0,
                        "win_rate": 0.0,
                        "best_performing_bot": None,
                        "worst_performing_bot": None,
                    },
                    "details": {"metrics": [], "chart_data": []},
                }
            else:
                return {
                    "summary": {
                        "total_bots": 0,
                        "active_bots": 0,
                        "total_trades": 0,
                        "total_pnl": 0.0,
                        "win_rate": 0.0,
                        "best_performing_bot": None,
                        "worst_performing_bot": None,
                    },
                    "details": {"metrics": [], "chart_data": []},
                }

    async def calculate_performance_metrics(
        self, bot_id: str, period: str = "all", db_session=None
    ) -> PerformanceMetrics:
        """Calculate performance metrics from real database data using Polars"""
        trades = await self._get_trades(bot_id, db_session=db_session)
        bot = await self._get_bot(bot_id, db_session=db_session)

        # Convert to DF
        if not trades:
            df = pl.DataFrame([])
        else:
            # dataclasses.asdict used for conversion
            df = pl.DataFrame([asdict(t) for t in trades])
            # Ensure types
            df = df.with_columns(
                [
                    pl.col("timestamp").cast(pl.Int64),
                    pl.col("total").cast(pl.Float64),
                    pl.col("totalWithFee").cast(pl.Float64),
                    pl.col("fee").cast(pl.Float64),
                ]
            )

        if not bot or df.height == 0:
            return PerformanceMetrics(
                botId=bot_id,
                period=period,
                totalReturn=0,
                sharpeRatio=0,
                maxDrawdown=0,
                winRate=0,
                averageWin=0,
                averageLoss=0,
                profitFactor=0,
                totalTrades=0,
            )

        # Filter trades by period
        filtered_df = self._filter_trades_by_period_pl(df, period)

        if filtered_df.height == 0:
            return PerformanceMetrics(
                botId=bot_id,
                period=period,
                totalReturn=0,
                sharpeRatio=0,
                maxDrawdown=0,
                winRate=0,
                averageWin=0,
                averageLoss=0,
                profitFactor=0,
                totalTrades=0,
            )

        # Calculate metrics using Polars DF
        total_return = self._calculate_total_return_pl(filtered_df)
        sharpe_ratio = self._calculate_sharpe_ratio_pl(filtered_df)
        max_drawdown = self._calculate_max_drawdown_pl(filtered_df)
        win_rate = self._calculate_win_rate_pl(filtered_df)
        average_win = self._calculate_average_win_pl(filtered_df)
        average_loss = self._calculate_average_loss_pl(filtered_df)
        profit_factor = self._calculate_profit_factor_pl(filtered_df)

        metrics = PerformanceMetrics(
            botId=bot_id,
            period=period,
            totalReturn=total_return,
            sharpeRatio=sharpe_ratio,
            maxDrawdown=max_drawdown,
            winRate=win_rate,
            averageWin=average_win,
            averageLoss=average_loss,
            profitFactor=profit_factor,
            totalTrades=filtered_df.height,
        )

        # Save to storage (mock)
        await self._save_performance_metrics(metrics)

        return metrics

    def _filter_trades_by_period_pl(
        self, df: pl.DataFrame, period: str
    ) -> pl.DataFrame:
        now = datetime.now().timestamp() * 1000
        start_time = 0

        if period == "1d":
            start_time = now - 24 * 60 * 60 * 1000
        elif period == "7d":
            start_time = now - 7 * 24 * 60 * 60 * 1000
        elif period == "30d":
            start_time = now - 30 * 24 * 60 * 60 * 1000
        elif period == "90d":
            start_time = now - 90 * 24 * 60 * 60 * 1000
        elif period == "1y":
            start_time = now - 365 * 24 * 60 * 60 * 1000
        else:
            return df  # 'all' period

        return df.filter(pl.col("timestamp") >= start_time)

    def _calculate_total_return_pl(self, df: pl.DataFrame) -> float:
        initial_investment = 100000.0

        # PnL = (Buy: -totalWithFee) + (Sell: total - fee)
        # Using when/then
        pnl_expr = (
            pl.when(pl.col("side") == "buy")
            .then(-pl.col("totalWithFee"))
            .otherwise(pl.col("total") - pl.col("fee"))
        )

        total_pnl = df.select(pnl_expr.sum()).item() or 0.0

        # Assumption: current_balance = initial + total_pnl
        return total_pnl / initial_investment

    def _calculate_sharpe_ratio_pl(self, df: pl.DataFrame) -> float:
        if df.height < 2:
            return 0.0

        # Calculate daily returns
        # Group by day: floor(timestamp / (24*60*60*1000))
        day_expr = (pl.col("timestamp") // (24 * 60 * 60 * 1000)).alias("day")
        pnl_expr = (
            pl.when(pl.col("side") == "buy")
            .then(-pl.col("totalWithFee"))
            .otherwise(pl.col("total") - pl.col("fee"))
        )

        daily_df = (
            df.with_columns([day_expr, pnl_expr.alias("pnl")])
            .group_by("day")
            .agg(pl.col("pnl").sum())
        )

        if daily_df.height == 0:
            return 0.0

        initial_balance = 100000.0
        daily_returns = daily_df.select((pl.col("pnl") / initial_balance).alias("ret"))

        avg_ret = daily_returns["ret"].mean()
        std_dev = daily_returns["ret"].std()

        risk_free_rate = 0.02 / 365

        if std_dev == 0 or std_dev is None:
            return 0.0

        return (avg_ret - risk_free_rate) / std_dev * math.sqrt(365)

    def _calculate_max_drawdown_pl(self, df: pl.DataFrame) -> float:
        if df.height == 0:
            return 0.0

        # Equity curve
        pnl_expr = (
            pl.when(pl.col("side") == "buy")
            .then(-pl.col("totalWithFee"))
            .otherwise(pl.col("total") - pl.col("fee"))
        )

        sorted_df = df.sort("timestamp")
        equity = sorted_df.select(
            (pl.lit(100000.0) + pnl_expr.cum_sum()).alias("equity")
        )

        if equity.height == 0:
            return 0.0

        # Max Drawdown = max((RunningMax - Equity) / RunningMax)
        running_max = equity["equity"].cum_max()
        drawdown = (running_max - equity["equity"]) / running_max

        return drawdown.max() or 0.0

    def _calculate_win_rate_pl(self, df: pl.DataFrame) -> float:
        total_trades = df.height
        if total_trades == 0:
            return 0.0

        wins = df.filter((pl.col("side") == "sell") & (pl.col("total") > 0)).height
        return wins / total_trades

    def _calculate_average_win_pl(self, df: pl.DataFrame) -> float:
        wins_df = df.filter((pl.col("side") == "sell") & (pl.col("total") > 0))
        if wins_df.height == 0:
            return 0.0

        return wins_df["total"].mean()

    def _calculate_average_loss_pl(self, df: pl.DataFrame) -> float:
        losses_df = df.filter((pl.col("side") == "sell") & (pl.col("total") < 0))
        if losses_df.height == 0:
            return 0.0

        return losses_df["total"].abs().mean()

    def _calculate_profit_factor_pl(self, df: pl.DataFrame) -> float:
        gross_profit = df.filter((pl.col("side") == "sell") & (pl.col("total") > 0))[
            "total"
        ].sum()
        gross_loss = df.filter((pl.col("side") == "sell") & (pl.col("total") < 0))[
            "total"
        ].sum()

        gross_loss = abs(gross_loss)

        if gross_loss > 0:
            return gross_profit / gross_loss
        elif gross_profit > 0:
            return float("inf")
        else:
            return 0.0

    async def get_performance_comparison(
        self, bot_ids: list[str], period: str = "30d"
    ) -> dict[str, PerformanceMetrics]:
        comparisons = {}

        for bot_id in bot_ids:
            comparisons[bot_id] = await self.calculate_performance_metrics(
                bot_id, period
            )

        return comparisons

    async def generate_performance_report(
        self, bot_id: str, period: str = "30d"
    ) -> str:
        metrics = await self.calculate_performance_metrics(bot_id, period)
        bot = await self._get_bot(bot_id)

        if not bot:
            return "Bot not found"
        # Build a human-readable performance report
        report = f"""
Performance Report for {bot.name} ({period})

Total Return: {(metrics.totalReturn * 100):.2f}%
Sharpe Ratio: {metrics.sharpeRatio:.2f}
Max Drawdown: {(metrics.maxDrawdown * 100):.2f}%
Win Rate: {(metrics.winRate * 100):.2f}%
Average Win: ${metrics.averageWin:.2f}
Average Loss: ${metrics.averageLoss:.2f}
Profit Factor: {metrics.profitFactor:.2f}
Total Trades: {metrics.totalTrades}
""".strip()

        return report

    # Database methods - use real database queries
    async def _get_trades(
        self, bot_id: str, user_id: int = None, db_session=None
    ) -> list[Trade]:
        """Get trades from database"""
        try:
            from sqlalchemy import select

            from ..models.trade import Trade as TradeModel

            if not db_session:
                from ..database import get_db_context

                async with get_db_context() as session:
                    return await self._get_trades(bot_id, user_id, session)

            query = select(TradeModel).where(TradeModel.bot_id == bot_id)
            if user_id:
                query = query.where(TradeModel.user_id == user_id)

            result = await db_session.execute(query)
            db_trades = list(result.scalars().all())

            # Convert to Trade dataclass
            trades = []
            for db_trade in db_trades:
                timestamp_ms = (
                    int(db_trade.executed_at.timestamp() * 1000)
                    if db_trade.executed_at
                    else int(db_trade.timestamp.timestamp() * 1000)
                )
                trades.append(
                    Trade(
                        timestamp=timestamp_ms,
                        side=db_trade.side,
                        total=db_trade.cost,
                        totalWithFee=db_trade.cost + db_trade.fee,
                        fee=db_trade.fee,
                        pair=db_trade.pair or db_trade.symbol,
                    )
                )

            return trades
        except Exception as e:
            logger.error(f"Error getting trades for bot {bot_id}: {e}", exc_info=True)
            return []

    async def _get_bot(self, bot_id: str, db_session=None) -> BotConfig | None:
        """Get bot from database"""
        try:
            from sqlalchemy import select

            from ..models.bot import Bot

            if not db_session:
                from ..database import get_db_context

                async with get_db_context() as session:
                    return await self._get_bot(bot_id, session)

            query = select(Bot).where(Bot.id == bot_id)
            result = await db_session.execute(query)
            bot = result.scalar_one_or_none()

            if bot:
                return BotConfig(id=bot.id, name=bot.name)
            return None
        except Exception as e:
            logger.error(f"Error getting bot {bot_id}: {e}", exc_info=True)
            return None

    async def _save_performance_metrics(self, metrics: PerformanceMetrics):
        """Save performance metrics (optional - can be stored in bot.performance_data)"""
        # Could store in bot.performance_data JSON field
        pass

    async def _analyze_summary(self, user_id: int, db_session=None) -> dict[str, Any]:
        """Analyze summary data"""
        # Use dashboard analysis for summary
        dashboard = await self._analyze_dashboard(user_id, db_session)
        return dashboard.get("summary", {})

    async def _analyze_performance(
        self, user_id: int, bot_id: str, period: str, db_session=None
    ) -> dict[str, Any]:
        """Analyze performance for a specific bot"""
        metrics = await self.calculate_performance_metrics(bot_id, period, db_session)
        return {
            "bot_id": bot_id,
            "period": period,
            "metrics": metrics.dict() if hasattr(metrics, "dict") else metrics,
        }

    async def _analyze_pnl_chart(
        self, user_id: int, bot_id: str | None, period: str, db_session=None
    ) -> dict[str, Any]:
        """Analyze PnL chart data"""
        try:
            from datetime import datetime, timedelta

            from sqlalchemy import select

            from ..models.trade import Trade

            if not db_session:
                from ..database import get_db_context

                async with get_db_context() as session:
                    return await self._analyze_pnl_chart(
                        user_id, bot_id, period, session
                    )

            # Calculate date range
            end_date = datetime.now()
            if period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)

            # Query trades
            query = select(Trade).where(
                Trade.user_id == user_id, Trade.executed_at >= start_date
            )
            if bot_id:
                query = query.where(Trade.bot_id == bot_id)

            result = await db_session.execute(query)
            trades = list(result.scalars().all())

            if not trades:
                return {
                    "chart_data": [],
                    "period": period,
                    "total_pnl": 0.0,
                }

            # Use Polars for aggregation
            trade_dicts = []
            for t in trades:
                date_key = (
                    t.executed_at.date().isoformat()
                    if t.executed_at
                    else datetime.fromtimestamp(t.timestamp).date().isoformat()
                )
                trade_dicts.append({"date": date_key, "pnl": t.pnl or 0.0})

            df = pl.DataFrame(trade_dicts)

            # Group by date
            daily_stats = df.group_by("date").agg(pl.col("pnl").sum()).sort("date")

            # Cumulative Sum
            daily_stats = daily_stats.with_columns(
                pl.col("pnl").cum_sum().alias("cumulative_pnl")
            )

            chart_data = daily_stats.select(
                ["date", "pnl", "cumulative_pnl"]
            ).to_dicts()
            total_pnl = daily_stats["pnl"].sum()

            return {
                "chart_data": chart_data,
                "period": period,
                "total_pnl": total_pnl,
            }
        except Exception as e:
            logger.error(f"Error analyzing PnL chart: {e}", exc_info=True)
            return {"chart_data": [], "period": period, "total_pnl": 0.0}


# Create singleton instance
analytics_engine = AnalyticsEngine()
