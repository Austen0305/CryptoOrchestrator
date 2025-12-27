"""add_performance_indexes

Revision ID: b2c3d4e5f6a7
Revises: e7f8g9h0i1j2
Create Date: 2025-01-XX 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'e7f8g9h0i1j2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_columns(table: str, cols: list[str]) -> bool:
        existing = {c["name"] for c in inspector.get_columns(table)}
        return all(col in existing for col in cols)

    def has_index(table: str, name: str) -> bool:
        return name in {idx["name"] for idx in inspector.get_indexes(table)}

    # Performance indexes for trades table
    if (
        has_columns("trades", ["user_id", "mode", "created_at"])
        and not has_index("trades", "ix_trades_user_mode_created")
    ):
        op.create_index('ix_trades_user_mode_created', 'trades', ['user_id', 'mode', 'created_at'], unique=False)
    if has_columns("trades", ["symbol", "side"]) and not has_index("trades", "ix_trades_symbol_side"):
        op.create_index('ix_trades_symbol_side', 'trades', ['symbol', 'side'], unique=False)
    if has_columns("trades", ["executed_at"]) and not has_index("trades", "ix_trades_executed_at_desc"):
        op.create_index('ix_trades_executed_at_desc', 'trades', [sa.text('executed_at DESC')], unique=False)
    
    # Performance indexes for bots table
    if has_columns("bots", ["user_id", "status"]) and not has_index("bots", "ix_bots_user_status"):
        op.create_index('ix_bots_user_status', 'bots', ['user_id', 'status'], unique=False)
    if has_columns("bots", ["user_id", "active"]) and not has_index("bots", "ix_bots_user_active"):
        op.create_index('ix_bots_user_active', 'bots', ['user_id', 'active'], unique=False)
    
    # Performance indexes for portfolios table
    if has_columns("portfolios", ["user_id", "exchange"]) and not has_index("portfolios", "ix_portfolios_user_exchange"):
        op.create_index('ix_portfolios_user_exchange', 'portfolios', ['user_id', 'exchange'], unique=False)
    
    # Performance indexes for candles table
    if has_columns("candles", ["symbol", "timeframe", "timestamp"]) and not has_index("candles", "ix_candles_symbol_timeframe_ts"):
        op.create_index('ix_candles_symbol_timeframe_ts', 'candles', ['symbol', 'timeframe', 'timestamp'], unique=False)
    
    # Performance indexes for risk_alerts table
    op.create_index('ix_risk_alerts_user_created', 'risk_alerts', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_risk_alerts_user_severity', 'risk_alerts', ['user_id', 'severity'], unique=False)
    
    # Performance indexes for wallets table (if exists)
    try:
        op.create_index('ix_wallets_user_type', 'wallets', ['user_id', 'wallet_type'], unique=False)
        op.create_index('ix_wallets_user_currency', 'wallets', ['user_id', 'currency'], unique=False)
    except Exception:
        pass  # Table might not exist yet
    
    # Performance indexes for wallet_transactions table (if exists)
    try:
        op.create_index('ix_wallet_transactions_user_created', 'wallet_transactions', ['user_id', 'created_at'], unique=False)
        op.create_index('ix_wallet_transactions_type_status', 'wallet_transactions', ['transaction_type', 'status'], unique=False)
    except Exception:
        pass  # Table might not exist yet


def downgrade() -> None:
    # Drop indexes in reverse order
    try:
        op.drop_index('ix_wallet_transactions_type_status', table_name='wallet_transactions')
        op.drop_index('ix_wallet_transactions_user_created', table_name='wallet_transactions')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_wallets_user_currency', table_name='wallets')
        op.drop_index('ix_wallets_user_type', table_name='wallets')
    except Exception:
        pass
    
    op.drop_index('ix_risk_alerts_user_severity', table_name='risk_alerts')
    op.drop_index('ix_risk_alerts_user_created', table_name='risk_alerts')
    op.drop_index('ix_candles_symbol_timeframe_ts', table_name='candles')
    op.drop_index('ix_portfolios_user_exchange', table_name='portfolios')
    op.drop_index('ix_bots_user_active', table_name='bots')
    op.drop_index('ix_bots_user_status', table_name='bots')
    op.drop_index('ix_trades_executed_at_desc', table_name='trades')
    op.drop_index('ix_trades_symbol_side', table_name='trades')
    op.drop_index('ix_trades_user_mode_created', table_name='trades')

