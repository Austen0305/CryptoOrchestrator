"""
Database Migration Management with Alembic
Run: alembic upgrade head
"""
# This file is intentionally minimal - Alembic autogenerates migrations

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import your models - this ensures all models are registered with Base.metadata
try:
    from server_fastapi.models import Base
    # Import all models to ensure they're registered with Base.metadata
    from server_fastapi.models import (
        User, Bot, RiskAlert, RiskLimit, Portfolio, Trade,
        Candle, ExchangeAPIKey, Wallet, WalletTransaction, IdempotencyKey,
        Order, OrderType, OrderStatus, Follow, CopiedTrade
    )
    # Import new competitive bot models
    try:
        from server_fastapi.models import GridBot, DCABot, InfinityGrid, TrailingBot, FuturesPosition
    except ImportError:
        pass  # Models may not all exist yet
    # Import DEX trading models
    try:
        from server_fastapi.models import DEXTrade, TradingFee, WalletNonce, UserWallet
    except ImportError:
        pass  # Models may not all exist yet
    # Import marketplace models
    try:
        from server_fastapi.models import SignalProvider, SignalProviderRating, Payout
    except ImportError:
        pass  # Models may not all exist yet
    # Import indicator marketplace models
    try:
        from server_fastapi.models import Indicator, IndicatorVersion, IndicatorPurchase, IndicatorRating
    except ImportError:
        pass  # Models may not all exist yet
    # Import institutional wallet models
    try:
        from server_fastapi.models import InstitutionalWallet, PendingTransaction, InstitutionalWalletTransaction, WalletAccessLog
    except ImportError:
        pass  # Models may not all exist yet
    # Import social recovery models
    try:
        from server_fastapi.models import SocialRecoveryGuardian, RecoveryRequest, RecoveryApproval
    except ImportError:
        pass  # Models may not all exist yet
    # Import accounting connection models
    try:
        from server_fastapi.models import AccountingConnection, AccountingSyncLog
    except ImportError:
        pass  # Models may not all exist yet
    # Import onboarding models
    try:
        from server_fastapi.models import OnboardingProgress, UserAchievement
    except ImportError:
        pass  # Models may not all exist yet
    # Import user analytics models
    try:
        from server_fastapi.models import UserEvent, FeatureUsage, ConversionFunnel, UserJourney, UserSatisfaction
    except ImportError:
        pass  # Models may not all exist yet
    # Import social & community models
    try:
        from server_fastapi.models import SharedStrategy, StrategyLike, StrategyComment, SocialFeedEvent, UserProfile, Achievement, UserAchievement, CommunityChallenge, ChallengeParticipant
    except ImportError:
        pass  # Models may not all exist yet
    # Import feature flags models
    try:
        from server_fastapi.models import FeatureFlag, FlagEvaluation, ABTestExperiment, ExperimentAssignment
    except ImportError:
        pass  # Models may not all exist yet
    # Import audit logs models
    try:
        from server_fastapi.models import AuditLog
    except ImportError:
        pass
    # Import webhooks and API keys models
    try:
        from server_fastapi.models import Webhook, WebhookDelivery, APIKey, APIKeyUsage
    except ImportError:
        pass
except ImportError:
    try:
        from models import Base
        # Import all models to ensure they're registered with Base.metadata
        from models import (
            User, Bot, RiskAlert, RiskLimit, Portfolio, Trade,
            Candle, ExchangeAPIKey, Wallet, WalletTransaction, IdempotencyKey,
            Order, OrderType, OrderStatus, Follow, CopiedTrade
        )
        # Import new competitive bot models
        try:
            from models import GridBot, DCABot, InfinityGrid, TrailingBot, FuturesPosition
        except ImportError:
            pass  # Models may not all exist yet
        # Import DEX trading models
        try:
            from models import DEXTrade, TradingFee, WalletNonce, UserWallet
        except ImportError:
            pass  # Models may not all exist yet
        # Import marketplace models
        try:
            from models import SignalProvider, SignalProviderRating, Payout
        except ImportError:
            pass  # Models may not all exist yet
        # Import indicator marketplace models
        try:
            from models import Indicator, IndicatorVersion, IndicatorPurchase, IndicatorRating
        except ImportError:
            pass  # Models may not all exist yet
        # Import institutional wallet models
        try:
            from models import InstitutionalWallet, PendingTransaction, InstitutionalWalletTransaction, WalletAccessLog
        except ImportError:
            pass  # Models may not all exist yet
        # Import social recovery models
        try:
            from models import SocialRecoveryGuardian, RecoveryRequest, RecoveryApproval
        except ImportError:
            pass  # Models may not all exist yet
        # Import accounting connection models
        try:
            from models import AccountingConnection, AccountingSyncLog
        except ImportError:
            pass  # Models may not all exist yet
        # Import onboarding models
        try:
            from models import OnboardingProgress, UserAchievement
        except ImportError:
            pass  # Models may not all exist yet
        # Import user analytics models
        try:
            from models import UserEvent, FeatureUsage, ConversionFunnel, UserJourney, UserSatisfaction
        except ImportError:
            pass  # Models may not all exist yet
        # Import social & community models
        try:
            from models import SharedStrategy, StrategyLike, StrategyComment, SocialFeedEvent, UserProfile, Achievement, UserAchievement, CommunityChallenge, ChallengeParticipant
        except ImportError:
            pass  # Models may not all exist yet
        # Import feature flags models
        try:
            from models import FeatureFlag, FlagEvaluation, ABTestExperiment, ExperimentAssignment
        except ImportError:
            pass  # Models may not all exist yet
        # Import audit logs models
        try:
            from models import AuditLog
        except ImportError:
            pass  # Models may not all exist yet
        # Import webhooks and API keys models
        try:
            from models import Webhook, WebhookDelivery, APIKey, APIKeyUsage
        except ImportError:
            pass  # Models may not all exist yet
    except ImportError:
        pass  # Models may not all exist yet

# this is the Alembic Config object
config = context.config

# Override database URL from environment variable if set (for deployment)
# This allows DATABASE_URL to be set in production without modifying alembic.ini
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Convert async URLs to sync for Alembic (Alembic uses sync SQLAlchemy)
    if "aiosqlite" in database_url:
        database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://")
    elif "asyncpg" in database_url:
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Get database URL (already converted from env var if set)
    url = config.get_main_option("sqlalchemy.url")
    # Additional conversion for async URLs (in case env var wasn't set)
    if url and "aiosqlite" in url:
        # Convert async SQLite URL to sync
        url = url.replace("sqlite+aiosqlite://", "sqlite://")
        config.set_main_option("sqlalchemy.url", url)
    elif url and "asyncpg" in url:
        # Convert async PostgreSQL URL to sync
        url = url.replace("postgresql+asyncpg://", "postgresql://")
        config.set_main_option("sqlalchemy.url", url)
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
