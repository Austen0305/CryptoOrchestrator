"""merge_all_heads

Revision ID: 01e0725f1aca
Revises: 20251208_remove_exchange, add_db_views_001, add_dex_positions_2025
Create Date: 2025-12-15 20:53:09.821302

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '01e0725f1aca'
down_revision = ('20251208_remove_exchange', 'add_db_views_001', 'add_dex_positions_2025')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

