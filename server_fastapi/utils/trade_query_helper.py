"""Trade query helper with asyncpg support for hot path queries

This utility provides optimized trade queries using asyncpg for PostgreSQL
databases, falling back to SQLAlchemy for SQLite or when asyncpg is unavailable.
"""

import logging
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.trade import Trade

logger = logging.getLogger(__name__)


class TradeQueryHelper:
    """Helper for optimized trade queries with asyncpg support"""

    @staticmethod
    async def get_trades_by_user_asyncpg(
        user_id: int, limit: int = 100, offset: int = 0, mode: str | None = None
    ) -> list[dict[str, Any]]:
        """Get trades by user using asyncpg (PostgreSQL only)"""
        try:
            from ..database.asyncpg_pool import AsyncPGPool

            if not AsyncPGPool._is_initialized:
                return []

            pool = await AsyncPGPool.get_pool()
            async with pool.acquire() as conn:
                query = """
                    SELECT id, user_id, bot_id, symbol, pair, side, order_type, 
                           amount, price, cost, fee, mode, status, pnl, 
                           executed_at, timestamp, transaction_hash, chain_id
                    FROM trades
                    WHERE user_id = $1
                """
                params = [user_id]

                if mode:
                    query += " AND mode = $2"
                    params.append(mode)

                query += " ORDER BY timestamp DESC LIMIT $%d OFFSET $%d" % (
                    len(params) + 1,
                    len(params) + 2,
                )
                params.extend([limit, offset])

                rows = await conn.fetch(query, *params)

                # Convert to dict format
                trades = []
                for row in rows:
                    trades.append(
                        {
                            "id": row["id"],
                            "user_id": row["user_id"],
                            "bot_id": row["bot_id"],
                            "symbol": row["symbol"],
                            "pair": row["pair"],
                            "side": row["side"],
                            "order_type": row["order_type"],
                            "amount": float(row["amount"]),
                            "price": float(row["price"]),
                            "cost": float(row["cost"]),
                            "fee": float(row["fee"]),
                            "mode": row["mode"],
                            "status": row["status"],
                            "pnl": float(row["pnl"]) if row["pnl"] else None,
                            "executed_at": row["executed_at"],
                            "timestamp": row["timestamp"],
                            "transaction_hash": row["transaction_hash"],
                            "chain_id": row["chain_id"],
                        }
                    )
                return trades
        except Exception as e:
            logger.warning(f"AsyncPG trade query failed: {e}")
            return []

    @staticmethod
    async def get_trades_by_user_sqlalchemy(
        session: AsyncSession,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        mode: str | None = None,
    ) -> list[Trade]:
        """Get trades by user using SQLAlchemy (fallback)"""
        stmt = select(Trade).where(Trade.user_id == user_id)

        if mode:
            stmt = stmt.where(Trade.mode == mode)

        stmt = stmt.order_by(desc(Trade.timestamp)).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_trades_by_bot_asyncpg(
        bot_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get trades by bot using asyncpg (PostgreSQL only)"""
        try:
            from ..database.asyncpg_pool import AsyncPGPool

            if not AsyncPGPool._is_initialized:
                return []

            pool = await AsyncPGPool.get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, user_id, bot_id, symbol, pair, side, order_type, 
                           amount, price, cost, fee, mode, status, pnl, 
                           executed_at, timestamp, transaction_hash, chain_id
                    FROM trades
                    WHERE bot_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2 OFFSET $3
                    """,
                    bot_id,
                    limit,
                    offset,
                )

                # Convert to dict format
                trades = []
                for row in rows:
                    trades.append(
                        {
                            "id": row["id"],
                            "user_id": row["user_id"],
                            "bot_id": row["bot_id"],
                            "symbol": row["symbol"],
                            "pair": row["pair"],
                            "side": row["side"],
                            "order_type": row["order_type"],
                            "amount": float(row["amount"]),
                            "price": float(row["price"]),
                            "cost": float(row["cost"]),
                            "fee": float(row["fee"]),
                            "mode": row["mode"],
                            "status": row["status"],
                            "pnl": float(row["pnl"]) if row["pnl"] else None,
                            "executed_at": row["executed_at"],
                            "timestamp": row["timestamp"],
                            "transaction_hash": row["transaction_hash"],
                            "chain_id": row["chain_id"],
                        }
                    )
                return trades
        except Exception as e:
            logger.warning(f"AsyncPG trade query failed: {e}")
            return []

    @staticmethod
    async def get_trades_by_bot_sqlalchemy(
        session: AsyncSession, bot_id: str, limit: int = 100, offset: int = 0
    ) -> list[Trade]:
        """Get trades by bot using SQLAlchemy (fallback)"""
        stmt = (
            select(Trade)
            .where(Trade.bot_id == bot_id)
            .order_by(desc(Trade.timestamp))
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
