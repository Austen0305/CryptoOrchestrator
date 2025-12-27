#!/usr/bin/env python3
"""
Database Seeding Script
Seeds the database with development/test data
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from server_fastapi.database import get_db_session
from server_fastapi.models import User, Bot, Trade, Portfolio
import hashlib


async def seed_users(db: AsyncSession, count: int = 10) -> list[int]:
    """Seed users"""
    print(f"🌱 Seeding {count} users...")
    user_ids = []
    
    for i in range(1, count + 1):
        user = User(
            email=f"user{i}@example.com",
            username=f"user{i}",
            hashed_password=hashlib.sha256(f"password{i}".encode()).hexdigest(),
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow() - timedelta(days=30 - i),
        )
        db.add(user)
        user_ids.append(user.id)
    
    await db.commit()
    print(f"✅ Created {count} users")
    return user_ids


async def seed_bots(db: AsyncSession, user_ids: list[int], bots_per_user: int = 3) -> list[int]:
    """Seed trading bots"""
    print(f"🌱 Seeding bots ({bots_per_user} per user)...")
    bot_ids = []
    
    strategies = ["simple_ma", "rsi", "bollinger_bands", "macd"]
    
    for user_id in user_ids:
        for i in range(bots_per_user):
            bot = Bot(
                user_id=user_id,
                name=f"Bot {i+1}",
                strategy=strategies[i % len(strategies)],
                symbol="BTC/USD",
                is_active=i == 0,  # First bot active
                trading_mode="paper",
                config={
                    "risk_per_trade": 0.02,
                    "max_positions": 3,
                },
                created_at=datetime.utcnow() - timedelta(days=7 - i),
            )
            db.add(bot)
            bot_ids.append(bot.id)
    
    await db.commit()
    print(f"✅ Created {len(bot_ids)} bots")
    return bot_ids


async def seed_trades(db: AsyncSession, user_ids: list[int], trades_per_user: int = 20) -> None:
    """Seed trades"""
    print(f"🌱 Seeding trades ({trades_per_user} per user)...")
    
    symbols = ["BTC/USD", "ETH/USD", "BNB/USD", "SOL/USD"]
    sides = ["buy", "sell"]
    
    trade_count = 0
    for user_id in user_ids:
        for i in range(trades_per_user):
            trade = Trade(
                user_id=user_id,
                symbol=symbols[i % len(symbols)],
                side=sides[i % 2],
                amount=Decimal("0.1") + Decimal(str(i % 10)) * Decimal("0.01"),
                price=Decimal("50000") + Decimal(str(i % 1000)),
                fee=Decimal("0.001"),
                status="completed",
                exchange="binance",
                trading_mode="paper",
                created_at=datetime.utcnow() - timedelta(hours=trades_per_user - i),
            )
            db.add(trade)
            trade_count += 1
    
    await db.commit()
    print(f"✅ Created {trade_count} trades")


async def seed_portfolios(db: AsyncSession, user_ids: list[int]) -> None:
    """Seed portfolios"""
    print(f"🌱 Seeding portfolios...")
    
    for user_id in user_ids:
        portfolio = Portfolio(
            user_id=user_id,
            name="Main Portfolio",
            total_value=Decimal("10000") + Decimal(str(user_id)) * Decimal("100"),
            total_cost=Decimal("8000") + Decimal(str(user_id)) * Decimal("80"),
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        db.add(portfolio)
    
    await db.commit()
    print(f"✅ Created {len(user_ids)} portfolios")


async def seed_database(
    users: int = 10,
    bots_per_user: int = 3,
    trades_per_user: int = 20,
    clear_existing: bool = False,
) -> None:
    """Main seeding function"""
    print("=" * 60)
    print("🌱 Database Seeding")
    print("=" * 60)
    
    async with get_db_session() as db:
        if clear_existing:
            print("⚠️  Clearing existing data...")
            # Note: In production, use proper cascade deletes
            # For now, we'll just add new data
        
        # Seed in order (respecting foreign keys)
        user_ids = await seed_users(db, count=users)
        bot_ids = await seed_bots(db, user_ids, bots_per_user=bots_per_user)
        await seed_trades(db, user_ids, trades_per_user=trades_per_user)
        await seed_portfolios(db, user_ids)
    
    print("=" * 60)
    print("✅ Database seeding complete!")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   - Users: {users}")
    print(f"   - Bots: {users * bots_per_user}")
    print(f"   - Trades: {users * trades_per_user}")
    print(f"   - Portfolios: {users}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed database with test data")
    parser.add_argument("--users", type=int, default=10, help="Number of users to create")
    parser.add_argument("--bots-per-user", type=int, default=3, help="Bots per user")
    parser.add_argument("--trades-per-user", type=int, default=20, help="Trades per user")
    parser.add_argument("--clear", action="store_true", help="Clear existing data (use with caution)")
    
    args = parser.parse_args()
    
    asyncio.run(seed_database(
        users=args.users,
        bots_per_user=args.bots_per_user,
        trades_per_user=args.trades_per_user,
        clear_existing=args.clear,
    ))


if __name__ == "__main__":
    main()
