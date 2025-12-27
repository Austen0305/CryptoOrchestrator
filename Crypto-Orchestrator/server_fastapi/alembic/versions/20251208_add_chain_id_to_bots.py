"""add chain_id to bots, deprecate exchange field

Revision ID: 20251208_add_chain_id
Revises:
Create Date: 2025-12-08

This migration adds chain_id fields to bot models and migrates data from exchange field.
The exchange field is kept for backward compatibility but is deprecated.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251208_add_chain_id"
down_revision = None  # Update this with the latest migration revision
branch_labels = None
depends_on = None


def upgrade():
    """
    Add chain_id columns to bot tables and migrate data from exchange field.
    """
    # Add chain_id to grid_bots
    op.add_column("grid_bots", sa.Column("chain_id", sa.Integer(), nullable=True))
    # Migrate data: if exchange is numeric, use it as chain_id
    # SQLite-compatible: use CAST and check if exchange is numeric
    op.execute(
        """
        UPDATE grid_bots
        SET chain_id = CAST(exchange AS INTEGER)
        WHERE CAST(exchange AS INTEGER) IS NOT NULL
        AND chain_id IS NULL
        AND exchange GLOB '[0-9]*'
    """
    )
    # Default to Ethereum (1) if exchange is not numeric or chain_id is still NULL
    op.execute(
        """
        UPDATE grid_bots
        SET chain_id = 1
        WHERE chain_id IS NULL
    """
    )
    # Make chain_id NOT NULL after migration
    op.alter_column("grid_bots", "chain_id", nullable=False)

    # Add chain_id to trailing_bots
    op.add_column("trailing_bots", sa.Column("chain_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE trailing_bots
        SET chain_id = CAST(exchange AS INTEGER)
        WHERE CAST(exchange AS INTEGER) IS NOT NULL
        AND chain_id IS NULL
        AND exchange GLOB '[0-9]*'
    """
    )
    op.execute(
        """
        UPDATE trailing_bots
        SET chain_id = 1
        WHERE chain_id IS NULL
    """
    )
    op.alter_column("trailing_bots", "chain_id", nullable=False)

    # Add chain_id to infinity_grids
    op.add_column("infinity_grids", sa.Column("chain_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE infinity_grids
        SET chain_id = CAST(exchange AS INTEGER)
        WHERE CAST(exchange AS INTEGER) IS NOT NULL
        AND chain_id IS NULL
        AND exchange GLOB '[0-9]*'
    """
    )
    op.execute(
        """
        UPDATE infinity_grids
        SET chain_id = 1
        WHERE chain_id IS NULL
    """
    )
    op.alter_column("infinity_grids", "chain_id", nullable=False)

    # Add chain_id to dca_bots
    op.add_column("dca_bots", sa.Column("chain_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE dca_bots
        SET chain_id = CAST(exchange AS INTEGER)
        WHERE CAST(exchange AS INTEGER) IS NOT NULL
        AND chain_id IS NULL
        AND exchange GLOB '[0-9]*'
    """
    )
    op.execute(
        """
        UPDATE dca_bots
        SET chain_id = 1
        WHERE chain_id IS NULL
    """
    )
    op.alter_column("dca_bots", "chain_id", nullable=False)

    # Add chain_id to futures_positions
    op.add_column(
        "futures_positions", sa.Column("chain_id", sa.Integer(), nullable=True)
    )
    op.execute(
        """
        UPDATE futures_positions
        SET chain_id = CAST(exchange AS INTEGER)
        WHERE CAST(exchange AS INTEGER) IS NOT NULL
        AND chain_id IS NULL
        AND exchange GLOB '[0-9]*'
    """
    )
    op.execute(
        """
        UPDATE futures_positions
        SET chain_id = 1
        WHERE chain_id IS NULL
    """
    )
    op.alter_column("futures_positions", "chain_id", nullable=False)

    # Create indexes on chain_id for better query performance
    op.create_index("ix_grid_bots_chain_id", "grid_bots", ["chain_id"])
    op.create_index("ix_trailing_bots_chain_id", "trailing_bots", ["chain_id"])
    op.create_index("ix_infinity_grids_chain_id", "infinity_grids", ["chain_id"])
    op.create_index("ix_dca_bots_chain_id", "dca_bots", ["chain_id"])
    op.create_index("ix_futures_positions_chain_id", "futures_positions", ["chain_id"])


def downgrade():
    """
    Remove chain_id columns (exchange field remains for backward compatibility).
    """
    # Drop indexes
    op.drop_index("ix_futures_positions_chain_id", "futures_positions")
    op.drop_index("ix_dca_bots_chain_id", "dca_bots")
    op.drop_index("ix_infinity_grids_chain_id", "infinity_grids")
    op.drop_index("ix_trailing_bots_chain_id", "trailing_bots")
    op.drop_index("ix_grid_bots_chain_id", "grid_bots")

    # Drop chain_id columns
    op.drop_column("futures_positions", "chain_id")
    op.drop_column("dca_bots", "chain_id")
    op.drop_column("infinity_grids", "chain_id")
    op.drop_column("trailing_bots", "chain_id")
    op.drop_column("grid_bots", "chain_id")
