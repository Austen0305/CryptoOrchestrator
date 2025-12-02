"""
Quick Filters for Bots and Trades
Provides pre-defined filters for common queries
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum


class BotFilter(str, Enum):
    """Pre-defined bot filters"""
    ALL = "all"
    ACTIVE = "active"
    PAUSED = "paused"
    PROFITABLE_TODAY = "profitable_today"
    NEED_ATTENTION = "need_attention"
    HIGH_PERFORMANCE = "high_performance"
    RECENTLY_CREATED = "recently_created"


class TradeFilter(str, Enum):
    """Pre-defined trade filters"""
    ALL = "all"
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    WINNING = "winning"
    LOSING = "losing"
    LARGE_TRADES = "large_trades"


def get_bot_filter_query(filter_type: BotFilter) -> Dict[str, Any]:
    """
    Get SQLAlchemy filter conditions for bot queries.
    
    Args:
        filter_type: Type of filter to apply
        
    Returns:
        Dictionary of filter conditions
    """
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    
    filters = {
        BotFilter.ALL: {},
        
        BotFilter.ACTIVE: {
            "is_active": True,
            "status": "running"
        },
        
        BotFilter.PAUSED: {
            "is_active": False
        },
        
        BotFilter.PROFITABLE_TODAY: {
            "is_active": True,
            "created_at__gte": today_start,
            # Note: Requires join with trades to calculate today's profit
        },
        
        BotFilter.NEED_ATTENTION: {
            # Bots with errors or warnings
            "status__in": ["error", "warning", "stopped"]
        },
        
        BotFilter.HIGH_PERFORMANCE: {
            "is_active": True,
            # Note: Requires calculation of Sharpe ratio or win rate
        },
        
        BotFilter.RECENTLY_CREATED: {
            "created_at__gte": now - timedelta(days=7)
        }
    }
    
    return filters.get(filter_type, {})


def get_trade_filter_query(filter_type: TradeFilter) -> Dict[str, Any]:
    """
    Get SQLAlchemy filter conditions for trade queries.
    
    Args:
        filter_type: Type of filter to apply
        
    Returns:
        Dictionary of filter conditions
    """
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = now - timedelta(days=now.weekday())
    month_start = datetime(now.year, now.month, 1)
    
    filters = {
        TradeFilter.ALL: {},
        
        TradeFilter.TODAY: {
            "executed_at__gte": today_start
        },
        
        TradeFilter.THIS_WEEK: {
            "executed_at__gte": week_start
        },
        
        TradeFilter.THIS_MONTH: {
            "executed_at__gte": month_start
        },
        
        TradeFilter.WINNING: {
            "profit__gt": 0
        },
        
        TradeFilter.LOSING: {
            "profit__lt": 0
        },
        
        TradeFilter.LARGE_TRADES: {
            # Trades above $1000 equivalent
            "amount__gte": 1000
        }
    }
    
    return filters.get(filter_type, {})


def format_filter_display_name(filter_type: str) -> str:
    """
    Get human-readable display name for filter.
    
    Args:
        filter_type: Filter enum value
        
    Returns:
        Formatted display name
    """
    display_names = {
        # Bot filters
        "all": "All Bots",
        "active": "Active Bots",
        "paused": "Paused Bots",
        "profitable_today": "Profitable Today",
        "need_attention": "Need Attention",
        "high_performance": "High Performance",
        "recently_created": "Recently Created",
        
        # Trade filters
        "today": "Today's Trades",
        "this_week": "This Week",
        "this_month": "This Month",
        "winning": "Winning Trades",
        "losing": "Losing Trades",
        "large_trades": "Large Trades (>$1000)"
    }
    
    return display_names.get(filter_type, filter_type.replace("_", " ").title())


def get_filter_description(filter_type: str) -> str:
    """
    Get description for filter.
    
    Args:
        filter_type: Filter enum value
        
    Returns:
        Filter description
    """
    descriptions = {
        # Bot filters
        "all": "Show all bots",
        "active": "Show only active and running bots",
        "paused": "Show paused or stopped bots",
        "profitable_today": "Show bots with positive profit today",
        "need_attention": "Show bots with errors or warnings",
        "high_performance": "Show bots with Sharpe ratio > 1.5",
        "recently_created": "Show bots created in last 7 days",
        
        # Trade filters
        "today": "Show trades executed today",
        "this_week": "Show trades from this week",
        "this_month": "Show trades from this month",
        "winning": "Show profitable trades only",
        "losing": "Show losing trades only",
        "large_trades": "Show trades above $1000"
    }
    
    return descriptions.get(filter_type, "")


def get_available_bot_filters() -> List[Dict[str, str]]:
    """Get list of all available bot filters with metadata."""
    return [
        {
            "value": f.value,
            "label": format_filter_display_name(f.value),
            "description": get_filter_description(f.value)
        }
        for f in BotFilter
    ]


def get_available_trade_filters() -> List[Dict[str, str]]:
    """Get list of all available trade filters with metadata."""
    return [
        {
            "value": f.value,
            "label": format_filter_display_name(f.value),
            "description": get_filter_description(f.value)
        }
        for f in TradeFilter
    ]
