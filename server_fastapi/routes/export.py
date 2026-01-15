"""
Export Routes - Export trades and performance data to CSV/PDF
"""

import csv
import io
import logging
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..dependencies.pnl import get_pnl_service
from ..services.pnl_service import PnLService
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_trades_csv(trades: list[dict]) -> str:
    """
    Generate CSV string from trades data.

    Args:
        trades: List of trade dictionaries

    Returns:
        CSV formatted string
    """
    output = io.StringIO()

    if not trades:
        return "No trades to export"

    # Define CSV columns
    fieldnames = [
        "trade_id",
        "bot_id",
        "symbol",
        "side",
        "type",
        "amount",
        "price",
        "total",
        "fee",
        "profit",
        "profit_percent",
        "executed_at",
        "status",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for trade in trades:
        row = {
            "trade_id": trade.get("id", ""),
            "bot_id": trade.get("bot_id", ""),
            "symbol": trade.get("symbol", ""),
            "side": trade.get("side", ""),
            "type": trade.get("order_type", ""),
            "amount": trade.get("amount", 0),
            "price": trade.get("price", 0),
            "total": trade.get("total_value", 0),
            "fee": trade.get("fee", 0),
            "profit": trade.get("profit", 0),
            "profit_percent": trade.get("profit_percent", 0),
            "executed_at": trade.get("executed_at", ""),
            "status": trade.get("status", ""),
        }
        writer.writerow(row)

    return output.getvalue()


def generate_performance_csv(metrics: dict) -> str:
    """
    Generate CSV string from performance metrics.

    Args:
        metrics: Performance metrics dictionary

    Returns:
        CSV formatted string
    """
    output = io.StringIO()

    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])

    for key, value in metrics.items():
        writer.writerow([key.replace("_", " ").title(), value])

    return output.getvalue()


@router.get("/export/trades/csv", tags=["Export"])
async def export_trades_csv(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: date | None = Query(None, description="Start date for export"),
    end_date: date | None = Query(None, description="End date for export"),
    bot_id: str | None = Query(None, description="Filter by bot ID"),
    symbol: str | None = Query(None, description="Filter by symbol"),
):
    """
    Export trades to CSV file.

    Allows filtering by date range, bot, and symbol.
    """
    try:
        user_id = _get_user_id(current_user)
        from sqlalchemy import select

        from ..models.trade import Trade

        # Build query
        query = select(Trade).where(Trade.user_id == user_id)

        if start_date:
            query = query.where(
                Trade.executed_at >= datetime.combine(start_date, datetime.min.time())
            )

        if end_date:
            query = query.where(
                Trade.executed_at <= datetime.combine(end_date, datetime.max.time())
            )

        if bot_id:
            query = query.where(Trade.bot_id == bot_id)

        if symbol:
            query = query.where(Trade.symbol == symbol)

        query = query.order_by(Trade.executed_at.desc())

        # Execute query
        result = await db_session.execute(query)
        trades = result.scalars().all()

        # Convert to dictionaries
        trades_data = []
        for trade in trades:
            trades_data.append(
                {
                    "id": trade.id,
                    "bot_id": trade.bot_id,
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "order_type": trade.order_type,
                    "amount": trade.amount,
                    "price": trade.price,
                    "total_value": trade.amount * trade.price,
                    "fee": trade.fee,
                    "profit": trade.profit,
                    "profit_percent": trade.profit_percent,
                    "executed_at": (
                        trade.executed_at.isoformat() if trade.executed_at else ""
                    ),
                    "status": trade.status,
                }
            )

        # Generate CSV
        csv_content = generate_trades_csv(trades_data)

        # Create filename
        filename = f"trades_export_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"

        # Return as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"Error exporting trades to CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export trades")


