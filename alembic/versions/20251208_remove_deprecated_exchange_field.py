"""remove_deprecated_exchange_field

Remove deprecated 'exchange' field from bot models (replaced by chain_id).
This migration drops the exchange column from tables that still have it.

Revision ID: 20251208_remove_exchange
Revises: 20251208_timescaledb
Create Date: 2025-12-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import logging

logger = logging.getLogger(__name__)

# revision identifiers, used by Alembic.
revision = '20251208_remove_exchange'
down_revision = '20251208_timescaledb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_column(table: str, col: str) -> bool:
        existing = {c["name"] for c in inspector.get_columns(table)}
        return col in existing

    # Remove exchange column from bot tables (replaced by chain_id)
    tables_to_update = [
        "dca_bots",
        "grid_bots",
        "trailing_bots",
        "infinity_grids",
        "futures_positions"
    ]
    
    for table_name in tables_to_update:
        try:
            if has_column(table_name, "exchange"):
                # Drop the exchange column
                op.drop_column(table_name, "exchange")
                logger.info(f"Dropped 'exchange' column from {table_name}")
            else:
                logger.info(f"Table {table_name} does not have 'exchange' column (already removed)")
        except Exception as e:
            logger.warning(f"Could not drop 'exchange' column from {table_name}: {e}")
            # Continue with other tables


def downgrade() -> None:
    # Add exchange column back (for rollback purposes)
    # Note: This is a simplified rollback - you may need to populate exchange values from chain_id
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    def has_column(table: str, col: str) -> bool:
        existing = {c["name"] for c in inspector.get_columns(table)}
        return col in existing
    
    tables_to_update = [
        "dca_bots",
        "grid_bots",
        "trailing_bots",
        "infinity_grids",
        "futures_positions"
    ]
    
    for table_name in tables_to_update:
        try:
            if not has_column(table_name, "exchange"):
                # Add exchange column back (nullable, as we don't have historical data)
                op.add_column(
                    table_name,
                    sa.Column("exchange", sa.String(50), nullable=True)
                )
                logger.info(f"Added 'exchange' column back to {table_name}")
        except Exception as e:
            logger.warning(f"Could not add 'exchange' column to {table_name}: {e}")
