"""add_hot_path_indexes

Add composite indexes for hot path queries as specified in optimization plan:
- idx_trades_user_timestamp: For user trade queries ordered by timestamp
- idx_trades_bot_timestamp: For bot trade queries ordered by timestamp  
- idx_wallets_user_chain: For wallet queries by user and chain
- idx_bots_user_status: For bot queries by user and status

Revision ID: 20251208_hot_path_indexes
Revises: optimize_query_indexes_001
Create Date: 2025-12-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251208_hot_path_indexes'
down_revision = 'optimize_query_indexes_001'
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

    # Index for trades: user_id + created_at DESC (hot path for user trade history)
    if (
        has_columns("trades", ["user_id", "created_at"])
        and not has_index("trades", "idx_trades_user_timestamp")
    ):
        op.create_index(
            'idx_trades_user_timestamp',
            'trades',
            ['user_id', sa.text('created_at DESC')],
            unique=False,
            postgresql_concurrently=True  # Non-blocking index creation for PostgreSQL
        )
    
    # Index for trades: bot_id + created_at DESC (hot path for bot trade history)
    # Only create if bot_id is not null (partial index)
    if (
        has_columns("trades", ["bot_id", "created_at"])
        and not has_index("trades", "idx_trades_bot_timestamp")
    ):
        # Use CONCURRENTLY for PostgreSQL to avoid locking
        if bind.dialect.name == 'postgresql':
            op.execute(
                sa.text("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trades_bot_timestamp 
                    ON trades(bot_id, created_at DESC) 
                    WHERE bot_id IS NOT NULL
                """)
            )
        else:
            # SQLite doesn't support CONCURRENTLY or partial indexes the same way
            op.create_index(
                'idx_trades_bot_timestamp',
                'trades',
                ['bot_id', sa.text('created_at DESC')],
                unique=False
            )
    
    # Index for wallets: user_id + chain_id + is_active (hot path for wallet queries)
    if (
        has_columns("wallets", ["user_id", "chain_id", "is_active"])
        and not has_index("wallets", "idx_wallets_user_chain")
    ):
        op.create_index(
            'idx_wallets_user_chain',
            'wallets',
            ['user_id', 'chain_id', 'is_active'],
            unique=False,
            postgresql_concurrently=True
        )
    
    # Index for bots: user_id + status + created_at DESC (hot path for bot queries)
    if (
        has_columns("bots", ["user_id", "status", "created_at"])
        and not has_index("bots", "idx_bots_user_status")
    ):
        op.create_index(
            'idx_bots_user_status',
            'bots',
            ['user_id', 'status', sa.text('created_at DESC')],
            unique=False,
            postgresql_concurrently=True
        )


def downgrade() -> None:
    # Drop indexes in reverse order
    try:
        op.drop_index('idx_bots_user_status', table_name='bots')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_wallets_user_chain', table_name='wallets')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_trades_bot_timestamp', table_name='trades')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_trades_user_timestamp', table_name='trades')
    except Exception:
        pass



