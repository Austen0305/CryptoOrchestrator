"""
Export Routes - Export trades and performance data to CSV/PDF
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import logging
import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies.auth import get_current_user
from ..database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_trades_csv(trades: List[dict]) -> str:
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
        'trade_id', 'bot_id', 'symbol', 'side', 'type',
        'amount', 'price', 'total', 'fee', 'profit',
        'profit_percent', 'executed_at', 'status'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for trade in trades:
        row = {
            'trade_id': trade.get('id', ''),
            'bot_id': trade.get('bot_id', ''),
            'symbol': trade.get('symbol', ''),
            'side': trade.get('side', ''),
            'type': trade.get('order_type', ''),
            'amount': trade.get('amount', 0),
            'price': trade.get('price', 0),
            'total': trade.get('total_value', 0),
            'fee': trade.get('fee', 0),
            'profit': trade.get('profit', 0),
            'profit_percent': trade.get('profit_percent', 0),
            'executed_at': trade.get('executed_at', ''),
            'status': trade.get('status', '')
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
    writer.writerow(['Metric', 'Value'])
    
    for key, value in metrics.items():
        writer.writerow([key.replace('_', ' ').title(), value])
    
    return output.getvalue()


@router.get("/export/trades/csv", tags=["Export"])
async def export_trades_csv(
    start_date: Optional[date] = Query(None, description="Start date for export"),
    end_date: Optional[date] = Query(None, description="End date for export"),
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Export trades to CSV file.
    
    Allows filtering by date range, bot, and symbol.
    """
    try:
        from sqlalchemy import select, and_
        from ..models.trade import Trade
        
        # Build query
        query = select(Trade).where(Trade.user_id == current_user["id"])
        
        if start_date:
            query = query.where(Trade.executed_at >= datetime.combine(start_date, datetime.min.time()))
        
        if end_date:
            query = query.where(Trade.executed_at <= datetime.combine(end_date, datetime.max.time()))
        
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
            trades_data.append({
                'id': trade.id,
                'bot_id': trade.bot_id,
                'symbol': trade.symbol,
                'side': trade.side,
                'order_type': trade.order_type,
                'amount': trade.amount,
                'price': trade.price,
                'total_value': trade.amount * trade.price,
                'fee': trade.fee,
                'profit': trade.profit,
                'profit_percent': trade.profit_percent,
                'executed_at': trade.executed_at.isoformat() if trade.executed_at else '',
                'status': trade.status
            })
        
        # Generate CSV
        csv_content = generate_trades_csv(trades_data)
        
        # Create filename
        filename = f"trades_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Return as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except Exception as e:
        logger.error(f"Error exporting trades to CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to export trades"
        )


@router.get("/export/performance/csv", tags=["Export"])
async def export_performance_csv(
    start_date: Optional[date] = Query(None, description="Start date for export"),
    end_date: Optional[date] = Query(None, description="End date for export"),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Export performance metrics to CSV file.
    """
    try:
        # TODO: Fetch actual performance metrics
        metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_profit': 0.0,
            'average_profit': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown': 0.0,
            'calmar_ratio': 0.0,
            'profit_factor': 0.0
        }
        
        # Generate CSV
        csv_content = generate_performance_csv(metrics)
        
        # Create filename
        filename = f"performance_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Return as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except Exception as e:
        logger.error(f"Error exporting performance to CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to export performance metrics"
        )


@router.get("/export/bots/csv", tags=["Export"])
async def export_bots_csv(
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Export bot configurations to CSV file.
    """
    try:
        from sqlalchemy import select
        from ..models.bot import Bot
        
        # Get all user's bots
        query = select(Bot).where(Bot.user_id == current_user["id"])
        result = await db_session.execute(query)
        bots = result.scalars().all()
        
        # Generate CSV
        output = io.StringIO()
        fieldnames = [
            'bot_id', 'name', 'strategy', 'symbol', 'exchange',
            'status', 'is_active', 'total_profit', 'win_rate',
            'created_at', 'updated_at'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for bot in bots:
            row = {
                'bot_id': bot.id,
                'name': bot.name,
                'strategy': bot.strategy,
                'symbol': bot.symbol,
                'exchange': bot.exchange,
                'status': bot.status,
                'is_active': bot.active,
                'total_profit': bot.total_profit or 0,
                'win_rate': 0,  # TODO: Calculate from trades
                'created_at': bot.created_at.isoformat() if bot.created_at else '',
                'updated_at': bot.updated_at.isoformat() if bot.updated_at else ''
            }
            writer.writerow(row)
        
        csv_content = output.getvalue()
        
        # Create filename
        filename = f"bots_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Return as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except Exception as e:
        logger.error(f"Error exporting bots to CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to export bots"
        )
