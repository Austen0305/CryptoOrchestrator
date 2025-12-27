"""optimize_query_indexes

Revision ID: optimize_query_indexes_001
Revises: 7db86ff346ef
Create Date: 2025-12-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'optimize_query_indexes_001'
down_revision = '7db86ff346ef'
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

    # Composite index for bots: user_id + active + created_at (common query pattern)
    if (
        has_columns("bots", ["user_id", "active", "created_at"])
        and not has_index("bots", "ix_bots_user_active_created")
    ):
        op.create_index(
            'ix_bots_user_active_created',
            'bots',
            ['user_id', 'active', sa.text('created_at DESC')],
            unique=False
        )
    
    # Composite index for bots: user_id + status + created_at
    if (
        has_columns("bots", ["user_id", "status", "created_at"])
        and not has_index("bots", "ix_bots_user_status_created")
    ):
        op.create_index(
            'ix_bots_user_status_created',
            'bots',
            ['user_id', 'status', sa.text('created_at DESC')],
            unique=False
        )
    
    # Index for portfolio queries: user_id + mode
    if (
        has_columns("portfolios", ["user_id", "mode"])
        and not has_index("portfolios", "ix_portfolios_user_mode")
    ):
        op.create_index(
            'ix_portfolios_user_mode',
            'portfolios',
            ['user_id', 'mode'],
            unique=False
        )
    
    # Index for orders: user_id + mode + created_at
    if (
        has_columns("orders", ["user_id", "mode", "created_at"])
        and not has_index("orders", "ix_orders_user_mode_created")
    ):
        op.create_index(
            'ix_orders_user_mode_created',
            'orders',
            ['user_id', 'mode', sa.text('created_at DESC')],
            unique=False
        )


def downgrade() -> None:
    # Drop indexes in reverse order
    try:
        op.drop_index('ix_orders_user_mode_created', table_name='orders')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_portfolios_user_mode', table_name='portfolios')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_bots_user_status_created', table_name='bots')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_bots_user_active_created', table_name='bots')
    except Exception:
        pass
