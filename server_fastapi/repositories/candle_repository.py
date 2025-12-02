from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.candle import Candle

class CandleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, candle: Candle) -> Candle:
        """Insert candle; on conflict (symbol,timeframe,ts) update OHLCV/updated_at.

        Supports SQLite (ON CONFLICT DO NOTHING then selective update) and
        PostgreSQL (native upsert).
        """
        table = Candle.__table__
        binder = self.session.bind
        if binder and binder.dialect.name == 'postgresql':
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
                    index_elements=['symbol', 'timeframe', 'ts'],
                    set=dict(
                        open=candle.open,
                        high=candle.high,
                        low=candle.low,
                        close=candle.close,
                        volume=candle.volume,
                    )
                )
                .returning(table)
            )
            res = await self.session.execute(stmt)
            await self.session.commit()
            return res.fetchone() or candle
        else:
            # SQLite path: DO NOTHING on conflict, then update if row existed
            stmt = sqlite_insert(table).values(
                symbol=candle.symbol,
                timeframe=candle.timeframe,
                ts=candle.ts,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
            ).prefix_with("OR IGNORE")
            await self.session.execute(stmt)
            # Try to update existing row to new values (idempotent if just inserted)
            await self.session.execute(
                table.update()
                .where(
                    (table.c.symbol == candle.symbol) &
                    (table.c.timeframe == candle.timeframe) &
                    (table.c.ts == candle.ts)
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

    async def get_history(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        stmt = select(Candle).where(
            Candle.symbol == symbol,
            Candle.timeframe == timeframe
        ).order_by(Candle.ts.desc()).limit(limit)
        res = await self.session.execute(stmt)
        rows = list(reversed(res.scalars().all()))
        return rows

    async def get_since(self, symbol: str, timeframe: str, since_ms: int, limit: int = 1000) -> List[Candle]:
        stmt = select(Candle).where(
            Candle.symbol == symbol,
            Candle.timeframe == timeframe,
            Candle.ts >= since_ms
        ).order_by(Candle.ts.asc()).limit(limit)
        res = await self.session.execute(stmt)
        return res.scalars().all()
