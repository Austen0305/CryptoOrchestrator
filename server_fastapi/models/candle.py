from sqlalchemy import String, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin

class Candle(Base, TimestampMixin):
    __tablename__ = 'candles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    timeframe: Mapped[str] = mapped_column(String(10), index=True)
    ts: Mapped[int] = mapped_column(Integer, index=True)  # epoch ms
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float, default=0)

    __table_args__ = (
        Index('ix_candles_symbol_tf_ts', 'symbol', 'timeframe', 'ts', unique=True),
    )
