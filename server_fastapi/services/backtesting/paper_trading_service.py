"""
Paper trading service for backtesting
"""

import os
import sqlite3
import json
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging
import asyncio
import uuid

# Import cache utilities
try:
    from ...middleware.query_cache import cache_query_result
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    def cache_query_result(*args, **kwargs):
        """Fallback no-op decorator when cache not available"""
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


class PaperTrade(BaseModel):
    id: str
    user_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    timestamp: int
    pnl: float = 0.0
    fee: float = 0.0
    commission: float = 0.001


class PaperPosition(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    current_value: float
    unrealized_pnl: float


class PaperPortfolio(BaseModel):
    total_balance: float
    available_balance: float
    positions: List[PaperPosition]
    total_pnl: float
    total_pnl_percentage: float


class PaperTradingService:
    """Paper trading service with SQLite database storage"""

    def __init__(self):
        self.db_path = os.getenv('PAPER_TRADING_DB', 'paper_trading.db')
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database and create tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    timestamp INTEGER NOT NULL,
                    pnl REAL DEFAULT 0.0,
                    fee REAL DEFAULT 0.0,
                    commission REAL DEFAULT 0.001,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS paper_portfolios (
                    user_id TEXT PRIMARY KEY,
                    total_balance REAL DEFAULT 1000.0,
                    available_balance REAL DEFAULT 1000.0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    async def execute_paper_trade(self, user_id: str, symbol: str, side: str, quantity: float, price: float) -> PaperTrade:
        """Execute paper trade with proper validation and P&L calculation"""
        if side not in ['buy', 'sell']:
            raise ValueError("Side must be 'buy' or 'sell'")

        if quantity <= 0 or price <= 0:
            raise ValueError("Quantity and price must be positive")

        timestamp = int(datetime.now().timestamp() * 1000)
        trade_id = str(uuid.uuid4())

        # Get current portfolio
        portfolio = await self.get_paper_portfolio(user_id)

        if side == 'buy':
            # Check if sufficient balance
            total_cost = quantity * price * (1 + 0.001)  # Include commission
            if portfolio.available_balance < total_cost:
                raise ValueError(f"Insufficient balance. Required: {total_cost}, Available: {portfolio.available_balance}")

            # Create buy trade
            trade = PaperTrade(
                id=trade_id,
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                timestamp=timestamp,
                pnl=0.0,
                fee=total_cost - (quantity * price),
                commission=0.001
            )

            # Update portfolio
            new_balance = portfolio.available_balance - total_cost
            await self._update_portfolio_balance(user_id, new_balance, new_balance)

        else:  # sell
            # Check if sufficient position
            position = next((p for p in portfolio.positions if p.symbol == symbol), None)
            if not position or position.quantity < quantity:
                raise ValueError(f"Insufficient position for {symbol}. Available: {position.quantity if position else 0}")

            # Calculate P&L for sell
            total_value = quantity * price
            cost_basis = quantity * position.avg_price
            pnl = total_value - cost_basis - (total_value * 0.001)  # Subtract commission

            trade = PaperTrade(
                id=trade_id,
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                timestamp=timestamp,
                pnl=pnl,
                fee=total_value * 0.001,
                commission=0.001
            )

            # Update portfolio
            remaining_quantity = position.quantity - quantity
            if remaining_quantity <= 0:
                # Remove position
                portfolio.positions = [p for p in portfolio.positions if p.symbol != symbol]
            else:
                # Update position
                position.quantity = remaining_quantity

            new_balance = portfolio.available_balance + total_value - (total_value * 0.001)
            await self._update_portfolio_balance(user_id, new_balance, new_balance)

        # Save trade to database
        await self._save_trade(trade)

        logger.info(f"Paper trade executed: {trade.id} - {side} {quantity} {symbol} at {price}")
        return trade

    @cache_query_result(ttl=300, key_prefix="paper_portfolio", include_user=True) if CACHE_AVAILABLE else lambda f: f
    async def get_paper_portfolio(self, user_id: str) -> PaperPortfolio:
        """Calculate and return current paper portfolio"""
        with sqlite3.connect(self.db_path) as conn:
            # Get balance
            cursor = conn.execute('''
                SELECT total_balance, available_balance FROM paper_portfolios WHERE user_id = ?
            ''', (user_id,))
            balance_row = cursor.fetchone()

            if not balance_row:
                # Create default portfolio if not exists
                conn.execute('''
                    INSERT INTO paper_portfolios (user_id, total_balance, available_balance)
                    VALUES (?, 1000.0, 1000.0)
                ''', (user_id,))
                conn.commit()
                total_balance = available_balance = 1000.0
            else:
                total_balance, available_balance = balance_row

            # Get all trades to calculate positions
            cursor = conn.execute('''
                SELECT symbol, side, quantity, price FROM paper_trades
                WHERE user_id = ? ORDER BY timestamp
            ''', (user_id,))
            trades = cursor.fetchall()

        # Calculate positions
        positions_dict = {}
        for symbol, side, quantity, price in trades:
            if symbol not in positions_dict:
                positions_dict[symbol] = {'quantity': 0, 'total_cost': 0}

            if side == 'buy':
                positions_dict[symbol]['quantity'] += quantity
                positions_dict[symbol]['total_cost'] += quantity * price
            else:  # sell
                positions_dict[symbol]['quantity'] -= quantity
                # Note: For simplicity, we don't adjust total_cost on sell
                # In a real implementation, we'd use FIFO/LIFO accounting

        positions = []
        total_pnl = 0.0

        for symbol, data in positions_dict.items():
            if data['quantity'] > 0:
                avg_price = data['total_cost'] / (data['quantity'] + 0.000001)  # Avoid division by zero
                # Mock current price - in real implementation, get from market data
                current_price = avg_price * 1.05  # Assume 5% price movement for demo
                current_value = data['quantity'] * current_price
                unrealized_pnl = current_value - data['total_cost']

                positions.append(PaperPosition(
                    symbol=symbol,
                    quantity=data['quantity'],
                    avg_price=avg_price,
                    current_value=current_value,
                    unrealized_pnl=unrealized_pnl
                ))
                total_pnl += unrealized_pnl

        # Calculate total portfolio value
        positions_value = sum(p.current_value for p in positions)
        total_value = available_balance + positions_value
        total_pnl_percentage = (total_pnl / (total_balance - total_pnl)) * 100 if total_balance > total_pnl else 0

        return PaperPortfolio(
            total_balance=total_value,
            available_balance=available_balance,
            positions=positions,
            total_pnl=total_pnl,
            total_pnl_percentage=total_pnl_percentage
        )

    async def get_paper_trades(self, user_id: str, limit: int = 100) -> List[PaperTrade]:
        """Get paper trading history for user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, user_id, symbol, side, quantity, price, timestamp, pnl, fee, commission
                FROM paper_trades WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?
            ''', (user_id, limit))
            rows = cursor.fetchall()

        trades = []
        for row in rows:
            trades.append(PaperTrade(
                id=row[0],
                user_id=row[1],
                symbol=row[2],
                side=row[3],
                quantity=row[4],
                price=row[5],
                timestamp=row[6],
                pnl=row[7],
                fee=row[8],
                commission=row[9]
            ))

        return trades

    async def reset_paper_trading(self, user_id: str) -> bool:
        """Reset paper trading account for user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete all trades for user
                conn.execute('DELETE FROM paper_trades WHERE user_id = ?', (user_id,))
                # Reset portfolio
                conn.execute('''
                    UPDATE paper_portfolios SET total_balance = 1000.0, available_balance = 1000.0, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (user_id,))
                # If no portfolio exists, create one
                if conn.total_changes == 0:
                    conn.execute('''
                        INSERT INTO paper_portfolios (user_id, total_balance, available_balance)
                        VALUES (?, 1000.0, 1000.0)
                    ''', (user_id,))
                conn.commit()

            logger.info(f"Paper trading account reset for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reset paper trading for user {user_id}: {e}")
            return False

    async def _save_trade(self, trade: PaperTrade):
        """Save trade to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO paper_trades (id, user_id, symbol, side, quantity, price, timestamp, pnl, fee, commission)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.id, trade.user_id, trade.symbol, trade.side,
                trade.quantity, trade.price, trade.timestamp,
                trade.pnl, trade.fee, trade.commission
            ))
            conn.commit()

    async def _update_portfolio_balance(self, user_id: str, total_balance: float, available_balance: float):
        """Update portfolio balances"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE paper_portfolios SET total_balance = ?, available_balance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (total_balance, available_balance, user_id))
            if conn.total_changes == 0:
                conn.execute('''
                    INSERT INTO paper_portfolios (user_id, total_balance, available_balance)
                    VALUES (?, ?, ?)
                ''', (user_id, total_balance, available_balance))
            conn.commit()