@router.get("/export/performance/csv", tags=["Export"])
async def export_performance_csv(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    pnl_service: Annotated[PnLService, Depends(get_pnl_service)],
    start_date: date | None = Query(None, description="Start date for export"),
    end_date: date | None = Query(None, description="End date for export"),
    mode: str | None = Query("paper", description="Trading mode (paper/real)"),
):
    """
    Export performance metrics to CSV file.
    """
    try:
        user_id = _get_user_id(current_user)
        # Fetch actual performance metrics from trades
        from sqlalchemy import and_, select

        from ..models.trade import Trade
        from ..utils.trading_utils import normalize_trading_mode

        # Get user's trades
        normalized_mode = normalize_trading_mode(mode or "paper")
        trades_query = select(Trade).where(
            and_(
                Trade.user_id == user_id,
                Trade.mode == normalized_mode,
                Trade.status == "completed",
            )
        )
        trades_result = await db_session.execute(trades_query)
        trades = trades_result.scalars().all()

        # Calculate metrics from trades
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl and t.pnl < 0]
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)

        win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0.0

        profits = [float(t.pnl) for t in trades if t.pnl is not None]
        total_profit = sum(profits) if profits else 0.0
        average_profit = (total_profit / len(profits)) if profits else 0.0

        # ✅ Use injected service - Calculate advanced metrics using PnLService
        # For now, use basic calculations (full implementation would use pnl_service methods)
        gross_profit = sum([p for p in profits if p > 0]) if profits else 0.0
        gross_loss = abs(sum([p for p in profits if p < 0])) if profits else 0.001
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Calculate drawdown (simplified)
        cumulative = []
        running_total = 0.0
        for p in profits:
            running_total += p
            cumulative.append(running_total)
        if cumulative:
            peak = cumulative[0]
            max_drawdown = 0.0
            for value in cumulative:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak if peak > 0 else 0.0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        else:
            max_drawdown = 0.0

        metrics = {
            "total_trades": total_trades,
            "winning_trades": winning_count,
            "losing_trades": losing_count,
            "win_rate": round(win_rate, 2),
            "total_profit": round(total_profit, 2),
            "average_profit": round(average_profit, 2),
            "sharpe_ratio": 0.0,  # Requires returns calculation
            "sortino_ratio": 0.0,  # Requires returns calculation
            "max_drawdown": round(max_drawdown, 4),
            "calmar_ratio": 0.0,  # Requires annual return
            "profit_factor": round(profit_factor, 2),
        }

        # Generate CSV
        csv_content = generate_performance_csv(metrics)

        # Create filename
        filename = (
            f"performance_export_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"
        )

        # Return as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"Error exporting performance to CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to export performance metrics"
        )


@router.get("/export/bots/csv", tags=["Export"])
async def export_bots_csv(
    current_user: Annotated[dict, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Export bot configurations to CSV file.
    """
    try:
        user_id = _get_user_id(current_user)
        from sqlalchemy import select

        from ..models.bot import Bot

        # Get all user's bots
        query = select(Bot).where(Bot.user_id == user_id)
        result = await db_session.execute(query)
        bots = result.scalars().all()

        # Generate CSV
        output = io.StringIO()
        fieldnames = [
            "bot_id",
            "name",
            "strategy",
            "symbol",
            "exchange",
            "status",
            "is_active",
            "total_profit",
            "win_rate",
            "created_at",
            "updated_at",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Get trades for all bots to calculate win rates
        from sqlalchemy import and_, select

        from ..models.trade import Trade

        for bot in bots:
            # Calculate win rate from trades for this bot
            win_rate = 0.0
            try:
                trades_query = select(Trade).where(
                    and_(
                        Trade.bot_id == str(bot.id),
                        Trade.status == "completed",
                    )
                )
                trades_result = await db_session.execute(trades_query)
                bot_trades = trades_result.scalars().all()

                if bot_trades:
                    winning_trades = [t for t in bot_trades if t.pnl and t.pnl > 0]
                    win_rate = (
                        (len(winning_trades) / len(bot_trades) * 100)
                        if bot_trades
                        else 0.0
                    )
            except Exception as e:
                logger.debug(f"Failed to calculate win rate for bot {bot.id}: {e}")

            row = {
                "bot_id": bot.id,
                "name": bot.name,
                "strategy": bot.strategy,
                "symbol": bot.symbol,
                "exchange": bot.exchange,
                "status": bot.status,
                "is_active": bot.active,
                "total_profit": bot.total_profit or 0,
                "win_rate": round(win_rate, 2),
                "created_at": bot.created_at.isoformat() if bot.created_at else "",
                "updated_at": bot.updated_at.isoformat() if bot.updated_at else "",
            }
            writer.writerow(row)

        csv_content = output.getvalue()

        # Create filename
        filename = f"bots_export_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"

        # Return as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"Error exporting bots to CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export bots")
