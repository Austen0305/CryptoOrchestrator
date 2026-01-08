"""
Test data factories for creating test entities.
Provides factories for users, bots, wallets, trades, etc.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

try:
    from server_fastapi.models.bot import Bot
    from server_fastapi.models.order import Order
    from server_fastapi.models.portfolio import Portfolio
    from server_fastapi.models.trade import Trade
    from server_fastapi.models.user import User
    from server_fastapi.models.wallet import UserWallet, Wallet
    from server_fastapi.services.auth.auth_service import AuthService
except ImportError:
    # Models may not be available in all test environments
    User = None
    Bot = None
    Wallet = None
    UserWallet = None
    Trade = None
    Portfolio = None
    Order = None
    AuthService = None


class UserFactory:
    """Factory for creating test users"""

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str | None = None,
        password: str = "TestPassword123!",
        name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create a test user in the database"""
        if AuthService is None:
            raise ImportError("AuthService not available")

        unique_email = email or f"testuser-{uuid.uuid4().hex[:8]}@example.com"
        user_name = name or f"Test User {uuid.uuid4().hex[:6]}"

        auth_service = AuthService()
        user = await auth_service.register_user(
            email=unique_email, password=password, name=user_name, **kwargs
        )

        return {
            "id": user.get("id") if isinstance(user, dict) else str(user),
            "email": unique_email,
            "name": user_name,
            "password": password,
            **kwargs,
        }

    @staticmethod
    def user_data(
        email: str | None = None,
        password: str = "TestPassword123!",
        name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate user data dict without creating in DB"""
        unique_email = email or f"testuser-{uuid.uuid4().hex[:8]}@example.com"
        user_name = name or f"Test User {uuid.uuid4().hex[:6]}"

        return {
            "email": unique_email,
            "password": password,
            "name": user_name,
            **kwargs,
        }


class BotFactory:
    """Factory for creating test bots"""

    @staticmethod
    def bot_data(
        name: str | None = None,
        symbol: str = "BTC/USDT",
        strategy: str = "simple_ma",
        user_id: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate bot configuration data"""
        bot_name = name or f"Test Bot {uuid.uuid4().hex[:6]}"

        default_config = {
            "max_position_size": 0.1,
            "stop_loss": 0.02,
            "take_profit": 0.05,
            "risk_per_trade": 0.01,
        }

        config = kwargs.pop("config", {})
        default_config.update(config)

        return {
            "name": bot_name,
            "symbol": symbol,
            "strategy": strategy,
            "config": default_config,
            "is_active": False,
            **kwargs,
        }

    @staticmethod
    async def create_bot(
        db: AsyncSession,
        user_id: str,
        name: str | None = None,
        symbol: str = "BTC/USDT",
        strategy: str = "simple_ma",
        **kwargs,
    ) -> dict[str, Any] | None:
        """Create a bot in the database"""
        if Bot is None:
            return None

        bot_data = BotFactory.bot_data(
            name=name, symbol=symbol, strategy=strategy, **kwargs
        )

        bot = Bot(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=bot_data["name"],
            symbol=bot_data["symbol"],
            strategy=bot_data["strategy"],
            config=bot_data["config"],
            is_active=bot_data.get("is_active", False),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(bot)
        await db.commit()
        await db.refresh(bot)

        return {
            "id": bot.id,
            "user_id": bot.user_id,
            "name": bot.name,
            "symbol": bot.symbol,
            "strategy": bot.strategy,
            "config": bot.config,
            "is_active": bot.is_active,
        }


class WalletFactory:
    """Factory for creating test wallets"""

    @staticmethod
    def wallet_data(
        user_id: str | None = None,
        chain_id: int = 1,  # Ethereum
        address: str | None = None,
        is_custodial: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate wallet data"""
        if address is None:
            # Generate a fake Ethereum address
            address = f"0x{uuid.uuid4().hex[:40]}"

        return {
            "user_id": user_id,
            "chain_id": chain_id,
            "address": address,
            "is_custodial": is_custodial,
            "balance": kwargs.get("balance", "0.0"),
            "created_at": datetime.utcnow(),
            **kwargs,
        }

    @staticmethod
    async def create_wallet(
        db: AsyncSession,
        user_id: str,
        chain_id: int = 1,
        address: str | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Create a wallet in the database"""
        if UserWallet is None:
            return None

        wallet_data = WalletFactory.wallet_data(
            user_id=user_id, chain_id=chain_id, address=address, **kwargs
        )

        wallet = UserWallet(
            id=str(uuid.uuid4()),
            user_id=user_id,
            chain_id=chain_id,
            address=wallet_data["address"],
            is_custodial=wallet_data.get("is_custodial", True),
            balance=wallet_data.get("balance", "0.0"),
            created_at=wallet_data["created_at"],
        )

        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)

        return {
            "id": wallet.id,
            "user_id": wallet.user_id,
            "chain_id": wallet.chain_id,
            "address": wallet.address,
            "is_custodial": wallet.is_custodial,
            "balance": wallet.balance,
        }


class TradeFactory:
    """Factory for creating test trades"""

    @staticmethod
    def trade_data(
        user_id: str | None = None,
        bot_id: str | None = None,
        symbol: str = "BTC/USDT",
        side: str = "buy",
        amount: float = 0.1,
        price: float = 50000.0,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate trade data"""
        return {
            "user_id": user_id,
            "bot_id": bot_id,
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": price,
            "fee": kwargs.get("fee", 0.001),
            "status": kwargs.get("status", "completed"),
            "mode": kwargs.get("mode", "paper"),
            "created_at": kwargs.get("created_at", datetime.utcnow()),
            **kwargs,
        }

    @staticmethod
    async def create_trade(
        db: AsyncSession,
        user_id: str,
        bot_id: str | None = None,
        symbol: str = "BTC/USDT",
        side: str = "buy",
        **kwargs,
    ) -> dict[str, Any] | None:
        """Create a trade in the database"""
        if Trade is None:
            return None

        trade_data = TradeFactory.trade_data(
            user_id=user_id, bot_id=bot_id, symbol=symbol, side=side, **kwargs
        )

        trade = Trade(
            id=str(uuid.uuid4()),
            user_id=user_id,
            bot_id=trade_data.get("bot_id"),
            symbol=trade_data["symbol"],
            side=trade_data["side"],
            amount=str(trade_data["amount"]),
            price=str(trade_data["price"]),
            fee=str(trade_data["fee"]),
            status=trade_data["status"],
            mode=trade_data.get("mode", "paper"),
            created_at=trade_data["created_at"],
        )

        db.add(trade)
        await db.commit()
        await db.refresh(trade)

        return {
            "id": trade.id,
            "user_id": trade.user_id,
            "bot_id": trade.bot_id,
            "symbol": trade.symbol,
            "side": trade.side,
            "amount": float(trade.amount),
            "price": float(trade.price),
            "fee": float(trade.fee),
            "status": trade.status,
            "mode": trade.mode,
        }


class PortfolioFactory:
    """Factory for creating test portfolios"""

    @staticmethod
    def portfolio_data(
        user_id: str | None = None,
        total_balance: float = 10000.0,
        available_balance: float = 9000.0,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate portfolio data"""
        return {
            "user_id": user_id,
            "total_balance": total_balance,
            "available_balance": available_balance,
            "mode": kwargs.get("mode", "paper"),
            "updated_at": kwargs.get("updated_at", datetime.utcnow()),
            **kwargs,
        }

    @staticmethod
    async def create_portfolio(
        db: AsyncSession, user_id: str, total_balance: float = 10000.0, **kwargs
    ) -> dict[str, Any] | None:
        """Create a portfolio in the database"""
        if Portfolio is None:
            return None

        portfolio_data = PortfolioFactory.portfolio_data(
            user_id=user_id, total_balance=total_balance, **kwargs
        )

        portfolio = Portfolio(
            id=str(uuid.uuid4()),
            user_id=user_id,
            total_balance=str(portfolio_data["total_balance"]),
            available_balance=str(
                portfolio_data.get("available_balance", total_balance * 0.9)
            ),
            mode=portfolio_data.get("mode", "paper"),
            updated_at=portfolio_data["updated_at"],
        )

        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)

        return {
            "id": portfolio.id,
            "user_id": portfolio.user_id,
            "total_balance": float(portfolio.total_balance),
            "available_balance": float(portfolio.available_balance),
            "mode": portfolio.mode,
        }
