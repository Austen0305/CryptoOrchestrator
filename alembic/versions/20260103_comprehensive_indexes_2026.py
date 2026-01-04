"""comprehensive_indexes_2026

Comprehensive database indexes for 2026 best practices
Adds missing indexes for all common query patterns

Revision ID: 20260103_comprehensive_indexes
Revises: <head>
Create Date: 2026-01-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260103_comprehensive_indexes'
down_revision = None  # Will be set to latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add comprehensive indexes for 2026 best practices
    
    Indexes are created using CONCURRENTLY for PostgreSQL to avoid locking
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    is_postgresql = bind.dialect.name == 'postgresql'

    def has_columns(table: str, cols: list[str]) -> bool:
        """Check if table has all required columns"""
        try:
            existing = {c["name"] for c in inspector.get_columns(table)}
            return all(col in existing for col in cols)
        except Exception:
            return False

    def has_index(table: str, name: str) -> bool:
        """Check if index already exists"""
        try:
            existing = {idx["name"] for idx in inspector.get_indexes(table)}
            return name in existing
        except Exception:
            return False

    # ==========================================
    # Orders Table Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("orders", ["user_id", "status", "created_at"]) and not has_index("orders", "idx_orders_user_status_created"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_status_created 
                ON orders(user_id, status, created_at DESC)
            """))
        else:
            op.create_index(
                'idx_orders_user_status_created',
                'orders',
                ['user_id', 'status', sa.text('created_at DESC')],
                unique=False
            )

    if has_columns("orders", ["user_id", "mode", "created_at"]) and not has_index("orders", "idx_orders_user_mode_created"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_mode_created 
                ON orders(user_id, mode, created_at DESC)
            """))
        else:
            op.create_index(
                'idx_orders_user_mode_created',
                'orders',
                ['user_id', 'mode', sa.text('created_at DESC')],
                unique=False
            )

    if has_columns("orders", ["symbol", "status", "created_at"]) and not has_index("orders", "idx_orders_symbol_status_created"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_symbol_status_created 
                ON orders(symbol, status, created_at DESC)
            """))
        else:
            op.create_index(
                'idx_orders_symbol_status_created',
                'orders',
                ['symbol', 'status', sa.text('created_at DESC')],
                unique=False
            )

    if has_columns("orders", ["bot_id", "status"]) and not has_index("orders", "idx_orders_bot_status"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_bot_status 
                ON orders(bot_id, status) 
                WHERE bot_id IS NOT NULL
            """))
        else:
            op.create_index(
                'idx_orders_bot_status',
                'orders',
                ['bot_id', 'status'],
                unique=False
            )

    # ==========================================
    # Trades Table Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("trades", ["user_id", "mode", "symbol", "created_at"]) and not has_index("trades", "idx_trades_user_mode_symbol_created"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trades_user_mode_symbol_created 
                ON trades(user_id, mode, symbol, created_at DESC)
            """))
        else:
            op.create_index(
                'idx_trades_user_mode_symbol_created',
                'trades',
                ['user_id', 'mode', 'symbol', sa.text('created_at DESC')],
                unique=False
            )

    if has_columns("trades", ["symbol", "side", "executed_at"]) and not has_index("trades", "idx_trades_symbol_side_executed"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trades_symbol_side_executed 
                ON trades(symbol, side, executed_at DESC)
            """))
        else:
            op.create_index(
                'idx_trades_symbol_side_executed',
                'trades',
                ['symbol', 'side', sa.text('executed_at DESC')],
                unique=False
            )

    if has_columns("trades", ["status", "created_at"]) and not has_index("trades", "idx_trades_status_created"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trades_status_created 
                ON trades(status, created_at DESC)
            """))
        else:
            op.create_index(
                'idx_trades_status_created',
                'trades',
                ['status', sa.text('created_at DESC')],
                unique=False
            )

    # ==========================================
    # Wallets Table Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("wallets", ["user_id", "currency", "is_active"]) and not has_index("wallets", "idx_wallets_user_currency_active"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_wallets_user_currency_active 
                ON wallets(user_id, currency, is_active)
            """))
        else:
            op.create_index(
                'idx_wallets_user_currency_active',
                'wallets',
                ['user_id', 'currency', 'is_active'],
                unique=False
            )

    if has_columns("wallets", ["user_id", "wallet_type", "is_active"]) and not has_index("wallets", "idx_wallets_user_type_active"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_wallets_user_type_active 
                ON wallets(user_id, wallet_type, is_active)
            """))
        else:
            op.create_index(
                'idx_wallets_user_type_active',
                'wallets',
                ['user_id', 'wallet_type', 'is_active'],
                unique=False
            )

    # ==========================================
    # Wallet Transactions Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("wallet_transactions", ["user_id", "transaction_type", "status", "created_at"]):
        if not has_index("wallet_transactions", "idx_wallet_txns_user_type_status_created"):
            if is_postgresql:
                op.execute(sa.text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_wallet_txns_user_type_status_created 
                    ON wallet_transactions(user_id, transaction_type, status, created_at DESC)
                """))
            else:
                op.create_index(
                    'idx_wallet_txns_user_type_status_created',
                    'wallet_transactions',
                    ['user_id', 'transaction_type', 'status', sa.text('created_at DESC')],
                    unique=False
                )

    if has_columns("wallet_transactions", ["wallet_id", "status", "created_at"]):
        if not has_index("wallet_transactions", "idx_wallet_txns_wallet_status_created"):
            if is_postgresql:
                op.execute(sa.text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_wallet_txns_wallet_status_created 
                    ON wallet_transactions(wallet_id, status, created_at DESC)
                """))
            else:
                op.create_index(
                    'idx_wallet_txns_wallet_status_created',
                    'wallet_transactions',
                    ['wallet_id', 'status', sa.text('created_at DESC')],
                    unique=False
                )

    # ==========================================
    # Bots Table Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("bots", ["user_id", "active", "status", "created_at"]) and not has_index("bots", "idx_bots_user_active_status_created"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bots_user_active_status_created 
                ON bots(user_id, active, status, created_at DESC)
            """))
        else:
            op.create_index(
                'idx_bots_user_active_status_created',
                'bots',
                ['user_id', 'active', 'status', sa.text('created_at DESC')],
                unique=False
            )

    if has_columns("bots", ["symbol", "active"]) and not has_index("bots", "idx_bots_symbol_active"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bots_symbol_active 
                ON bots(symbol, active) 
                WHERE active = true
            """))
        else:
            op.create_index(
                'idx_bots_symbol_active',
                'bots',
                ['symbol', 'active'],
                unique=False
            )

    # ==========================================
    # Portfolio Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("portfolios", ["user_id", "mode", "created_at"]) and not has_index("portfolios", "idx_portfolios_user_mode_created"):
        if is_postgresql:
            op.execute(sa.text("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolios_user_mode_created 
                ON portfolios(user_id, mode, created_at DESC)
            """))
        else:
            op.create_index(
                'idx_portfolios_user_mode_created',
                'portfolios',
                ['user_id', 'mode', sa.text('created_at DESC')],
                unique=False
            )

    # ==========================================
    # DEX Positions Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("dex_positions", ["user_id", "chain_id", "is_open", "opened_at"]):
        if not has_index("dex_positions", "idx_dex_positions_user_chain_open"):
            if is_postgresql:
                op.execute(sa.text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dex_positions_user_chain_open 
                    ON dex_positions(user_id, chain_id, is_open, opened_at DESC)
                """))
            else:
                op.create_index(
                    'idx_dex_positions_user_chain_open',
                    'dex_positions',
                    ['user_id', 'chain_id', 'is_open', sa.text('opened_at DESC')],
                    unique=False
                )

    # ==========================================
    # DEX Trades Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("dex_trades", ["user_id", "chain_id", "status", "created_at"]):
        if not has_index("dex_trades", "idx_dex_trades_user_chain_status_created"):
            if is_postgresql:
                op.execute(sa.text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dex_trades_user_chain_status_created 
                    ON dex_trades(user_id, chain_id, status, created_at DESC)
                """))
            else:
                op.create_index(
                    'idx_dex_trades_user_chain_status_created',
                    'dex_trades',
                    ['user_id', 'chain_id', 'status', sa.text('created_at DESC')],
                    unique=False
                )

    if has_columns("dex_trades", ["transaction_hash"]):
        if not has_index("dex_trades", "idx_dex_trades_tx_hash"):
            if is_postgresql:
                op.execute(sa.text("""
                    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_dex_trades_tx_hash 
                    ON dex_trades(transaction_hash) 
                    WHERE transaction_hash IS NOT NULL
                """))
            else:
                op.create_index(
                    'idx_dex_trades_tx_hash',
                    'dex_trades',
                    ['transaction_hash'],
                    unique=True
                )

    # ==========================================
    # Risk Alerts Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("risk_alerts", ["user_id", "severity", "acknowledged", "created_at"]):
        if not has_index("risk_alerts", "idx_risk_alerts_user_severity_ack"):
            if is_postgresql:
                op.execute(sa.text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_risk_alerts_user_severity_ack 
                    ON risk_alerts(user_id, severity, acknowledged, created_at DESC)
                """))
            else:
                op.create_index(
                    'idx_risk_alerts_user_severity_ack',
                    'risk_alerts',
                    ['user_id', 'severity', 'acknowledged', sa.text('created_at DESC')],
                    unique=False
                )

    # ==========================================
    # Audit Logs Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("audit_logs", ["user_id", "action", "created_at"]):
        if not has_index("audit_logs", "idx_audit_logs_user_action_created"):
            if is_postgresql:
                op.execute(sa.text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_action_created 
                    ON audit_logs(user_id, action, created_at DESC)
                """))
            else:
                op.create_index(
                    'idx_audit_logs_user_action_created',
                    'audit_logs',
                    ['user_id', 'action', sa.text('created_at DESC')],
                    unique=False
                )

    # ==========================================
    # API Key Usage Indexes (2026 Best Practices)
    # ==========================================
    if has_columns("api_key_usage", ["api_key_id", "created_at"]):
        if not has_index("api_key_usage", "idx_api_key_usage_key_created"):
            if is_postgresql:
                op.execute(sa.text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_key_usage_key_created 
                    ON api_key_usage(api_key_id, created_at DESC)
                """))
            else:
                op.create_index(
                    'idx_api_key_usage_key_created',
                    'api_key_usage',
                    ['api_key_id', sa.text('created_at DESC')],
                    unique=False
                )

    import logging
    logger = logging.getLogger(__name__)
    logger.info("Comprehensive indexes for 2026 best practices created successfully")


def downgrade() -> None:
    """Remove comprehensive indexes"""
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'

    indexes_to_drop = [
        'idx_orders_user_status_created',
        'idx_orders_user_mode_created',
        'idx_orders_symbol_status_created',
        'idx_orders_bot_status',
        'idx_trades_user_mode_symbol_created',
        'idx_trades_symbol_side_executed',
        'idx_trades_status_created',
        'idx_wallets_user_currency_active',
        'idx_wallets_user_type_active',
        'idx_wallet_txns_user_type_status_created',
        'idx_wallet_txns_wallet_status_created',
        'idx_bots_user_active_status_created',
        'idx_bots_symbol_active',
        'idx_portfolios_user_mode_created',
        'idx_dex_positions_user_chain_open',
        'idx_dex_trades_user_chain_status_created',
        'idx_dex_trades_tx_hash',
        'idx_risk_alerts_user_severity_ack',
        'idx_audit_logs_user_action_created',
        'idx_api_key_usage_key_created',
    ]

    for index_name in indexes_to_drop:
        try:
            if is_postgresql:
                op.execute(sa.text(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}"))
            else:
                op.drop_index(index_name)
        except Exception as e:
            logger.warning(f"Could not drop index {index_name}: {e}")
