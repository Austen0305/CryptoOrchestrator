"""
DEX Trading Metrics Service
Tracks DEX trading volume, fees, aggregator performance, and error rates
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ...models.dex_trade import DEXTrade
from ...models.trading_fee import TradingFee
from ...config.settings import get_settings

logger = logging.getLogger(__name__)


class DEXMetricsService:
    """Service for collecting and aggregating DEX trading metrics"""

    def __init__(self):
        self.settings = get_settings()

    async def get_trade_volume(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        chain_id: Optional[int] = None,
        aggregator: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get DEX trade volume metrics

        Args:
            db: Database session
            start_date: Start date for metrics (default: 30 days ago)
            end_date: End date for metrics (default: now)
            chain_id: Optional chain ID filter
            aggregator: Optional aggregator filter

        Returns:
            Dictionary with volume metrics
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            stmt = (
                select(
                    func.sum(DEXTrade.sell_amount_decimal).label("total_volume"),
                    func.count(DEXTrade.id).label("trade_count"),
                    func.avg(DEXTrade.sell_amount_decimal).label("avg_trade_size"),
                )
                .where(DEXTrade.executed_at >= start_date)
                .where(DEXTrade.executed_at <= end_date)
                .where(DEXTrade.status == "completed")
            )

            if chain_id:
                stmt = stmt.where(DEXTrade.chain_id == chain_id)
            if aggregator:
                stmt = stmt.where(DEXTrade.aggregator == aggregator)

            result = await db.execute(stmt)
            row = result.first()

            return {
                "total_volume": float(row.total_volume or 0),
                "trade_count": int(row.trade_count or 0),
                "avg_trade_size": float(row.avg_trade_size or 0),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting trade volume: {e}", exc_info=True)
            return {
                "total_volume": 0.0,
                "trade_count": 0,
                "avg_trade_size": 0.0,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            }

    async def get_fee_collection(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get platform fee collection metrics

        Args:
            db: Database session
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            Dictionary with fee metrics
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            stmt = (
                select(
                    func.sum(TradingFee.fee_amount).label("total_fees"),
                    func.count(TradingFee.id).label("fee_count"),
                    func.avg(TradingFee.fee_amount).label("avg_fee"),
                )
                .where(TradingFee.collected_at >= start_date)
                .where(TradingFee.collected_at <= end_date)
                .where(TradingFee.trade_type == "dex")
                .where(TradingFee.status == "collected")
            )

            result = await db.execute(stmt)
            row = result.first()

            return {
                "total_fees": float(row.total_fees or 0),
                "fee_count": int(row.fee_count or 0),
                "avg_fee": float(row.avg_fee or 0),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting fee collection: {e}", exc_info=True)
            return {
                "total_fees": 0.0,
                "fee_count": 0,
                "avg_fee": 0.0,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            }

    async def get_aggregator_performance(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics for each aggregator

        Args:
            db: Database session
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            List of aggregator performance dictionaries
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            stmt = (
                select(
                    DEXTrade.aggregator,
                    func.count(DEXTrade.id).label("trade_count"),
                    func.sum(DEXTrade.sell_amount_decimal).label("total_volume"),
                    func.avg(DEXTrade.sell_amount_decimal).label("avg_trade_size"),
                    func.sum(
                        func.case(
                            (DEXTrade.success.is_(True), 1),
                            else_=0,
                        )
                    ).label("successful_trades"),
                    func.sum(
                        func.case(
                            (DEXTrade.success.is_(False), 1),
                            else_=0,
                        )
                    ).label("failed_trades"),
                )
                .where(DEXTrade.executed_at >= start_date)
                .where(DEXTrade.executed_at <= end_date)
                .group_by(DEXTrade.aggregator)
            )

            result = await db.execute(stmt)
            rows = result.all()

            aggregators = []
            for row in rows:
                total_trades = int(row.trade_count or 0)
                successful = int(row.successful_trades or 0)
                failed = int(row.failed_trades or 0)
                success_rate = (
                    (successful / total_trades * 100) if total_trades > 0 else 0
                )

                aggregators.append(
                    {
                        "aggregator": row.aggregator,
                        "trade_count": total_trades,
                        "total_volume": float(row.total_volume or 0),
                        "avg_trade_size": float(row.avg_trade_size or 0),
                        "successful_trades": successful,
                        "failed_trades": failed,
                        "success_rate": round(success_rate, 2),
                    }
                )

            return aggregators

        except Exception as e:
            logger.error(f"Error getting aggregator performance: {e}", exc_info=True)
            return []

    async def get_error_rates(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get error rate metrics

        Args:
            db: Database session
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            Dictionary with error rate metrics
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            # Total trades
            total_stmt = (
                select(func.count(DEXTrade.id))
                .where(DEXTrade.executed_at >= start_date)
                .where(DEXTrade.executed_at <= end_date)
            )
            total_result = await db.execute(total_stmt)
            total_trades = total_result.scalar() or 0

            # Failed trades
            failed_stmt = (
                select(func.count(DEXTrade.id))
                .where(DEXTrade.executed_at >= start_date)
                .where(DEXTrade.executed_at <= end_date)
                .where(DEXTrade.success.is_(False))
            )
            failed_result = await db.execute(failed_stmt)
            failed_trades = failed_result.scalar() or 0

            # Trades with errors
            error_stmt = (
                select(func.count(DEXTrade.id))
                .where(DEXTrade.executed_at >= start_date)
                .where(DEXTrade.executed_at <= end_date)
                .where(DEXTrade.error_message.isnot(None))
            )
            error_result = await db.execute(error_stmt)
            error_trades = error_result.scalar() or 0

            error_rate = (failed_trades / total_trades * 100) if total_trades > 0 else 0

            return {
                "total_trades": total_trades,
                "failed_trades": failed_trades,
                "error_trades": error_trades,
                "error_rate": round(error_rate, 2),
                "success_rate": round(100 - error_rate, 2),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting error rates: {e}", exc_info=True)
            return {
                "total_trades": 0,
                "failed_trades": 0,
                "error_trades": 0,
                "error_rate": 0.0,
                "success_rate": 0.0,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            }

    async def get_chain_volume(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get volume metrics by chain

        Args:
            db: Database session
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            List of chain volume dictionaries
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            stmt = (
                select(
                    DEXTrade.chain_id,
                    func.count(DEXTrade.id).label("trade_count"),
                    func.sum(DEXTrade.sell_amount_decimal).label("total_volume"),
                )
                .where(DEXTrade.executed_at >= start_date)
                .where(DEXTrade.executed_at <= end_date)
                .where(DEXTrade.status == "completed")
                .group_by(DEXTrade.chain_id)
            )

            result = await db.execute(stmt)
            rows = result.all()

            chains = []
            for row in rows:
                chains.append(
                    {
                        "chain_id": row.chain_id,
                        "trade_count": int(row.trade_count or 0),
                        "total_volume": float(row.total_volume or 0),
                    }
                )

            return chains

        except Exception as e:
            logger.error(f"Error getting chain volume: {e}", exc_info=True)
            return []

    async def get_all_metrics(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get all DEX trading metrics

        Args:
            db: Database session
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            Dictionary with all metrics
        """
        try:
            volume = await self.get_trade_volume(db, start_date, end_date)
            fees = await self.get_fee_collection(db, start_date, end_date)
            aggregators = await self.get_aggregator_performance(
                db, start_date, end_date
            )
            errors = await self.get_error_rates(db, start_date, end_date)
            chains = await self.get_chain_volume(db, start_date, end_date)

            return {
                "volume": volume,
                "fees": fees,
                "aggregators": aggregators,
                "errors": errors,
                "chains": chains,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting all metrics: {e}", exc_info=True)
            return {
                "volume": {},
                "fees": {},
                "aggregators": [],
                "errors": {},
                "chains": [],
                "timestamp": datetime.utcnow().isoformat(),
            }


# Singleton instance
_dex_metrics_service: Optional[DEXMetricsService] = None


def get_dex_metrics_service() -> DEXMetricsService:
    """Get singleton DEXMetricsService instance"""
    global _dex_metrics_service
    if _dex_metrics_service is None:
        _dex_metrics_service = DEXMetricsService()
    return _dex_metrics_service
