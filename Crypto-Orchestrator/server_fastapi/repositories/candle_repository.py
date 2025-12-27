from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from ..models.candle import Candle

logger = logging.getLogger(__name__)


class CandleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._use_asyncpg = False
        self._asyncpg_pool = None

        # Try to use asyncpg for PostgreSQL hot path queries
        try:
            from ..database.asyncpg_pool import AsyncPGPool

            if AsyncPGPool._is_initialized:
                self._asyncpg_pool = AsyncPGPool
                self._use_asyncpg = True
        except (ImportError, AttributeError):
            # Fallback to SQLAlchemy if asyncpg not available
            pass

    async def upsert(self, candle: Candle) -> Candle:
        """Insert candle; on conflict (symbol,timeframe,ts) update OHLCV/updated_at.

        Supports SQLite (ON CONFLICT DO NOTHING then selective update) and
        PostgreSQL (native upsert).
        """
        table = Candle.__table__
        binder = self.session.bind
        if binder and binder.dialect.name == "postgresql":
            stmt = (
                pg_insert(table)
                .values(
                    symbol=candle.symbol,
                    timeframe=candle.timeframe,
                    ts=candle.ts,
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    volume=candle.volume,
                )
                .on_conflict_do_update(
                    index_elements=["symbol", "timeframe", "ts"],
                    set=dict(
                        open=candle.open,
                        high=candle.high,
                        low=candle.low,
                        close=candle.close,
                        volume=candle.volume,
                    ),
                )
                .returning(table)
            )
            res = await self.session.execute(stmt)
            await self.session.commit()
            return res.fetchone() or candle
        else:
            # SQLite path: DO NOTHING on conflict, then update if row existed
            stmt = (
                sqlite_insert(table)
                .values(
                    symbol=candle.symbol,
                    timeframe=candle.timeframe,
                    ts=candle.ts,
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    volume=candle.volume,
                )
                .prefix_with("OR IGNORE")
            )
            await self.session.execute(stmt)
            # Try to update existing row to new values (idempotent if just inserted)
            await self.session.execute(
                table.update()
                .where(
                    (table.c.symbol == candle.symbol)
                    & (table.c.timeframe == candle.timeframe)
                    & (table.c.ts == candle.ts)
                )
                .values(
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    volume=candle.volume,
                )
            )
            await self.session.commit()
            return candle

    async def get_history(
        self, symbol: str, timeframe: str, limit: int
    ) -> List[Candle]:
        """Get candle history - uses asyncpg for PostgreSQL if available"""
        # Use asyncpg for hot path queries if available (PostgreSQL only)
        if (
            self._use_asyncpg
            and self.session.bind
            and self.session.bind.dialect.name == "postgresql"
        ):
            try:
                pool = await self._asyncpg_pool.get_pool()
                async with pool.acquire() as conn:
                    rows = await conn.fetch(
                        """
                        SELECT id, symbol, timeframe, ts, open, high, low, close, volume, created_at, updated_at
                        FROM candles
                        WHERE symbol = $1 AND timeframe = $2
                        ORDER BY ts DESC
                        LIMIT $3
                        """,
                        symbol,
                        timeframe,
                        limit,
                    )
                    # Convert to Candle objects
                    candles = []
                    for row in reversed(rows):
                        candle = Candle(
                            id=row["id"],
                            symbol=row["symbol"],
                            timeframe=row["timeframe"],
                            ts=row["ts"],
                            open=row["open"],
                            high=row["high"],
                            low=row["low"],
                            close=row["close"],
                            volume=row["volume"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                        candles.append(candle)
                    return candles
            except Exception as e:
                logger.warning(f"AsyncPG query failed, falling back to SQLAlchemy: {e}")
                # Fall through to SQLAlchemy

        # Fallback to SQLAlchemy
        stmt = (
            select(Candle)
            .where(Candle.symbol == symbol, Candle.timeframe == timeframe)
            .order_by(Candle.ts.desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        rows = list(reversed(res.scalars().all()))
        return rows

    async def get_since(
        self, symbol: str, timeframe: str, since_ms: int, limit: int = 1000
    ) -> List[Candle]:
        """Get candles since timestamp - uses asyncpg for PostgreSQL if available"""
        # Use asyncpg for hot path queries if available (PostgreSQL only)
        if (
            self._use_asyncpg
            and self.session.bind
            and self.session.bind.dialect.name == "postgresql"
        ):
            try:
                pool = await self._asyncpg_pool.get_pool()
                async with pool.acquire() as conn:
                    rows = await conn.fetch(
                        """
                        SELECT id, symbol, timeframe, ts, open, high, low, close, volume, created_at, updated_at
                        FROM candles
                        WHERE symbol = $1 AND timeframe = $2 AND ts >= $3
                        ORDER BY ts ASC
                        LIMIT $4
                        """,
                        symbol,
                        timeframe,
                        since_ms,
                        limit,
                    )
                    # Convert to Candle objects
                    candles = []
                    for row in rows:
                        candle = Candle(
                            id=row["id"],
                            symbol=row["symbol"],
                            timeframe=row["timeframe"],
                            ts=row["ts"],
                            open=row["open"],
                            high=row["high"],
                            low=row["low"],
                            close=row["close"],
                            volume=row["volume"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                        candles.append(candle)
                    return candles
            except Exception as e:
                logger.warning(f"AsyncPG query failed, falling back to SQLAlchemy: {e}")
                # Fall through to SQLAlchemy

        # Fallback to SQLAlchemy
        stmt = (
            select(Candle)
            .where(
                Candle.symbol == symbol,
                Candle.timeframe == timeframe,
                Candle.ts >= since_ms,
            )
            .order_by(Candle.ts.asc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()
